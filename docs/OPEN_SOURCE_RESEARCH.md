# Open-Source Project Research and Architecture Decision

**Review date:** 26 November 2026  
**Purpose:** Learn from successful open-source developer tools, reuse compatible capabilities responsibly, and avoid fragile foundations.

This is an engineering research record, not an exhaustive audit. Before importing code or shipping a dependency, re-check the exact commit, license file, dependency licenses, security advisories, release activity, and platform support.

## 1. Product strategy

NKK CodeMind will not be a blind merge of several complete applications. It will be one unified product with:
- One NKK desktop experience and design system.
- One project/workspace model and durable task history.
- One safety and permission policy controlled by CodeMind.
- One model-selection and token-budget policy.
- Pluggable agent runtimes, tools, providers, and editor capabilities.
- A documented third-party component register and attribution notices.

Prefer stable SDKs, APIs, protocols, and adapters. Copy source code only when there is a clear technical reason and exact license/dependency obligations have been reviewed.

## 2. Reference-project capability map

| Project | Strengths worth learning from | Risks and lessons | CodeMind decision |
|---|---|---|---|
| **OpenCode** (MIT) | Multi-provider model support, agent modes, tools, MCP, plugins, sessions, events, undo/redo, SDK | Generic defaults can allow broad access; permission defaults and external-directory boundaries need deliberate hardening. MCP tools also consume context. | **Primary agent-runtime candidate.** Integrate through its SDK, not by copying its UI or maintaining a large fork. |
| **Cline** (Apache-2.0) | Human-in-the-loop approvals, task visibility, editor workflow | Asking for every harmless action becomes tiring; use scoped remembered permissions and risk levels. | Learn approval UX, explainable tool actions, and checkpoints. CodeMind policy remains authoritative. |
| **Aider** (Apache-2.0) | Repository map, Git-aware edits, focused file changes, test/lint feedback | Terminal-first interaction is not a complete desktop workspace; check maintenance pace before adopting dependencies. | Reproduce repository-map and Git-review ideas behind replaceable interfaces. |
| **Goose** (Apache-2.0) | Desktop + CLI, broad providers, MCP extensions, reusable recipes, subagents, ACP, security features | General-purpose extensibility can add complexity and context overhead. | Study ACP, recipes, extension lifecycle, and provider onboarding. |
| **OpenHands** (MIT) | Larger autonomous software-engineering workflows and runtime isolation concepts | Full platform/runtime is heavier than the first Windows release. | Borrow evaluation and sandbox concepts; do not import its full platform into the MVP. |
| **Kilo Code** (MIT) | Consolidated agentic workflow and broad model choice; project has adopted OpenCode foundations | Downstream products can inherit upstream breaking changes and duplicate abstractions. | Study its integration choices; avoid a second provider layer on top of OpenCode. |
| **Monaco Editor** (MIT) | Proven embeddable editor component from the VS Code ecosystem | Monaco alone is not a full IDE; language servers, terminal, debugging, explorer, and workspace services are separate. | Candidate editor inside a custom NKK workbench. |
| **Code-OSS / VS Code** | Full workbench, extension model, mature editor workflows | Large build/maintenance surface; Microsoft-branded distribution assets and services cannot be assumed available to redistributors. | No full Code-OSS fork for the MVP. |
| **Repomix** | Compact, structured repository context packaging | Packing a whole repository can still waste context and expose irrelevant/private content. | Use context-packaging ideas selectively; retrieve only task-relevant files and symbols. |

## 3. Product lessons to adopt

### Planning and execution
- Separate Explore, Plan, Build, and Review responsibilities.
- Plan mode must not edit normal project files.
- Every implementation task has acceptance criteria, affected paths, risks, and verification commands.
- Show what the agent is doing and what changed.
- Persist checkpoints so long tasks can resume after restart.

### Safe approvals
- Default-deny dangerous operations.
- Classify actions: read, search, edit, shell, install, network, credential access, Git push, PR, merge, and release.
- Auto-allow only narrowly scoped, low-risk operations.
- Ask before installs, destructive commands, external transfers, access outside the workspace, and publishing.
- Explicit deny rules must override remembered approvals.
- Never let a model approve its own risky action.

### Repository intelligence
- Build a deterministic project map from manifests, directory structure, symbols, imports, and Git history.
- Use lexical search first; add syntax-aware indexing when it materially helps.
- Retrieve relevant files and code windows progressively.
- Send focused patches or excerpts instead of entire repositories.
- Keep source references explaining why a file was selected.

### Verification
- Run project tests, lint, format, type-check, and build commands where available.
- Distinguish passed, failed, skipped, and unavailable checks.
- Limit repair attempts and preserve useful failure evidence.
- A model saying “fixed” is not proof; command output and tests are proof.

## 4. Failure patterns to avoid

1. **Unbounded autonomy:** mitigate with policy enforcement outside the model, scoped workspace roots, approvals, checkpoints, and command timeouts.
2. **Prompt injection through repository content:** READMEs, issues, web pages, comments, and tool output are untrusted data; they cannot grant permissions or override policy.
3. **Provider lock-in:** capability-test adapters; verify tool calling and structured output per model.
4. **Token bloat:** many agents, MCP tools, huge prompts, and full-repository dumps can increase cost without improving results. Use local retrieval, minimal tool catalogs, compact task state, budgets, and selective escalation.
5. **False confidence:** generated code can look convincing while tests fail or never ran. Completion must be evidence-based.
6. **Overloaded first release:** importing a full autonomous platform, IDE, and model runtime at once makes the app slow and hard to debug. Build small vertical slices.
7. **Unmaintained dependencies:** popularity does not guarantee maintenance. Track releases, issue response, security advisories, bus-factor signals, and replacement paths.
8. **License surprises:** a repository license does not automatically cover every dependency, model, dataset, marketplace, icon, or bundled asset. Review each one.
9. **Cloud data leakage:** use Local Only, Hybrid, and Cloud Only modes, clear data-scope notices, secret filtering, and a global cloud-off switch.
10. **Unsafe updates:** keep user data outside the install directory, stage updates, verify artifacts, and support rollback.

## 5. Architecture decision: OpenCode as the first agent runtime

**Decision:** Adopt the OpenCode SDK as the first coding-agent runtime behind a CodeMind-owned adapter.

Why:
- The SDK can host OpenCode inside an application process and exposes sessions, prompts, and event streams.
- It avoids building a complete tool-calling/session engine from zero.
- OpenCode supports a broad provider ecosystem, local models, plugins, MCP, custom agents, and permissions.
- Its MIT license is a promising integration basis, subject to a complete dependency and notice audit.

CodeMind still owns:
- NKK desktop shell, navigation, editor/workbench, onboarding, settings, and visual identity.
- Project registry, durable project memory, plans, acceptance criteria, and checkpoints.
- Local-first knowledge index and token/context preparation.
- Model routing: smallest capable model, local RAM awareness, and explicit cloud escalation.
- A stricter safety policy than generic runtime defaults.
- GitHub discovery, repository workflows, CI visibility, publishing approvals, diagnostics, and updates.

### Proposed process boundaries
- **Desktop:** Tauri + React + TypeScript, Windows-first.
- **Agent host:** pinned OpenCode SDK in a managed local sidecar/service, with explicit lifecycle and event streaming.
- **CodeMind intelligence:** retain the current Python knowledge/indexing prototype initially; connect it through a narrow local interface/custom tools. Re-evaluate a TypeScript migration only after a working vertical slice.
- **Storage:** SQLite and files under %LOCALAPPDATA%/NKK/CodeMind/; project source remains in its chosen workspace.
- **Editor:** Monaco inside the NKK workbench; add language-server support and terminal integration separately.
- **GitHub:** Git/GitHub CLI first, then a dedicated least-privilege adapter.

Do not expose an unauthenticated local agent server to the network. Prefer in-process SDK hosting or authenticated local IPC. If loopback HTTP is required, bind only to localhost, use an unguessable per-launch token, validate origins, and shut down cleanly.

### Runtime hardening required before Build mode
- Deny Git push, merge, release, and destructive commands by default.
- Require approval for shell commands unless a narrow project policy explicitly allows them.
- Deny secret-file reads by default; allow safe example templates only.
- Explicitly constrain external-directory reads and writes.
- Use isolated Git worktrees for risky or parallel work.
- Enforce CodeMind policy before every tool invocation; runtime configuration is not the only security boundary.
- Cap model steps, retries, output size, command duration, and task budget.
- Record tool events and diffs without logging secrets or full private prompts.

## 6. Editor decision

Start with **Monaco + a custom NKK workbench**, not a full Code-OSS fork.

This keeps the UI under our control and avoids the full maintenance burden of a complete IDE distribution. The first workbench should include project explorer, tabs, Monaco editor, agent chat, plan/review panel, diff viewer, integrated terminal, problems/test output, and model/resource status.

Monaco is not a complete IDE. Language Server Protocol, debug adapters, terminal, search, file watching, and extension support must be added deliberately as replaceable subsystems.

## 7. Token economy: measure success, don't guess

Optimize **cost per verified task**, not simply the fewest tokens.

1. Deterministic tools first: file tree, manifests, Git diff, tests, parsers, and search.
2. Small local model: classify tasks, rank files, summarize logs/docs, prepare context.
3. Strong local model: attempt implementation if quality and RAM allow.
4. Cloud escalation: only for a demonstrated capability gap and when explicitly enabled.
5. Local verifier: check patch scope, acceptance criteria, test results, and suspicious output.
6. Save a compact checkpoint: task, decisions, files touched, test evidence, unresolved issues.

Measure token counts where providers expose them, local prompt-size estimates, wall time, peak RAM, tool calls, retries, and test success. Never claim savings without comparing the same task and success criteria. Avoid parallel agents by default on CPU-only 8 GB devices.

## 8. Preliminary license and maintenance register

| Component | Upstream | Observed license/status signal | Reuse plan |
|---|---|---|---|
| OpenCode | https://github.com/anomalyco/opencode | MIT shown on repository; active project/docs | SDK integration; pin versions and audit dependencies |
| Cline | https://github.com/cline/cline | Apache-2.0 shown on repository | Study UX and workflow; no source copy planned |
| Aider | https://github.com/Aider-AI/aider | Apache-2.0 shown on repository | Study repository map/Git techniques; no runtime dependency |
| Goose | https://github.com/aaif-goose/goose | Apache-2.0 documented by project | Study ACP, recipes, extension model |
| OpenHands | https://github.com/OpenHands/OpenHands | MIT shown on repository | Study isolation and task evaluation |
| Kilo Code | https://github.com/Kilo-Org/kilocode | MIT shown on repository | Study product consolidation and upstream choices |
| Monaco Editor | https://github.com/microsoft/monaco-editor | MIT shown on repository | Candidate editor dependency |
| Code-OSS | https://github.com/microsoft/vscode | Source is MIT; distribution assets/services differ | No full fork in MVP |

This is a preliminary register, not legal advice or a substitute for a release-time Software Bill of Materials. Keep upstream copyright and license notices for reused code.

## 9. Implementation order

1. Pin and prototype the OpenCode SDK in a minimal local host.
2. Prove it connects to Ollama and runs a read-only Explore/Plan task.
3. Add CodeMind's local project map and retrieval as tools.
4. Add a policy wrapper and tests proving push/merge/destructive actions are blocked.
5. Add patch preview, approval, Git checkpoint, test execution, and bounded repair.
6. Build the Tauri + React shell around the working engine.
7. Add Monaco and the remaining workbench panels.
8. Add GitHub workflows and CI visibility.
9. Add update packaging only after persistent storage is stable.

**First vertical-slice acceptance test:** open a sample repository, investigate a seeded bug, generate a read-only plan, request permission before editing, apply a focused patch, run the relevant test, show the diff and evidence, and leave Git push disabled.
