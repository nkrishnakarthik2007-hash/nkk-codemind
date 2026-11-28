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
