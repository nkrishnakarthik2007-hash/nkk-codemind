"""CPU-first model candidates and repeatable Ollama benchmark."""
from __future__ import annotations
import json
import platform
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class ModelCandidate:
    tag: str
    size_class: str
    roles: str
    license_note: str
    source: str

CANDIDATES = (
    ModelCandidate("qwen3.5:0.8b", "tiny", "classification, extraction", "Verify exact model-card terms", "https://ollama.com/library/qwen3.5"),
    ModelCandidate("qwen3.5:2b", "small", "general assistant, summarization", "Verify exact model-card terms", "https://ollama.com/library/qwen3.5"),
    ModelCandidate("qwen3.5:4b", "medium", "general reasoning, multilingual baseline", "Apache-2.0 model card", "https://huggingface.co/Qwen/Qwen3.5-4B"),
    ModelCandidate("qwen2.5-coder:3b", "medium", "code generation and repair", "Verify exact model-card terms", "https://ollama.com/library/qwen2.5-coder"),
    ModelCandidate("phi4-mini", "medium", "compact reasoning and structured output", "Verify exact model-card terms", "https://ollama.com/library/phi4-mini"),
    ModelCandidate("gemma4:e2b", "small", "compact instruction and multimodal experiment", "Gemma terms; not Apache/MIT", "https://ollama.com/library/gemma4"),
)
TASKS = (
    ("explain", "Explain in plain English what this function does.\ndef add_tax(price, rate):\n    return round(price * (1 + rate), 2)"),
    ("coding", "Write a Python function is_even(n) and exactly three pytest tests. Return code only."),
    ("debugging", "Fix this function so empty input returns 0.\ndef average(values):\n    return sum(values) / len(values)"),
    ("json", 'Return only valid JSON with keys "language" and "paradigm" for Python. No Markdown.'),
)

def benchmark_models(provider: Any, models: list[str], *, num_ctx: int = 1024, num_predict: int = 160) -> dict:
    rows = []
    for model in models:
        for task, prompt in TASKS:
            started = time.perf_counter()
            try:
                result = provider.generate(model, prompt, system="You are a concise software engineering assistant. Follow output formats exactly.", num_ctx=num_ctx, num_predict=num_predict, keep_alive=0)
                elapsed = time.perf_counter() - started
                duration = result.total_duration_ns / 1e9 if result.total_duration_ns else elapsed
                count = result.generated_tokens or 0
                rows.append({"model": model, "task": task, "output": result.text, "prompt_tokens": result.prompt_tokens, "generated_tokens": count, "duration_seconds": round(duration, 4), "tokens_per_second": round(count / duration, 3) if duration > 0 else 0.0, "error": None})
            except Exception as exc:
                rows.append({"model": model, "task": task, "output": "", "prompt_tokens": None, "generated_tokens": None, "duration_seconds": round(time.perf_counter() - started, 4), "tokens_per_second": 0.0, "error": "{}: {}".format(type(exc).__name__, exc)})
    return {"schema_version": 1, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "hardware": {"platform": platform.platform(), "processor": platform.processor()}, "settings": {"num_ctx": num_ctx, "num_predict": num_predict, "mode": "sequential-unloaded"}, "results": rows, "note": "Speed is measured locally. Correctness requires human review and executable tests."}

def save_benchmark_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
