# CodeMind Agent Host

This is the first OpenCode SDK integration spike for NKK CodeMind.

## Current scope

- Runs as a local Bun process and communicates through newline-delimited JSON on stdin/stdout.
- Embeds the OpenCode 2.4.1 SDK; it does not open a network listener.
- Stores agent sessions under the CodeMind agent data directory.
- Supports health checks and read-only Plan sessions.
- Denies shell execution, edits, secret-file reads, web access, external-directory access, and Code Mode execution.
- Sends runtime events as JSON lines on stdout. Diagnostics go to stderr.

This is deliberately **not Build mode**. It cannot edit project files or run project commands. The next stage must add CodeMind-owned permission brokering, plan review, safe patch preview, Git checkpoints, and test execution before enabling implementation.

## Requirements

- Bun 1.3+
- Node-compatible Windows environment
- An OpenCode-supported model configured for the local host; Ollama is the intended first local provider.

## Run

From this directory:

```powershell
bun install
bun run typecheck
bun run start
```

Send one JSON object per line:

```json
{"id":"health-1","method":"health"}
{"id":"plan-1","method":"plan","params":{"workspace":"C:\\Projects\\sample","prompt":"Inspect this project and propose a read-only plan to fix the login bug. Do not edit files."}}
```

The plan response returns a session ID. Agent events are emitted separately as JSON lines. The process remains alive until stdin closes or a shutdown request is sent.

## Important validation status

The source is committed as an integration prototype. It has not yet been installed, type-checked, or exercised against a real Ollama model on Windows. Do not treat this as a verified runtime release. The SDK permission configuration and event behavior must be validated in CI and on a Windows machine before enabling additional capabilities.
