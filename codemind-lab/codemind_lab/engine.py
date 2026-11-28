"""Composition strategies built on GAMA's tested backend abstractions."""

from __future__ import annotations

from gama.abmcts import ABMCTSBackend
from gama.backends import EnsembleBackend, GamaBackend
from gama.benchmark import SUITES, run_bench, summarize
from gama.meshflow import MeshflowBackend
from gama.models import ModelTier

from .backends import build_backends, build_router, build_sequential_ensemble
from .config import LabConfig


def ask(config: LabConfig, model_name: str, prompt: str, task_type: str = "generic") -> str:
    backends, _ = build_backends(config)
    if model_name not in backends:
        raise ValueError(f"Unknown model {model_name!r}.")
    return backends[model_name].complete(prompt, ModelTier.SMALL, task_type=task_type)


def combine(
    config: LabConfig, model_names: list[str], prompt: str, task_type: str = "generic"
) -> str:
    backend = build_sequential_ensemble(config, model_names)
    return backend.complete(prompt, ModelTier.SMALL, task_type=task_type)


def develop_pipeline(
    config: LabConfig,
    prompt: str,
    planner: str,
    coder: str,
    reviewer: str | None = None,
) -> dict[str, str]:
    """Run plan → code → review sequentially; never fan out model calls."""
    backends, _ = build_backends(config)
    for name in (planner, coder, reviewer):
        if name is not None and name not in backends:
            raise ValueError(f"Unknown model {name!r}.")

    plan = backends[planner].complete(
        "Create a short implementation plan. Do not write code yet.\n\nTask:\n" + prompt,
        ModelTier.SMALL,
        task_type="architecture",
    )
    code = backends[coder].complete(
        "Implement the task using this plan. Return the proposed code and file-level changes.\n"
        f"Task:\n{prompt}\n\nPlan:\n{plan}",
        ModelTier.SMALL,
        task_type="code_implementation",
    )
    result = {"plan": plan, "implementation": code}
    if reviewer:
        result["review"] = backends[reviewer].complete(
            "Review this proposed implementation. Identify concrete bugs, missing cases and "
            "security problems. Do not claim tests were run.\n"
            f"Task:\n{prompt}\n\nPlan:\n{plan}\n\nImplementation:\n{code}",
            ModelTier.SMALL,
            task_type="code_review",
        )
    return result


def build_verified_escalation(config: LabConfig, model_names: list[str]):
    """Build GAMA's cheap-to-strong verification escalation over serial CPU adapters."""
    backends, _ = build_backends(config)
    if not 1 <= len(model_names) <= config.max_ensemble_members:
        raise ValueError(
            f"Choose between 1 and {config.max_ensemble_members} escalation tiers."
        )
    missing = [name for name in model_names if name not in backends]
    if missing:
        raise ValueError(f"Unknown model names: {', '.join(missing)}")
    tiers = [(name, backends[name]) for name in model_names]
    return MeshflowBackend(
        tiers,
        verify=None,  # GAMA benchmark supplies its deterministic case checker per call.
        mesh="synthesize",
        aggregator=backends[model_names[-1]],
        pass_score=1.0,
    )


def build_adaptive_search(config: LabConfig, model_names: list[str], budget: int = 3):
    """Build GAMA AB-MCTS with a small, bounded model-call budget."""
    backends, _ = build_backends(config)
    if not 1 <= len(model_names) <= config.max_ensemble_members:
        raise ValueError(
            f"Choose between 1 and {config.max_ensemble_members} search workers."
        )
    missing = [name for name in model_names if name not in backends]
    if missing:
        raise ValueError(f"Unknown model names: {', '.join(missing)}")
    workers = [(name, backends[name]) for name in model_names]
    return ABMCTSBackend(
        workers,
        verify=None,  # GAMA benchmark supplies its deterministic case checker per call.
        budget=max(1, min(int(budget), 4)),
        pass_score=1.0,
        seed=7,
    )


def benchmark(
    config: LabConfig,
    model_names: list[str],
    suite_name: str = "qadeep",
    repeats: int = 1,
    strategy: str = "single",
) -> dict:
    """Run GAMA deterministic graders; qadeep never executes generated code."""
    if suite_name not in SUITES:
        raise ValueError(
            f"Unknown GAMA suite {suite_name!r}. Available: {', '.join(sorted(SUITES))}"
        )
    if suite_name != "qadeep":
        raise ValueError(
            "Only qadeep is enabled in the initial CPU lab. Other GAMA suites may execute "
            "model-generated code; add a separately reviewed OS sandbox before enabling them."
        )
    backends, _ = build_backends(config)
    missing = [name for name in model_names if name not in backends]
    if missing:
        raise ValueError(f"Unknown model names: {', '.join(missing)}")
    if not model_names:
        raise ValueError("Select at least one model for benchmarking.")
    if strategy == "single":
        chosen = {name: backends[name] for name in model_names}
    elif strategy == "ensemble":
        chosen = {"codemind-ensemble": build_sequential_ensemble(config, model_names)}
    elif strategy == "meshflow":
        chosen = {"codemind-meshflow": build_verified_escalation(config, model_names)}
    elif strategy == "abmcts":
        chosen = {"codemind-abmcts": build_adaptive_search(config, model_names)}
    else:
        raise ValueError("strategy must be single, ensemble, meshflow or abmcts")
    records = run_bench(
        chosen,
        suite=SUITES[suite_name],
        tier=ModelTier.SMALL,
        repeats=max(1, min(int(repeats), 3)),
        run_id="codemind-cpu-lab",
    )
    return {"summary": summarize(records), "records": records}


__all__ = [
    "ABMCTSBackend", "EnsembleBackend", "GamaBackend", "MeshflowBackend",
    "ask", "benchmark", "build_adaptive_search", "build_router",
    "build_sequential_ensemble", "build_verified_escalation",
    "combine", "develop_pipeline",
]
