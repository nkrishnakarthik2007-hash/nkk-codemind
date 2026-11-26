# Security and Privacy

NKK CodeMind can read source code, retrieve web content and execute developer tools. These capabilities require explicit safety boundaries.

## Source code and cloud providers

- Local processing is the default.
- Cloud providers are opt-in and configured by the user.
- Clearly identify when source code or prompts will leave the machine.
- Do not silently upload entire repositories.
- Redact secrets from context where practical.
- Keep API keys in the operating system's credential store or environment; never commit them.

## Web and document ingestion

- Treat retrieved pages, READMEs, code comments and documents as untrusted data.
- Retrieved content must never override system policy or grant tools new permissions.
- Enforce request timeouts, content-size limits and redirect limits.
- Block localhost, private-network and link-local destinations in URL ingestion to reduce SSRF risk.
- Respect robots, terms, copyright and source licences. Prefer official documentation and user-provided files.
- Store source URL, retrieval time and content hash.

## Filesystem

- Restrict writes to the selected workspace and CodeMind data directory.
- Do not follow symlinks outside allowed roots without explicit permission.
- Show diffs before destructive or broad changes.
- Keep backups or Git checkpoints where possible.

## Shell and execution

- No unrestricted shell execution by default.
- Classify commands by risk.
- Require user approval for installs, deletion, network-sensitive actions, privilege escalation and commands outside the workspace.
- Use timeouts and bounded output.
- Run tests in the project environment and report exactly what ran.

## Model output

- Treat model output as untrusted.
- Validate paths and tool arguments.
- Never execute arbitrary generated instructions without policy checks.
- A model's claim that a task is safe or complete is not verification.

## Reporting vulnerabilities

Please report security issues privately to the repository owner rather than publishing exploit details in an issue.