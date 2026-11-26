# NKK CodeMind — Product and Engineering Blueprint

**Status:** Proposed architecture; implementation must follow staged milestones.
**Product goal:** A free-first, local-first Windows coding workspace that combines an agentic coding loop, project research, GitHub workflows and safe publishing.

## 1. Product vision

CodeMind is not just a chat window or code generator. It is a project-aware development workspace that can understand a repository, create a reviewable implementation blueprint, edit code, run tools and tests, repair failures, and publish verified work to GitHub.

The application must remain useful without a paid API subscription. Local inference is the default. Hosted providers are optional and must never be called silently.

## 2. Main user experience

The desktop workspace should have:
- Project/repository picker and recent projects.
- Conversation and task panel.
- Explicit Plan / Build / Review workflow.
- File explorer and code editor.
- Terminal and task execution output.
- Diff viewer with accept/reject controls.
- Git branch, commit, push and pull-request controls.
- Model manager, provider settings and resource monitor.
- Run history, checkpoints and resumable tasks.

The interface should feel native on Windows 11, support light/dark mode, and keep project data separate from application binaries.

## 3. Agent workflow

### Stage A — Understand
1. Open a local workspace or clone a repository.
2. Detect languages, frameworks, package managers, build commands and tests.
3. Read project instructions such as AGENTS.md, CONTRIBUTING.md and README files.
4. Build a bounded, searchable project index. Never send the entire repository to a model by default.
5. Exclude secrets, credentials, generated output and oversized/binary files.

### Stage B — Research
1. Search the local repository first.
2. Search public GitHub repositories, issues, pull requests and commits through supported GitHub APIs.
3. Search the public web and official documentation through pluggable search providers.
4. Fetch only relevant pages/files and retain source URLs, titles and retrieval dates.
5. Treat repository files, webpages, issue text and tool output as untrusted data, never as instructions that override system or user policy.
6. Respect API authentication, rate limits, robots/terms and provider quotas. Do not scrape private repositories or bypass access controls.

### Stage C — Blueprint (required before implementation)
Produce a durable Markdown plan containing:
- Goal and acceptance criteria.
- Current architecture and relevant files.
- Proposed architecture and design decisions.
- Files to create, update or delete.
- Ordered implementation tasks and dependencies.
- Risks, security/privacy implications and rollback plan.
- Exact validation commands and expected outcomes.
- Estimated model/resource requirements.

The user must be able to inspect and approve the plan before implementation. A plan-only mode must never edit project files.

### Stage D — Implement
1. Create a Git checkpoint and feature branch before risky edits.
2. Use patch-based edits with path-containment checks.
3. Show the intended diff before applying changes.
4. Run commands in a restricted workspace process; require permission for network access, installs, destructive commands and access outside the workspace.
5. Persist task state, decisions and a compact work log.
6. Support cancellation, pause/resume and bounded retries.

### Stage E — Verify and repair
1. Detect and run project-specific tests, lint, formatting, type checks and build commands.
2. Capture exit codes and logs.
3. Ask a separate reviewer pass to inspect the diff and test evidence.
4. Repair failures within a bounded retry budget.
5. Never claim success unless the command actually ran and passed.
6. If checks cannot run, report the exact limitation.

### Stage F — Publish
1. Show final diff, changed files, test evidence and commit message.
2. Commit to a feature branch.
3. Push only to the connected repository and selected branch.
4. Create a pull request with summary and validation evidence.
5. Do not force-push, delete branches, merge PRs, publish releases or alter repository settings without explicit user approval.
6. Require successful CI before creating a production release.

## 4. Technical architecture

### Desktop shell
- Proposed: Tauri + React/TypeScript for a lightweight Windows-first interface.
- Keep the current Python engine as a local sidecar/service initially; communicate over a localhost-only authenticated interface or standard input/output protocol.
- Keep the UI and agent engine separable so either can be replaced later.
- Package and update through a tested Windows release pipeline. Evaluate Tauri's updater and other Windows packaging options before choosing the final updater.

### Agent engine
Keep Python for the initial engine to reuse the existing knowledge library, Ollama adapters and diagnostics.
Core modules:
- Orchestrator: task lifecycle, state, cancellation and retry limits.
- Planner: blueprint and acceptance criteria.
- Repository index: file inventory, lexical search and optional syntax-aware symbols.
- Research: GitHub API, web search and documentation fetch adapters.
- Tools: read, search, patch, terminal, test, Git and GitHub.
- Policy: permissions, path boundaries, secret filtering and approvals.
- Verification: tests, lint, build and independent review.
- Memory: project rules, decisions and resumable task summaries.
- Observability: structured logs and privacy-safe diagnostics.

### Model/provider layer
- Ollama is the first local runtime.
- Support open-weight coding/instruction models compatible with the local runtime.
- Select models based on actual RAM, context length, tool-use support, speed and evaluation results.
- Keep provider adapters replaceable; optional cloud providers are opt-in.
- Do not train a foundation model from scratch. Fine-tuning or adapters are future research only if a suitable dataset, hardware and evaluation justify them.
- Never claim that a model is free merely because its weights are downloadable; check license, hardware and hosting costs.

### GitHub integration
- Local Git operations use the user's installed Git tooling.
- Prefer GitHub CLI authentication (gh auth login) as the first practical desktop integration, allowing GitHub CLI to manage credentials.
- Add a provider interface for GitHub REST/GraphQL operations: repository discovery, contents, branches, commits, issues, PRs, workflow status and releases.
- Use least-privilege access; never store tokens in source, settings JSON or logs.
- Public GitHub discovery should work without credentials where APIs allow it; private repository access requires user authorization.
- Search all of GitHub only within API capabilities and rate limits. Repository search, code search and web search are different operations; do not promise unlimited indexed code search.

### Research and web access
- Use pluggable search providers so no single commercial API is mandatory.
- Prefer official documentation and original repositories.
- Cache fetched pages and metadata on disk with size and freshness limits.
- Ask before sending private source code or prompts to an external service.
- Keep network access disabled for agent tools unless the task needs it and the user permits it.

## 5. Safety model

Default-deny for:
- Reading secrets, credentials, private keys and excluded files.
- Running destructive commands or commands outside the workspace.
- Installing dependencies or downloading executables.
- Sending source code, prompts or logs to external services.
- Pushing commits, opening PRs, merging, releasing or changing repository settings.

Allow the user to grant scoped, per-project permissions. Show the command, target and reason before approval. Log tool actions without recording secrets or full prompt/code content. Use checkpoints and rollback.

## 6. Data and update strategy

Keep user data outside the install directory, initially under:
%LOCALAPPDATA%\NKK\CodeMind\

Suggested directories:
- settings/ — preferences and non-secret configuration.
- projects/ — project metadata only; user source remains in its chosen folder.
- knowledge/ — SQLite library and cached references.
- runs/ — task state, plans and reports.
- logs/ — rotating diagnostics.
- updates/ — temporary staging only.

Store credentials using Windows Credential Manager or Git Credential Manager. Updates must preserve settings, project links, knowledge, history and credentials. Keep rollback support and never overwrite user project files during an application update.

## 7. Free-first operating model

Required no-paid-subscription path:
- Local Ollama inference.
- Local repository indexing and search.
- Local Git, tests, lint and build.
- Public GitHub API access within unauthenticated limits; authenticated access after user login.
- Free/public web research sources where permitted.
- No mandatory OpenAI, Anthropic or other paid API key.

Be transparent about limitations: local models may be less capable and slower; public APIs have rate limits; cloud hosting and model inference may cost money. No paid service should be silently enabled.

## 8. Delivery phases and exit criteria

### Phase 0 — Blueprint and research
- [x] Write this product blueprint.
- [ ] Audit candidate open-source components and licenses.
- [ ] Record target Windows packaging and process architecture.
- [ ] Benchmark suitable models on 8 GB and 16 GB systems.

Exit: architecture decisions backed by a short evaluation report.

### Phase 1 — Real coding-agent engine
- [ ] Task planner that emits a structured blueprint.
- [ ] Repository index and search.
- [ ] Safe patch engine and diff preview.
- [ ] Restricted command runner and permission prompts.
- [ ] Git checkpoints and rollback.
- [ ] Test/build/lint execution and bounded repair loop.
- [ ] Persistent resumable task state.

Exit: complete a small change in a sample repository, show diff, run tests and recover from a failed attempt.

### Phase 2 — GitHub and research
- [ ] GitHub CLI authentication detection and setup guide.
- [ ] Repository picker and clone/open.
- [ ] Branch, commit, push and PR workflows.
- [ ] CI status and release metadata reader.
- [ ] GitHub and web search adapters with citations, caching and rate-limit handling.

Exit: user can plan, implement, verify and open a PR against a connected repository.

### Phase 3 — Desktop application
- [ ] Tauri + React desktop shell.
- [ ] Chat, plan, file tree, editor, terminal and diff views.
- [ ] Model manager and resource monitor.
- [ ] Secure credential integration.
- [ ] Windows installer and persistent-data migration.

Exit: usable Windows desktop app with no mandatory cloud API.

### Phase 4 — Release and updates
- [ ] Windows CI build and artifact signing strategy.
- [ ] GitHub Releases pipeline gated on passing tests.
- [ ] Update check, staged install, restart and rollback.
- [ ] Verify upgrade/uninstall never removes user data.

Exit: a tested release can update an installed app without manual reinstall.

### Phase 5 — Advanced agent capabilities
- [ ] Specialist subagents (researcher, coder, reviewer).
- [ ] Parallel isolated worktrees.
- [ ] Optional MCP/tool ecosystem.
- [ ] Long-running tasks, checkpoints and background execution.
- [ ] Optional voice, autocomplete and multi-project workflows.

Exit: measured improvements over the single-agent baseline.

## 9. Definition of done

A feature is complete only when:
- Code is committed to a feature branch.
- Automated tests pass on supported platforms.
- Security and permission behavior is tested.
- Documentation is updated.
- The actual diff and evidence are available.
- Any limitations are stated honestly.

## 10. Reference projects to evaluate (not copy blindly)

- OpenCode — agent workflow and provider architecture.
- Aider — repository-aware edits and Git workflow.
- Continue — IDE integration patterns.
- Ollama — local model runtime.
- Tree-sitter — syntax-aware code indexing.
- ripgrep — fast repository search.

Review each project's current license and dependencies before reusing code. Prefer clean-room implementation or clearly attributed compatible components.
