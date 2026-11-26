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

Early prototype. The current CLI can store/search knowledge and query an installed local Ollama model with a few relevant knowledge excerpts. It is **not yet** a full autonomous coding agent or Windows desktop application.

See:
- [VISION.md](VISION.md) — product principles and boundaries
- [ARCHITECTURE.md](ARCHITECTURE.md) — proposed technical design
- [ROADMAP.md](ROADMAP.md) — staged implementation plan
- [MODEL_RESEARCH.md](MODEL_RESEARCH.md) — model and runtime evaluation plan
- [SECURITY.md](SECURITY.md) — safety and privacy principles
- [docs/LOCAL_MODEL_SETUP.md](docs/LOCAL_MODEL_SETUP.md) — Windows setup instructions

## Quick start on Windows

Requirements:
- Python 3.10+
- [Ollama for Windows](https://ollama.com/) for local inference (optional for knowledge-only commands)

Create an environment and install:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Install one small candidate model:

```powershell
ollama pull qwen2.5-coder:1.5b
```

List local models:

```powershell
python -m codemind models
```

Add a local document:

```powershell
python -m codemind add-file .\python-notes.md --tags python,docs
```

Add public documentation:

```powershell
python -m codemind add-url https://docs.python.org/3/tutorial/ --tags python,official
```

Ask the local model. CodeMind retrieves a small number of relevant saved excerpts and sends them with the question:

```powershell
python -m codemind ask "How do I read JSON from a file in Python?" --model qwen2.5-coder:1.5b
```

Search the knowledge library without starting a model:

```powershell
python -m codemind search "read JSON file"
```

The default Ollama request uses a 2048-token context budget, a 512-token output limit and `keep_alive=0` so the model is asked to unload after the task. Adjust limits for your hardware:

```powershell
python -m codemind ask "Explain this function" --model qwen2.5-coder:1.5b --num-ctx 1024 --num-predict 256
```

Knowledge is stored under `%USERPROFILE%\.codemind` by default. Set `CODEMIND_HOME` to choose another directory.

## Design constraints

1. No model is required just to manage/search documentation.
2. No large vector database or embedding model is required for the first version.
3. Local model loading must be lazy and unloadable.
4. Cloud providers must be optional, explicitly configured and subject to their own quotas and privacy terms.
5. Never merge arbitrary models and assume the result is better. Model merging requires compatible architectures/tokenizers and evaluation.
6. All code execution must be permission-controlled.

## License

The project is not yet licensed. A license will be selected before distributing code or binaries.