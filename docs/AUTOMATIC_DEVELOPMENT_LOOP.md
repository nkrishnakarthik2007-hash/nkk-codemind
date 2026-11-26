# Automatic Diagnostics, AI Development and App Updates

This document defines the intended DroidBox-style workflow for CodeMind. It is an architecture plan, not a claim that all integrations are already implemented.

## Current state

CodeMind is currently a Python CLI prototype. It can inspect a workspace, select bounded source context, retrieve saved knowledge, call local Ollama or an explicitly selected OpenAI-compatible provider, and write local rotating JSONL diagnostics. `codemind diagnostics --output codemind-support.zip` exports a support bundle containing the app manifest and rotated logs.

The local diagnostics foundation is implemented. It does not yet have automatic remote log upload, a GitHub-connected coding agent, a desktop shell, or an installed-app updater.

## Target workflow

1. **Implemented:** CodeMind writes structured, rotating JSONL diagnostic logs locally under `%USERPROFILE%\\.codemind\\logs` (or `$CODEMIND_HOME\\logs`).
2. **Partially implemented:** the CLI records command start/failure metadata and can export a support ZIP. Automatic error snapshots, environment summary and correlation IDs remain future work.
3. **Local baseline implemented:** common credential patterns are redacted and sensitive metadata keys are excluded. The support ZIP includes only the diagnostics log files and a small manifest; it does not collect project files, prompts or model output.
4. The app uploads a bounded diagnostic report to a **separate private GitHub diagnostics repository** and creates/updates an issue. Never upload raw logs to this public source repository.
5. The coding assistant can retrieve the report through the connected GitHub integration, investigate the failure, edit the CodeMind source repository, and run CI.
6. A release is published only after tests/build checks pass.
7. Installed CodeMind checks the GitHub Releases update feed, downloads the signed/versioned update, replaces application files, and restarts.
8. User data remains in a stable location outside the install directory and is never overwritten by an app update.

## ChatGPT connection: important product boundary

A desktop app cannot attach itself to a particular ChatGPT browser conversation or reuse a ChatGPT Go subscription as an API credential. ChatGPT consumer subscriptions and API billing are separate products.

Supported connection design:
- In-app AI: local Ollama by default, plus an optional user-configured OpenAI API key or another compatible provider.
- ChatGPT-assisted development: upload sanitized diagnostics to the private GitHub diagnostics repository. The user can ask ChatGPT to inspect that repository through its GitHub connection; this conversation can also work on the source repository when GitHub access is connected.
- Do not pretend that an uploaded GitHub issue automatically sends a message into the current ChatGPT conversation. That requires a separately supported messaging/agent integration.

## GitHub access and privacy

- Use a narrowly scoped GitHub App or OAuth/device authorization for the desktop app; do not ask users to paste a personal access token into source code.
- Keep credentials in Windows Credential Manager or the OS secure credential store.
- Use a separate private diagnostics repository, not the public source repository.
- Make diagnostic upload configurable and visible. Never silently upload full source code, project files, personal information, APKs, or arbitrary environment data.
- Redact API keys, tokens, passwords, cookies, authorization headers, and common private-key formats before upload.
- Apply size limits, log rotation, retention and a local delete/export control.
- GitHub issues should contain a short summary, app version, OS/runtime metadata, correlation ID and a link/path to the private report.

## Safe source-code development loop

- The coding agent works on a feature branch.
- It reads the diagnostic report and only the project files needed for the fix.
- It creates a patch and tests it.
- GitHub Actions runs unit tests, lint, security checks and Windows packaging.
- Failed checks block release publication.
- Successful changes are published as a versioned GitHub Release. Direct pushes to the default branch alone must not cause an untested binary to be installed.

## Automatic updates

The eventual Windows desktop distribution should use a versioned updater feed backed by GitHub Releases (the DroidBox project uses the Velopack approach).

- Build a Windows package from the tested source revision.
- Publish installer/update artifacts and release metadata.
- Check for updates at startup and periodically, with a manual Check for updates action.
- Download and stage the update before replacing application binaries.
- Restart into the new version and retain the previous working version for rollback.
- Keep all persistent user data outside the application install directory.

Suggested persistent CodeMind data directory:
`%LOCALAPPDATA%\\NKK\\CodeMind\\`

Suggested subdirectories:
- `logs\\` — rotating local logs
- `knowledge\\` — SQLite knowledge library and documents
- `projects\\` — only if the user explicitly chooses CodeMind-managed project copies
- `settings\\` — app settings and provider preferences
- `updates\\` — temporary update staging only

The updater must never delete or replace the persistent data directory.

## Release policy

A commit is a source-code change, not automatically a safe app release. Every change should trigger CI. Only a successful Windows build and passing required checks may be promoted to a release. The installed app then updates from that release without manual download, extraction, uninstall or reinstall.

## Implementation order

1. **Done (initial foundation):** add structured rotating diagnostics, common-secret redaction, and a local support ZIP export to the Python engine.
2. Add private GitHub diagnostics upload and issue creation with scoped authentication.
3. Add a GitHub-assisted development workflow and branch/PR/CI checks.
4. Build the Windows desktop shell and secure settings/credential storage.
5. Package the app and integrate the updater.
6. Test update, rollback, crash recovery and preservation of existing user data on Windows.
