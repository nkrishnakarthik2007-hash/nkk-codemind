"""Composition strategies built on GAMA's tested backend abstractions."""

from __future__ import annotations

from gama.abmcts import ABMCTSBackend
from gama.backends import EnsembleBackend, GamaBackend
from gama.benchmark import SUITES, run_bench, summarize
from gama.config import build_backend
from gama.meshflow import MeshflowBackend
from gama.models import ModelTier

from .backends import build_backends, build_router, build_sequential_ensemble
from .config import LabConfig


def ask(config: LabConfig, model_name: str, prompt: str, task_type: str = "generic") -> str:
    backends, _ = build_backends(config)
    if model_name not in backends:
        raise ValueError(f"Unknown model {model_name!r}.")
    return backends[model_name].complete(
        prompt, ModelTier.SMALL, task_type=task_type
    )


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
        review = backends[reviewer].complete(
            "Review this proposed implementation. Identify concrete bugs, missing cases and "
            "security problems. Do not claim tests were run.\n"
            f"Task:\n{prompt}\n\nPlan:\n{plan}\n\nImplementation:\n{code}",
            ModelTier.SMALL,
            task_type="code_review",
        )
        result["review"] = review
    return result


def benchmark(
    config: LabConfig,
    model_names: list[str],
    suite_name: str = "qadeep",
    repeats: int = 1,
) -> dict:
    """Run GAMA's deterministic graders. qadeep is the safe default (no generated-code execution)."""
    if suite_name not in SUITES:
        raise ValueError(f"Unknown GAMA suite {suite_name!r}. Available: {', '.join(sorted(SUITES))}")
    if suite_name != "qadeep":
        raise ValueError(
            "Only qadeep is enabled in the initial CPU lab. Other GAMA suites may execute "
            "model-generated code; add a separately reviewed OS sandbox before enabling them."
        )
    backends, _ = build_backends(config)
    chosen = {name: backends[name] for name in model_names}
    records = run_bench(
        chosen,
        suite=SUITES[suite_name],
        tier=ModelTier.SMALL,
        repeats=max(1, min(int(repeats), 3)),
        run_id="codemind-cpu-lab",
    )
    return {"summary": summarize(records), "records": records}


__all__ = [
    "ABMCTSBackend",
    "EnsembleBackend",
    "GamaBackend",
    "MeshflowBackend",
    "ask",
    "benchmark",
    "build_router",
    "build_sequential_ensemble",
    "combine",
    "develop_pipeline",
]
