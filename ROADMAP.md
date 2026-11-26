# Roadmap

## Milestone 0 — Research and reproducible baseline

- [ ] Inspect existing open-source coding agents and identify reusable components.
- [ ] Record licences and attribution requirements.
- [ ] Select candidate small coding and instruction models.
- [ ] Benchmark quantized CPU inference on 8 GB and 16 GB machines.
- [ ] Define a small, repeatable coding evaluation set.

**Exit condition:** documented evidence for model/runtime choices, including RAM, speed and code correctness.

## Milestone 1 — Knowledge library (current)

- [x] Define product vision and architecture.
- [x] Create a Python package skeleton.
- [ ] Add local text/Markdown ingestion.
- [ ] Add URL ingestion with timeouts, size limits and safe content handling.
- [ ] Store documents and metadata on disk.
- [ ] Add lexical search and source-aware snippets.
- [ ] Add tests for storage, retrieval and failure cases.

**Exit condition:** user can supply a file or URL, close the app, reopen it, and retrieve relevant passages without loading the entire corpus into memory.

## Milestone 2 — Model provider interface

- [ ] Define provider protocol.
- [ ] Add one local runtime adapter (llama.cpp server or compatible endpoint).
- [ ] Add one hosted provider adapter.
- [ ] Support cancellation, timeouts and streaming.
- [ ] Keep secrets outside repository and logs.
- [ ] Add provider health and quota failure handling.

## Milestone 3 — Coding workspace engine

- [ ] Project file inventory and language detection.
- [ ] Relevant file selection and bounded context assembly.
- [ ] Safe patch-based editing.
- [ ] Git diff and rollback-friendly workflow.
- [ ] Tool permission policy.
- [ ] Test/formatter/linters integration.

## Milestone 4 — Knowledge-aware agent loop

- [ ] Task classification and plan.
- [ ] Detect missing documentation.
- [ ] Retrieve official docs and user-supplied references.
- [ ] Generate changes.
- [ ] Run verification and repair loop with limits.
- [ ] Persist concise project state and decisions.

## Milestone 5 — Windows desktop application

- [ ] Tauri shell and React interface.
- [ ] Project picker, chat, knowledge library and diff view.
- [ ] Model/provider settings.
- [ ] Resource monitor and local model manager.
- [ ] Windows packaging, installer and update strategy.

## Milestone 6 — Evaluation and release

- [ ] Benchmark 8 GB CPU-only device.
- [ ] Benchmark 16 GB CPU-only device.
- [ ] Security review of web ingestion and command execution.
- [ ] Licence and third-party notices.
- [ ] User documentation and demo project.
- [ ] Tag a versioned release.

## Development rule

Do not mark a task complete because code was generated. Complete it only after running the relevant checks and recording their outcome.