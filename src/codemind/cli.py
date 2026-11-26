"""Command-line interface for the first CodeMind prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .knowledge.ingest import add_url
from .knowledge.library import KnowledgeLibrary


def _tags(value: str) -> tuple[str, ...]:
    return tuple(tag.strip() for tag in value.split(",") if tag.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codemind",
        description="NKK CodeMind — on-demand local knowledge library",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_file = sub.add_parser("add-file", help="Add a UTF-8 text/Markdown file")
    add_file.add_argument("path", type=Path)
    add_file.add_argument("--tags", default="")

    add_web = sub.add_parser("add-url", help="Fetch and store a public HTTPS page")
    add_web.add_argument("url")
    add_web.add_argument("--tags", default="")

    search = sub.add_parser("search", help="Search saved knowledge")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)

    sub.add_parser("list", help="List saved knowledge items")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    library = KnowledgeLibrary()

    try:
        if args.command == "add-file":
            item = library.add_file(args.path, tags=_tags(args.tags))
            print(f"Saved: {item.title}\nID: {item.item_id}\nSource: {item.source}")
        elif args.command == "add-url":
            item = add_url(library, args.url, tags=_tags(args.tags))
            print(f"Saved: {item.title}\nID: {item.item_id}\nSource: {item.source}")
        elif args.command == "search":
            results = library.search(args.query, limit=args.limit)
            if not results:
                print("No matching knowledge found.")
                return 0
            for number, result in enumerate(results, start=1):
                print(f"\n[{number}] {result.item.title} ({result.item.source_type})")
                print(f"Source: {result.item.source}")
                if result.item.tags:
                    print(f"Tags: {', '.join(result.item.tags)}")
                print(result.excerpt)
        elif args.command == "list":
            items = library.list_items()
            if not items:
                print("Knowledge library is empty.")
            for item in items:
                print(f"{item.title} | {item.source_type} | {item.item_id}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())