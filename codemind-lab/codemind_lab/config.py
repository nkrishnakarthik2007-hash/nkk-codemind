"""Small, explicit configuration and conservative host-memory checks."""

from __future__ import annotations

import ctypes
import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelSpec:
    name: str
    backend: str
    model: str
    base_url: str
    api_key_env: str | None = None
    estimated_ram_gb: float | None = None
    context_tokens: int = 2048
    max_output_tokens: int = 512
    unload_after_call: bool = True


@dataclass(frozen=True)
class LabConfig:
    models: tuple[ModelSpec, ...]
    reserve_ram_gb: float = 1.5
    max_parallel_calls: int = 1
    max_ensemble_members: int = 2
    request_timeout_seconds: int = 180


def available_memory_bytes() -> int | None:
    """Return OS-reported available physical memory without requiring psutil."""
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullAvailPhys)
        return None

    try:
        pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return int(pages * page_size)
    except (AttributeError, OSError, ValueError):
        return None


def check_memory_budget(spec: ModelSpec, reserve_ram_gb: float) -> None:
    """Refuse a configured model estimate that would consume the safety reserve.

    estimated_ram_gb is intentionally user-supplied: model file size alone is not
    a reliable estimate of runtime RAM because KV cache and runtime overhead vary.
    """
    if spec.estimated_ram_gb is None:
        return
    if spec.estimated_ram_gb <= 0:
        raise ValueError(f"{spec.name}: estimated_ram_gb must be positive")
    free_bytes = available_memory_bytes()
    if free_bytes is None:
        return
    required = (spec.estimated_ram_gb + reserve_ram_gb) * (1024 ** 3)
    if free_bytes < required:
        free_gb = free_bytes / (1024 ** 3)
        raise MemoryError(
            f"Not enough currently available RAM for {spec.name}: "
            f"estimated model budget {spec.estimated_ram_gb:.2f} GB + "
            f"{reserve_ram_gb:.2f} GB reserve, but only {free_gb:.2f} GB is available. "
            "Close other apps, lower context, or choose a smaller model."
        )


def load_config(path: str | Path) -> LabConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    policy = raw.get("policy", {})
    models = []
    for item in raw.get("models", []):
        models.append(ModelSpec(
            name=str(item["name"]),
            backend=str(item.get("backend", "openai")),
            model=str(item["model"]),
            base_url=str(item["base_url"]).rstrip("/"),
            api_key_env=item.get("api_key_env"),
            estimated_ram_gb=(
                float(item["estimated_ram_gb"])
                if item.get("estimated_ram_gb") is not None else None
            ),
            context_tokens=int(item.get("context_tokens", 2048)),
            max_output_tokens=int(item.get("max_output_tokens", 512)),
            unload_after_call=bool(item.get("unload_after_call", True)),
        ))
    if not models:
        raise ValueError("Configuration must contain at least one model.")
    if len({m.name for m in models}) != len(models):
        raise ValueError("Model names must be unique.")
    max_parallel = int(policy.get("max_parallel_calls", 1))
    if max_parallel != 1:
        raise ValueError("CPU-first mode currently enforces max_parallel_calls=1.")
    max_members = int(policy.get("max_ensemble_members", 2))
    if not 1 <= max_members <= 4:
        raise ValueError("max_ensemble_members must be between 1 and 4.")
    return LabConfig(
        models=tuple(models),
        reserve_ram_gb=float(policy.get("reserve_ram_gb", 1.5)),
        max_parallel_calls=1,
        max_ensemble_members=max_members,
        request_timeout_seconds=int(policy.get("request_timeout_seconds", 180)),
    )
