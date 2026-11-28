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

Early prototype. The CLI can store/search knowledge, query an installed local Ollama model, and now writes local rotating diagnostics, exports privacy-safe support bundles, and can upload a bundle to a verified private GitHub repository when explicitly requested. It is **not yet** a full autonomous coding agent, automatic error uploader, or Windows desktop application.

See:
- [VISION.md](VISION.md) — product principles and boundaries
- [ARCHITECTURE.md](ARCHITECTURE.md) — proposed technical design
- [ROADMAP.md](ROADMAP.md) — staged implementation plan
- [MODEL_RESEARCH.md](MODEL_RESEARCH.md) — model and runtime evaluation plan
- [SECURITY.md](SECURITY.md) — safety and privacy principles
- [docs/LOCAL_MODEL_SETUP.md](docs/LOCAL_MODEL_SETUP.md) — Windows setup instructions
- [docs/CLOUD_PROVIDER_SETUP.md](docs/CLOUD_PROVIDER_SETUP.md) — optional hosted inference
- [docs/AUTOMATIC_DEVELOPMENT_LOOP.md](docs/AUTOMATIC_DEVELOPMENT_LOOP.md) — diagnostics, GitHub development and automatic updates

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

Inspect a project before asking questions:

```powershell
python -m codemind inspect .\my-project
```

Ask the local model. CodeMind retrieves relevant saved excerpts and, when `--workspace` is supplied, selects a few relevant source files rather than sending the whole repository:

```powershell
python -m codemind ask "Find the login bug and suggest a fix" --model qwen2.5-coder:1.5b --workspace .\my-project
```

The `ask --workspace` integration is **read-only context selection**. A separate, guarded patch command is now available for proposed unified diffs. It previews exact changes by default and writes nothing unless you pass `--apply`. The first version only edits existing UTF-8 text files inside the selected workspace; it rejects traversal, symlinks, file creation/deletion and stale patch context. It does not yet let the model autonomously edit files or run project commands.

Preview a proposed patch:

```powershell
python -m codemind apply-patch .\\change.patch --workspace .\\my-project
```

Apply it after reviewing the preview:

```powershell
python -m codemind apply-patch .\\change.patch --workspace .\\my-project --apply
```

See [SAFE_PATCHING.md](docs/SAFE_PATCHING.md) for supported patch format and safety limits.

```powershell
python -m codemind ask "How do I read JSON from a file in Python?" --model qwen2.5-coder:1.5b
```

Hosted inference is also available through an OpenAI-compatible API. It is **never selected automatically** in this prototype. Set your provider key in the current PowerShell session and explicitly choose the provider:

```powershell
$env:CODEMIND_API_KEY = "your-provider-key"
python -m codemind ask "Review this Python function" --provider openai-compatible --model "provider/model-name"
```

The default hosted endpoint is OpenRouter. To use another compatible service, provide its HTTPS base URL:

```powershell
python -m codemind ask "Explain this code" --provider openai-compatible --base-url https://api.groq.com/openai/v1 --model "your-model-id"
```

Provider model IDs, free-tier availability and quotas depend on the provider. Sending a prompt to a hosted provider sends that prompt, retrieved excerpts and selected workspace snippets off your computer. Use this only when you have chosen a provider and are comfortable with its data policy.

Create a support bundle containing operational logs and app metadata (not project source files or prompts):

```powershell
python -m codemind diagnostics --output .\\codemind-support.zip
```

Review the ZIP before sharing it. Logs are stored locally under `%USERPROFILE%\\.codemind\\logs` by default. To explicitly upload the bundle to a private GitHub repository, create a fine-grained token with **Contents: Read and write** and **Issues: Read and write** for that private repository, then set it only for the current PowerShell session:

```powershell
$secureToken = Read-Host 'GitHub token' -AsSecureString
$tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
try { $env:CODEMIND_GITHUB_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer) }
python -m codemind diagnostics --upload --repo YOUR_ACCOUNT/private-diagnostics
Remove-Item Env:CODEMIND_GITHUB_TOKEN
```

The command checks that the destination repository is private, uploads the ZIP, and opens a GitHub issue. Never put the token in source code or commit it to Git. Automatic upload on errors and secure Windows Credential Manager storage are still planned.

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