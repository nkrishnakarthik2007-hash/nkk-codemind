# NKK CodeMind Project Status

Last reviewed: 2026-11-27

## Current product state
- CodeMind is a Python CLI prototype, not a Windows desktop coding agent yet.
- It can store/search local knowledge, ingest HTTPS documentation, query a local Ollama model, optionally call an explicitly selected OpenAI-compatible provider, and select a small set of relevant project files as read-only context.
- It does not yet edit project files or run development commands autonomously.
- No desktop installer or published desktop release exists.

## Verification
- GitHub Actions tests pass on Windows and Ubuntu with Python 3.10, 3.11 and 3.12; Ruff lint also passes.
- Workspace selection skips common secret files, symlinks, ignored directories and oversized files, and redacts common secret patterns before sending snippets to a model.
- URL ingestion currently requires HTTPS, rejects private/non-global IPs, refuses redirects, uses a 12-second timeout and caps responses at 2 MB.
- The URL fetcher is still a prototype: DNS validation and the later network connection are separate operations, so DNS-rebinding/TOCTOU hardening should be revisited before unattended ingestion.
- No new confirmed runtime bug was identified in this review.

## Open development work
- PR #1, `Add NKK CodeMind autonomous coding agent blueprint`, is a draft.
- PR #2, `Define shared NKK desktop update and diagnostics experience`, is also a draft and is based on PR #1.
- Both PR branches have passing test workflows. Neither is a desktop release.

## Feedback and support
- No in-app feedback form exists in this CLI prototype. Use the repository's GitHub Issues for early bug reports and feature suggestions; do not attach prompts, private code or credentials.

## Next engineering step
1. Implement a permission-controlled workspace tool layer for read, edit, test and command execution.
2. Require explicit approval for writes, installs, destructive actions, network-sensitive actions and commands outside the selected workspace.
3. Add a dry-run/plan view, bounded output, command timeouts, rollback/diff review and tests before enabling real edits.
4. Measure peak RAM, CPU, time-to-first-token and tokens/second on CPU-only Windows hardware before choosing default models.

## Product and growth
- First make the CLI reliable and useful for a small set of real coding tasks; collect feedback from early developers before building a large desktop shell.
- A free local-first core is the right launch model. Add a donation/sponsorship link only after public demos, documentation and repeat usage exist.
- Consider paid hosted inference or team features only after there is a clear support and operating-cost reason; never make cloud inference automatic.
