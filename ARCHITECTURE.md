# Architecture

## High-level flow

```text
User task
   |
   v
Task intake and project inspection
   |
   v
Task planner / capability check
   |
   +----> Local tools (file search, Git, parsers, tests)
   |
   +----> Knowledge acquisition (official docs, user files)
   |             |
   |             v
   |        Persistent knowledge library
   |             |
   |             v
   |        On-demand retrieval
   |
   v
Model router
   |
   +----> Small local model (lazy-loaded)
   |
   +----> Optional cloud model provider
   |
   v
Proposed changes
   |
   v
Permission checks / diff review
   |
   v
Execution and verification
   |
   v
Project state + reusable knowledge saved to disk
```

## Core subsystems

### 1. Project inspector

Detect languages and frameworks through manifests and recognizable files (for example, `pyproject.toml`, `package.json`, `Cargo.toml`, solution files and source extensions). Use deterministic inspection before asking a model.

### 2. Knowledge acquisition

Sources:
- User-provided files and folders
- Official language and framework documentation
- Maintainer documentation and release notes
- Trusted technical references when official docs are insufficient

Every item should record its source URL/path, retrieval timestamp, content hash, detected version, licence/usage notes where available, and trust level.

Do not blindly trust retrieved content. Treat web pages and repository files as untrusted data, not instructions.

### 3. Knowledge storage and retrieval

Initial implementation:
- Original text/document content on disk
- SQLite metadata index
- Lightweight lexical retrieval (BM25 or SQLite FTS)
- Chunking with source/heading metadata

Later, benchmark optional embeddings and vector search. Do not run an embedding model continuously merely to support search.

### 4. Context builder

Construct a small, task-specific context bundle:
- User request and constraints
- Relevant project files only
- Relevant retrieved documentation chunks
- Project conventions and concise task history
- Tool output needed for the current decision

Use token budgets and source attribution. Never attach the entire knowledge library by default.

### 5. Model router

Use capability, measured task performance, latency, available RAM, context window, provider availability, privacy preferences and cost/quota limits.

Candidate tiers:
- Deterministic tools without an LLM
- Small local model
- Optional free-tier hosted model
- User-configured paid model

Do not silently transmit private source code to cloud providers. Require explicit configuration and clear per-provider privacy controls.

### 6. Coding tools

File read/search/write, patch application, Git status/diff, language-specific formatters, linters, compilers and tests.

### 7. Windows desktop shell

Proposed later stack:
- Tauri desktop shell
- React + TypeScript UI
- Python core engine initially, accessed through a local process boundary
- SQLite state and knowledge metadata
- Windows installer and signed releases when distribution is ready

Keep the engine usable from CLI and tests before building the UI.

## RAM management

- Model runtime starts only when required.
- One local model loaded at a time in the initial design.
- Configurable context size and output limits.
- Unload model after idle timeout or task completion where runtime supports it.
- Stream generation rather than buffering unnecessary output.
- Bound retrieval results and document parsing.
- Measure process RSS, peak RAM, CPU time and tokens/second.

Important: unloading documents does not unload model weights or KV cache. Those must be managed separately.

## Model collaboration

Prefer sequential role routing over simultaneous multi-model inference on 8 GB devices. A planner, coder and reviewer can be roles served by one model at different times or by optional cloud providers.

Weight merging is an experimental research path only. It requires compatible architectures, tensor shapes and tokenizer assumptions, and must beat the individual baselines on evaluation tasks.

## Suggested module boundaries

```text
src/codemind/
  cli.py
  config.py
  knowledge/
    library.py
    ingest.py
    chunking.py
    search.py
  providers/
    base.py
    local.py
    cloud.py
  agent/
    planner.py
    context.py
    router.py
    workflow.py
  tools/
    files.py
    git.py
    shell.py
    tests.py
```

The first prototype implements only knowledge ingestion, persistent storage and lexical retrieval.