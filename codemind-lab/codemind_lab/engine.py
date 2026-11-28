"""Composition strategies built on GAMA's tested backend abstractions."""

from __future__ import annotations

from time import perf_counter

from gama.abmcts import ABMCTSBackend
from gama.backends import EnsembleBackend, GamaBackend
from gama.benchmark import SUITES, run_bench, summarize
from gama.meshflow import MeshflowBackend
from gama.models import ModelTier

from .backends import build_backends, build_router, build_sequential_ensemble
from .config import LabConfig, available_memory_bytes


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



def profile_models(
    config: LabConfig,
    model_names: list[str],
    prompt: str = "Return exactly: CODEMIND_PROFILE_OK",
    repeats: int = 2,
) -> dict:
    """Measure real endpoint latency, token throughput and free-RAM snapshots."""
    if not prompt.strip():
        raise ValueError("Profile prompt cannot be empty.")
    if not model_names:
        raise ValueError("Select at least one model to profile.")
    backends, _ = build_backends(config)
    missing = [name for name in model_names if name not in backends]
    if missing:
        raise ValueError(f"Unknown model names: {', '.join(missing)}")

    results = {}
    for name in model_names:
        backend = backends[name]
        samples = []
        for index in range(max(1, min(int(repeats), 5))):
            free_before = available_memory_bytes()
            started = perf_counter()
            answer = backend.complete(prompt, ModelTier.SMALL)
            elapsed = __import__("time").perf_counter() - started
            free_after = available_memory_bytes()
            usage = getattr(backend, "last_usage", None) or {}
            completion_tokens = usage.get("completion_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", 0)
            if not isinstance(completion_tokens, (int, float)):
                completion_tokens = 0
            if not isinstance(prompt_tokens, (int, float)):
                prompt_tokens = 0
            samples.append({
                "run": index + 1,
                "seconds": round(elapsed, 3),
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "output_tokens_per_second": (
                    round(completion_tokens / elapsed, 2) if elapsed > 0 and completion_tokens else None
                ),
                "free_ram_before_gb": (
                    round(free_before / (1024 ** 3), 3) if free_before is not None else None
                ),
                "free_ram_after_gb": (
                    round(free_after / (1024 ** 3), 3) if free_after is not None else None
                ),
                "answer_preview": answer[:240],
            })
        durations = [item["seconds"] for item in samples]
        results[name] = {
            "backend": getattr(backend, "name", type(backend).__name__),
            "runs": samples,
            "average_seconds": round(sum(durations) / len(durations), 3),
            "fastest_seconds": min(durations),
            "slowest_seconds": max(durations),
            "memory_note": (
                "RAM values are system-wide free-memory snapshots, not peak process RAM "
                "or isolated model memory."
            ),
        }
    return {"prompt": prompt, "results": results}

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
    "ask", "benchmark", "profile_models", "build_adaptive_search", "build_router",
    "build_sequential_ensemble", "build_verified_escalation",
    "combine", "develop_pipeline",
]
