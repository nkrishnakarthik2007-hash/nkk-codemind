# Roadmap

## Milestone 0 — Research and reproducible baseline

- [ ] Inspect existing open-source coding agents and identify reusable components.
- [ ] Record licences and attribution requirements.
- [ ] Select candidate small coding and instruction models.
- [ ] Benchmark quantized CPU inference on 8 GB and 16 GB machines.
- [ ] Define a small, repeatable coding evaluation set.

**Exit condition:** documented evidence for model/runtime choices, including RAM, speed and code correctness.

## Milestone 1 — Knowledge library

- [x] Define product vision and architecture.
- [x] Create a Python package skeleton.
- [x] Add local UTF-8 text/Markdown ingestion.
- [x] Add basic HTTPS URL ingestion with timeouts and response-size limits (prototype; hardening remains).
- [x] Store documents and metadata on disk.
- [x] Add SQLite FTS lexical search and source-aware snippets.
- [x] Add tests for storage and retrieval.

**Exit condition:** user can supply a file or URL, close the app, reopen it, and retrieve relevant passages without loading the entire corpus at startup.

## Milestone 2 — Local model connection (prototype)

- [x] Add Ollama local HTTP adapter.
- [x] List locally installed Ollama models.
- [x] Send bounded-context generation requests.
- [x] Default to unloading the model after each request.
- [x] Retrieve relevant saved knowledge for a coding question.
- [x] Add provider and CLI unit tests.
- [ ] Verify the workflow against a real installed model on Windows.
- [ ] Measure peak RAM, CPU, time-to-first-token and tokens/second.

## Milestone 3 — Provider routing

- [x] Define a common provider protocol.
- [ ] Add a llama.cpp adapter or evaluate Ollama's underlying runtime first.
- [x] Add one optional OpenAI-compatible hosted provider adapter.
- [ ] Implement model selection and fallback based on task, capability, latency, privacy and quota.
- [ ] Support streaming and cancellation.
- [x] Require explicit hosted-provider selection and HTTPS endpoints.
- [x] Keep API keys in environment variables rather than repository files.

## Milestone 4 — Coding workspace engine

- [x] Project file inventory and basic language/framework detection.
- [x] Relevant file selection and bounded read-only context assembly.
- [ ] Safe patch-based editing.
- [ ] Git diff and rollback-friendly workflow.
- [ ] Tool permission policy.
- [ ] Test/formatter/linters integration.

## Milestone 5 — Knowledge-aware agent loop

- [ ] Task classification and plan.
- [ ] Detect missing documentation.
- [ ] Retrieve official docs and user-supplied references.
- [ ] Generate changes.
- [ ] Run verification and repair loop with limits.
- [ ] Persist concise project state and decisions.

## Milestone 6 — Windows desktop application

- [ ] Tauri shell and React interface.
- [ ] Project picker, chat, knowledge library and diff view.
- [ ] Model/provider settings.
- [ ] Resource monitor and local model manager.
- [ ] Windows packaging, installer and update strategy.

## Milestone 7 — Evaluation and release

- [ ] Benchmark 8 GB CPU-only device.
- [ ] Benchmark 16 GB CPU-only device.
- [ ] Security review of web ingestion and command execution.
- [ ] Licence and third-party notices.
- [ ] User documentation and demo project.
- [ ] Tag a versioned release.

## Development rule

Do not mark a task complete because code was generated. Complete it only after running the relevant checks and recording their outcome.