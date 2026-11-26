# NKK CodeMind

**A lightweight, knowledge-driven AI software development engine for ordinary Windows PCs.**

NKK CodeMind is a local-first coding agent designed around one principle:

> Keep reusable knowledge on disk, retrieve only what a task needs, and use the smallest capable AI engine for the job.

It aims to make useful AI-assisted software development available on CPU-only computers, with an initial engineering target of **8 GB RAM**.

## What makes it different?

- **On-demand knowledge:** acquire documentation from official sources or user-provided files when a task needs it.
- **Disk-first storage:** keep knowledge in a local library; do not keep entire documentation sets in RAM.
- **Small-model-first routing:** use compact local models for suitable tasks and optional cloud models for harder work.
- **No unnecessary interrogation:** infer sensible defaults, ask only when a decision blocks safe or correct progress.
- **Real development tools:** inspect files, edit code, run tests and report what was actually verified.
- **Replaceable providers:** model providers and runtimes are adapters, not hard-coded dependencies.
- **Windows-first:** package as a native-feeling Windows desktop application after the core engine is proven.

## Status

Early research and prototype stage. This repository does **not** yet claim to be a complete autonomous coding agent.

See:
- [VISION.md](VISION.md) — product principles and boundaries
- [ARCHITECTURE.md](ARCHITECTURE.md) — proposed technical design
- [ROADMAP.md](ROADMAP.md) — staged implementation plan
- [MODEL_RESEARCH.md](MODEL_RESEARCH.md) — model and runtime evaluation plan
- [SECURITY.md](SECURITY.md) — safety and privacy principles

## Prototype: knowledge library

The first prototype is deliberately small and does not require an AI model. It demonstrates the key idea: add documents or URLs to a persistent library, search them on demand, and retrieve only relevant excerpts.

### Requirements

- Python 3.10+
- Optional internet access for URL ingestion

### Run on Windows

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m codemind --help
```

Add a local document:

```powershell
python -m codemind add-file .\docs\python-guide.md --tags python,docs
```

Add a web page:

```powershell
python -m codemind add-url https://docs.python.org/3/tutorial/ --tags python,official
```

Search the knowledge library:

```powershell
python -m codemind search "read a JSON file in Python"
```

The prototype stores data under the user profile by default, not inside the project directory. Set `CODEMIND_HOME` to change that location.

## Design constraints

1. No model is required just to manage/search documentation.
2. No large vector database or embedding model is required for the first version.
3. Local model loading must be lazy and unloadable.
4. Cloud providers must be optional, explicitly configured and subject to their own quotas and privacy terms.
5. Never merge arbitrary models and assume the result is better. Model merging requires compatible architectures/tokenizers and evaluation.
6. All code execution must be permission-controlled.

## License

The project is not yet licensed. A license will be selected before distributing code or binaries.