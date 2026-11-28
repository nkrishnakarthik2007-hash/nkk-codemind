"""Command-line interface for the first CodeMind CPU lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import build_backends
from .config import load_config
from .engine import ask, benchmark, combine, develop_pipeline


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="codemind-lab", description="NKK CodeMind CPU-first model lab")
    p.add_argument("--config", type=Path, default=Path("models.json"))
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("models", help="List configured model endpoints")

    one = sub.add_parser("ask", help="Send a prompt to one configured model")
    one.add_argument("--model", required=True)
    one.add_argument("--task-type", default="generic")
    one.add_argument("prompt")

    many = sub.add_parser("combine", help="Combine small models sequentially using GAMA")
    many.add_argument("--models", required=True, help="Comma-separated configured model names")
    many.add_argument("prompt")

    team = sub.add_parser("develop", help="Run planner → coder → reviewer sequentially")
    team.add_argument("--planner", required=True)
    team.add_argument("--coder", required=True)
    team.add_argument("--reviewer")
    team.add_argument("prompt")

    bench = sub.add_parser("bench", help="Run GAMA deterministic benchmark suite")
    bench.add_argument("--models", required=True, help="Comma-separated configured model names")
    bench.add_argument("--suite", default="qadeep", choices=["qadeep"])
    bench.add_argument("--repeats", type=int, default=1)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "models":
            for item in config.models:
                print(
                    f"{item.name}: {item.backend} | {item.model} | {item.base_url} | "
                    f"context={item.context_tokens} | estimated RAM="
                    f"{item.estimated_ram_gb if item.estimated_ram_gb is not None else 'not set'} GB"
                )
            print(
                f"CPU policy: one active call, max {config.max_ensemble_members} ensemble members, "
                f"{config.reserve_ram_gb:.1f} GB RAM reserve."
            )
            return 0
        if args.command == "ask":
            print(ask(config, args.model, args.prompt, args.task_type))
            return 0
        if args.command == "combine":
            names = [x.strip() for x in args.models.split(",") if x.strip()]
            print(combine(config, names, args.prompt))
            return 0
        if args.command == "develop":
            result = develop_pipeline(
                config, args.prompt, args.planner, args.coder, args.reviewer
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "bench":
            names = [x.strip() for x in args.models.split(",") if x.strip()]
            result = benchmark(config, names, args.suite, args.repeats)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        return 2
    except (OSError, ValueError, RuntimeError, MemoryError) as exc:
        print(f"CodeMind Lab error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
