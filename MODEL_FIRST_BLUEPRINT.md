# CodeMind — Model-First Product Blueprint

**Status:** proposed architecture and implementation order  
**Priority:** build the reusable AI engine before the CodeMind desktop coding agent.

## 1. Product definition

CodeMind is two products that share one core:

1. **CodeMind Engine** — a model-agnostic, local-first AI engine that combines, routes and coordinates many models behind one stable API. It must be usable from Ollama-compatible clients, LM Studio-compatible clients, VS Code extensions, OpenCode-style agents and custom applications.
2. **CodeMind Studio** — a Windows-first desktop coding environment/agent built on that engine. It combines a code editor/workspace, model launcher/settings, project tools, terminal, GitHub, local Git, databases and app/web development workflows.

The engine is the first deliverable. The desktop agent comes after the engine is useful and stable.

## 2. What “combined model” means

Do not begin by trying to merge unrelated model weights. Qwen, Llama, Gemma, DeepSeek and other families may have different architectures, tensor layouts, tokenizers and licences. A naive weight merge is not a universal model and is likely to fail.

Build a **Unified Model Engine** first:

- One API and one model identity presented to client applications.
- A registry of local and remote model endpoints.
- A task router that selects one or more models by capability, quality measurements, latency, context, RAM/CPU budget, availability, privacy and user policy.
- Sequential specialist collaboration: planner → coder → reviewer, normally reusing one loaded local model on low-memory PCs.
- Retry and fallback when an endpoint is unavailable, rate-limited or fails.
- Optional ensemble/reviewer calls only when the task justifies their extra time and resource use.
- Later research: distillation, LoRA fine-tuning and compatible-family model merging, measured against a fixed coding benchmark.

The user should experience one CodeMind engine, not have to understand which model handled each subtask unless they open the run details.

## 3. Model compatibility and public API

The engine should expose a local OpenAI-compatible API first:

- `GET /v1/models`
- `POST /v1/chat/completions` (streaming and non-streaming)
- `POST /v1/embeddings` when an embedding backend is configured
- Health, readiness and usage/telemetry endpoints on localhost

Also plan an Ollama-compatible surface where practical:

- `GET /api/tags`
- `POST /api/chat`
- `POST /api/generate`

This makes CodeMind selectable as a custom OpenAI-compatible endpoint in VS Code tools and other clients. An API gateway/router is not itself a GGUF model file: it cannot simply be imported into Ollama or loaded by LM Studio as if it were model weights. To make the engine appear as a real standalone model in those runtimes, a later, separately evaluated distillation/fine-tuning/export path is required. Meanwhile, Ollama and LM Studio can be registered as local inference backends behind CodeMind.

VS Code compatibility targets:
- Continue, Cline, Roo Code and other extensions that accept custom OpenAI-compatible endpoints.
- OpenCode and similar coding agents through a configured provider/base URL.
- A future CodeMind VS Code extension for native status, model selection, chat, edit and autocomplete.

Do not fork VS Code or copy an editor wholesale in the first phase. Use an existing editor integration or a legally reusable open-source editor base after the engine is proven. If building a standalone editor later, evaluate Code-OSS/VSCodium and Monaco separately, with licence/trademark and extension compatibility review.

## 4. Model Launcher / Model Settings

A dedicated Model Center is a core product area, not a small settings page.

### Local runtimes
- Ollama
- LM Studio local server
- llama.cpp / llama-server
- Jan local API
- LocalAI and other compatible local endpoints

For each endpoint: detect or manually configure host/port, test connection, list models, inspect loaded state when supported, set model aliases, context/output limits, keep-alive/unload policy and health status.

### Remote providers
- OpenAI-compatible custom endpoints
- OpenRouter and other documented aggregators
- Google AI Studio / Gemini API and other official free-tier APIs where available
- Hugging Face inference endpoints and other documented services
- User-defined provider, base URL, API key, model ID and capability metadata

Requirements:
- API-key add/edit/remove/test controls.
- Secrets stored using Windows Credential Manager or another OS credential store, never in Git, project files or plain-text config.
- Per-provider enable/disable and per-model enable/disable.
- User-defined priority, rotation groups, fallback order and task roles.
- Usage, quota/rate-limit and last-error tracking where the provider exposes it.
- A free-only mode that excludes models with known charges; it must still warn that free quotas and eligibility can change.
- No automatic paid call. Paid endpoints remain disabled until the user explicitly enables them and sets a budget/limit.
- Never assume an endpoint is free just because a community list labels it free.

Only integrate endpoints through documented APIs or user-authorized access. Do not bypass authentication, paywalls, quotas or provider terms through reverse-engineered private endpoints. Public open-weight model downloads and documented free tiers are valid sources; each model/provider licence and usage policy must be recorded.

## 5. Model routing and collaboration

Use a deterministic policy engine before adding a learned router.

Possible task roles:
- General chat / explanation
- Coding plan
- Code generation / edit
- Code review
- Debugging
- Long-context repository analysis
- Fast autocomplete
- Embeddings / retrieval
- Web research

Routing order:
1. Check user policy (local-only, free-only, allowed providers, privacy).
2. Check endpoint health, quota and availability.
3. Check model capability and context fit.
4. Estimate RAM/CPU fit for local models.
5. Use measured benchmark quality and latency for the task role.
6. Select the smallest adequate model; escalate only when needed and allowed.
7. Record which endpoint/model was used and why.

Rotation must not randomly spray requests across every endpoint. Use priority lists, health checks, per-provider cooldowns, retry budgets and idempotency-aware retries. Avoid retrying non-idempotent tool actions blindly.

## 6. Local-first performance for ordinary Windows PCs

Initial target: the developer's 16 GB RAM, CPU-only Windows laptop; later validate 8 GB machines too. Do not promise that a tiny model will match a frontier model.

- Default to one active local generation at a time.
- Never load every registered model simultaneously.
- Use llama.cpp/GGUF or an existing local runtime where it performs best; do not rewrite inference kernels prematurely.
- Probe available RAM and CPU threads; choose conservative defaults and allow manual overrides.
- Set context and output-token budgets per task.
- Stream tokens; support stop/cancel and timeouts.
- Use a bounded queue and prevent duplicate requests from loading the same model twice.
- Unload model/KV cache after task or configurable idle period when backend supports it.
- Use disk-backed indexes and retrieval; avoid keeping whole repositories/docs in RAM.
- Keep embeddings optional; lexical search is the fallback.
- Track time-to-first-token, tokens/second, peak RSS, CPU utilization and task success.
- If a task is too large for the selected model, split it into bounded subtasks rather than increasing context without limit.
- Do not saturate the CPU in a way that freezes Windows. Adaptive thread limits and a responsive UI are requirements.

## 7. Internet and knowledge acquisition

The engine can research technical information on the internet when required:

- Search official documentation, release notes, package registries, GitHub repositories and trusted references.
- Download only bounded, relevant pages/files; respect robots, terms, authentication, rate limits and licences.
- Cache results locally with URL, timestamp, version, content hash and source attribution.
- Index documentation incrementally and retrieve relevant passages per task.
- Treat every retrieved page, repository file and issue comment as untrusted data, never as executable instructions.
- Distinguish current web facts from the model's own knowledge.
- Provide offline mode and make all network access visible/configurable.

Internet access does not mean the model automatically learns or retrains itself from every page. Retrieval gives it relevant evidence at inference time. Fine-tuning is a separate controlled pipeline.

## 8. CodeMind Studio — after the engine

The desktop application should feel like a real development environment, not just a chat window.

Core layout:
- Project explorer and file tree
- Code editor with tabs, syntax highlighting, search and terminal
- Agent/chat panel with task plan and progress
- Diff review with per-file approval
- Problems/test output panel
- Git changes, commit, branch, push and pull-request workflows
- Model Center launcher/settings
- Resource monitor and task queue

Agent capabilities:
- Read/search project files and understand project structure.
- Create websites, desktop/mobile apps, APIs and database-backed applications.
- Install dependencies only after showing what will be installed and asking permission when needed.
- Create and manage local databases (SQLite first; PostgreSQL/MySQL as optional detected services).
- Start/stop local development servers and show their localhost URLs.
- Use browser automation for preview/testing with user-visible permissions.
- Use GitHub to clone, branch, commit, push and open PRs after explicit authorization.
- Work fully offline for local projects where possible.
- Save project state and resume after restart.

Windows control:
- A separate permissioned computer-control service for opening apps, reading permitted UI state, typing/clicking and browser actions.
- Start with allowlisted actions and visible confirmation for destructive or external actions.
- Never provide unrestricted hidden desktop control to a model.
- Log actions and support immediate stop/kill switch.

## 9. Open-source projects to study, not blindly copy

| Project | Study for | Planned use |
|---|---|---|
| LiteLLM | Unified provider API, model aliases, fallback and load balancing | Architecture reference; evaluate reuse/dependency |
| RouteLLM | Model routing by task difficulty and quality/cost trade-off | Routing evaluation reference |
| Ollama | Local model lifecycle and simple local API | Backend integration |
| llama.cpp | CPU/GGUF inference and OpenAI-compatible server | Preferred low-level runtime candidate |
| LM Studio | Desktop model discovery, settings and local server | Backend integration and UX reference |
| Jan | Open-source local model manager, API server and desktop UX | Model Center reference |
| Continue | VS Code chat, edit, agent and autocomplete integration | First IDE integration target |
| Cline / Roo Code | Agent approvals, diffs and VS Code workflow | Agent UX and permission reference |
| OpenCode | Model-agnostic coding agent and terminal workflow | Coding-agent architecture reference |
| OpenClaw | Long-running agent gateway, tools and desktop/device actions | Computer-control and gateway reference |
| Aider | Git-aware coding and change review | Git workflow reference |
| OpenHands | Agent runtime, tool execution and development environment | Later agent execution reference |

Study licences and dependency requirements before adopting or copying any code. Prefer clean integration or small, attributed components over copying an entire project.

## 10. Implementation order and acceptance criteria

### Phase A — Engine API and provider registry (first)
- Define a provider protocol with capabilities, health, model discovery, streaming, cancellation and resource metadata.
- Add adapters for Ollama, LM Studio OpenAI-compatible server and llama.cpp OpenAI-compatible server.
- Add custom OpenAI-compatible remote providers.
- Add encrypted/OS-backed credentials.
- Add `/v1/models` and `/v1/chat/completions`.
- Add config file schema, import/export without secrets, and a small CLI.
- Add integration tests using mock HTTP servers; no real provider or paid API required in CI.

**Done when:** VS Code-compatible clients can point at the CodeMind localhost URL and use a selected Ollama/LM Studio/llama.cpp model through CodeMind.

### Phase B — Router, free-only mode and rotation
- Add task roles, priority groups, health checks, cooldowns, retries and fallback.
- Add user-configurable local-only/free-only/paid-enabled policy.
- Add model/provider usage and quota metadata.
- Add task routing traces and reproducible tests.

**Done when:** a request can fail over from an unavailable local endpoint to another user-approved endpoint without violating privacy or cost policy.

### Phase C — Model Center
- Build a dedicated model settings/launcher UI.
- Add/edit/test providers and API keys.
- Detect local runtimes and installed models.
- Set default model per task role, priority and fallback.
- Display model status, context, estimated memory and usage.

**Done when:** the user can manage all configured model endpoints from one screen without editing config files manually.

### Phase D — Engine quality and combined-model research
- Build a coding benchmark suite.
- Compare single model, sequential specialist roles and reviewer-assisted workflows.
- Evaluate distillation/LoRA on permitted datasets and compatible base models.
- Export a standalone GGUF model only if the resulting model improves benchmark quality and can be legally distributed.

**Done when:** claims about the combined model are supported by measured results and reproducible artifacts.

### Phase E — Coding agent and editor
- Add agent planning, bounded context, safe file tools, diff review and test runner.
- Integrate Continue/Cline/OpenCode through the API.
- Build a native VS Code extension.
- Build CodeMind Studio shell after the engine and agent APIs stabilize.

### Phase F — Project builder and computer control
- Add app scaffolding, package installation, local database setup, server lifecycle and browser preview.
- Add GitHub/local Git operations with explicit permissions.
- Add allowlisted Windows computer control and action audit logs.

## 11. Non-negotiable product rules

- Engine first; desktop app second.
- Local model first; cloud only when allowed.
- Free-only mode must never silently spend money.
- User keys stay encrypted and local.
- No hidden use of private/reverse-engineered APIs to evade provider controls.
- No simultaneous loading of multiple large models by default.
- No destructive file, shell, database, Git push or desktop action without the required approval.
- Never claim a build, test or deployment succeeded unless verified.
- The engine remains independently useful to Ollama, LM Studio, VS Code and third-party clients.


## 12. CPU-first small-model combination research — expanded priority

The goal is not merely to route to an arbitrary large model. We want to investigate whether a carefully composed system of compact, open-weight models plus deterministic tools can deliver strong coding-agent results on CPU-only Windows machines.

### Research finding: GAMA is a close prior-art project

- Repository: https://github.com/akihidem/gama
- The repository identifies an MIT licence.
- It already explores small-model routing, ensembles, tool backends, benchmark-driven routing tables, verification-gated escalation and adaptive branching/search.
- It supports OpenAI-compatible local servers including Ollama and LM Studio.
- Its README's headline comparison uses 7B + 24B + 32B models on a Mac, so that headline is not evidence that the same result is achievable on a 16 GB CPU-only laptop.
- Study its source and tests first. Reuse code only after reviewing the exact files, dependency tree, MIT notice/attribution obligations and whether its architecture fits our CPU budget. Prefer importing a small, well-tested component over copying the entire project.

This discovery means the general idea of combining local models is not wholly unexplored. Our differentiator must be a reproducible, genuinely CPU-first small-model combination, measured on ordinary Windows hardware, with integration into VS Code/Ollama/LM Studio.

### CPU inference foundation: BitNet

Study https://github.com/microsoft/BitNet (MIT repository) and its BitNet b1.58 model/runtime. The official project describes CPU kernels and a 2.4B-parameter model; published speedups are project-reported and must be independently measured on our hardware. It is a promising inference track, not proof that it is the best coding model. Keep it separate from GGUF/llama.cpp candidates until compatibility and performance are verified.

### Candidate model pool — download only after licence and format checks

Initial evaluation pool, with multiple model families and task strengths:

- Qwen2.5-Coder 0.5B / 1.5B / 3B: coding specialist candidates.
- Qwen3 0.6B / 1.7B: compact general/reasoning candidates.
- SmolLM2 135M / 360M / 1.7B: tiny routing, classification and lightweight tasks.
- Granite small code/instruct models: coding and tool-following candidates.
- StarCoder2 3B and OpenCoder 1.5B: code-generation comparisons.
- BitNet b1.58 2.4B: CPU-efficient general model experiment.
- Small embedding models, including BitNet embedding variants where runtime support is verified: retrieval, not chat generation.

This is a candidate pool, not a promise that every model has a compatible licence, GGUF file, Ollama recipe or good Windows CPU performance. For each exact checkpoint record model-card URL, immutable revision, licence, tokenizer, architecture, context, format, quantization, download size and intended use. Do not redistribute weights unless the licence permits it.

### Combination experiments — test all, keep only measured winners

1. **Specialist routing:** one compact model per task class (code, explanation, planning, review, retrieval classification).
2. **Sequential specialist pipeline:** planner → coder → reviewer, with one model unloaded before the next is loaded to keep peak RAM low.
3. **Tool-augmented model:** a small model calls deterministic tools (tests, compiler, calculator, search, AST, Git) instead of trying to remember everything.
4. **Independent review:** a second model reviews a patch only when its different failure profile justifies the added latency.
5. **Selective ensemble:** ask multiple small models only for high-uncertainty tasks; aggregate using tests, static checks or a verifier rather than trusting majority vote alone.
6. **Adaptive search:** explore alternative solutions, then spend more inference on the promising candidate. Bound branches, calls, time and memory.
7. **Weight merging:** use MergeKit methods such as task arithmetic, TIES and DARE only for compatible model families/checkpoints (matching architecture and tensor structure, and usually a shared base). Never average unrelated architectures or tokenizers.
8. **Distillation / LoRA:** train a compact student on legally usable teacher outputs/data and verified coding tasks; measure whether it retains useful skills at a lower CPU cost.
9. **Quantization/runtime comparison:** compare GGUF quantization levels and BitNet formats on supported hardware; quality loss and actual RSS matter as much as file size.

### Benchmark design for our actual laptop

Use the Dell Latitude 7420 class target (Intel i7-1185G7, 16 GB RAM, CPU-only) as the first reference machine. Also test an 8 GB profile if possible.

Measure each candidate and combination:
- Peak process and system RAM, including model weights and KV cache
- CPU utilization, thread count, temperature/throttling where observable
- Time to first token, prompt processing speed and generation tokens/second
- Cold start and warm start
- Task success using hidden/sealed tests, not model self-rating
- Patch correctness, regression rate, tool-call success and hallucinated APIs
- Total wall-clock time and energy/power where measurable
- Whether the machine remains responsive while inference runs

Benchmark tasks: repository Q&A, small function + tests, bug fix, multi-file change, framework documentation lookup, debugging test output, code review, and build a minimal web app with a local database.

Use identical prompts, context budgets and test environments. Separate development/tuning tasks from a sealed evaluation set. Keep negative results and failed combinations in the report.

### CPU-first architecture hypothesis

Prefer a small number of sequential model calls plus deterministic tools over running many models in parallel. Use complementary specialists, not several near-identical models. Maintain a memory-aware scheduler that loads one model, runs it, saves the structured result, unloads it, and then loads the next model. Parallel execution is allowed only when the measured free RAM budget safely supports it.

### Download and source-code policy

- First clone and inspect the GAMA source, tests, dependency list and MIT licence; do not immediately vendor it.
- Study BitNet source and build instructions independently; its runtime is a separate inference backend.
- Download candidate weights into a dedicated model cache, not the Git repository.
- Keep model binaries out of Git; use a manifest with model IDs, revisions, hashes, licences and download instructions.
- Never execute arbitrary scripts shipped with model repositories without inspection.
- Do not scrape private endpoints or bypass rate limits. Use public model files and documented APIs.
- The model set is extensible: evaluate new small models continuously, but promote a model only after reproducible benchmark results.

### Immediate next implementation milestone

Create a standalone `codemind-lab` experiment package before changing the production engine:
- Model manifest and licence metadata.
- OpenAI-compatible backend adapter for Ollama / LM Studio / llama.cpp.
- Task suite and deterministic graders.
- Baseline single-model runs.
- Routing, sequential collaboration, verifier and selective ensemble experiments.
- JSON/CSV results with hardware, model revision, latency and peak memory.
- A comparison report that identifies the best measured configuration for CPU-only coding tasks.

Only after the lab proves a winning combination should its routing/collaboration strategy be integrated into CodeMind Engine.
