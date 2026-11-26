import { OpenCode } from "@opencode/sdk";
import { mkdir, realpath, stat } from "node:fs/promises";
import { homedir } from "node:os";
import { isAbsolute, resolve } from "node:path";
import { createInterface } from "node:readline";

type Request = {
  id?: string | number;
  method: string;
  params?: Record<string, unknown>;
};

const dataRoot = process.env.CODEMIND_AGENT_DATA
  ? resolve(process.env.CODEMIND_AGENT_DATA)
  : resolve(homedir(), "AppData", "Local", "NKK", "CodeMind", "agent");

await mkdir(dataRoot, { recursive: true });

function send(value: Record<string, unknown>): void {
  process.stdout.write(`${JSON.stringify(value)}\n`);
}

function logError(error: unknown): void {
  const message = error instanceof Error ? error.stack ?? error.message : String(error);
  process.stderr.write(`[codemind-agent-host] ${message}\n`);
}

function requiredString(value: unknown, name: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`Missing or invalid ${name}`);
  }
  return value.trim();
}

async function resolveWorkspace(value: unknown): Promise<string> {
  const requested = requiredString(value, "workspace");
  if (!isAbsolute(requested)) {
    throw new Error("Workspace must be an absolute path");
  }

  const canonical = await realpath(requested);
  const info = await stat(canonical);
  if (!info.isDirectory()) {
    throw new Error("Workspace must be an existing directory");
  }
  return canonical;
}

const host = await OpenCode.create({
  database: { path: resolve(dataRoot, "sessions.db") },
  config: {
    directory: dataRoot,
    project: false,
    content: JSON.stringify({
      default_agent: "plan",
      permissions: [
        { action: "shell", resource: "*", effect: "deny" },
        { action: "edit", resource: "*", effect: "deny" },
        { action: "read", resource: "*.env", effect: "deny" },
        { action: "read", resource: "*.env.*", effect: "deny" },
        { action: "external_directory", resource: "*", effect: "deny" },
        { action: "webfetch", resource: "*", effect: "deny" },
        { action: "websearch", resource: "*", effect: "deny" },
        { action: "execute", resource: "*", effect: "deny" }
      ]
    })
  },
  models: { fetch: false },
  fs: { filewatcher: false },
  log: {
    level: "warn",
    emit: (entry) => {
      process.stderr.write(`[opencode:${entry.level}] ${entry.message}\n`);
    }
  }
});

let closing = false;

const eventTask = (async () => {
  try {
    for await (const event of host.events.subscribe()) {
      if (closing) break;
      send({ type: "event", event });
    }
  } catch (error) {
    if (!closing) logError(error);
  }
})();

async function handle(request: Request): Promise<void> {
  const id = request.id ?? null;
  try {
    if (request.method === "health") {
      send({ id, ok: true, result: { status: "ready", mode: "read-only-plan" } });
      return;
    }

    if (request.method === "plan") {
      const workspace = await resolveWorkspace(request.params?.workspace);
      const prompt = requiredString(request.params?.prompt, "prompt");
      const session = await host.sessions.create({
        location: { directory: workspace },
        title: "NKK CodeMind Plan"
      });

      await host.sessions.switchAgent({
        sessionID: session.id,
        agent: "plan"
      });

      await host.sessions.prompt({
        sessionID: session.id,
        text: prompt
      });

      send({
        id,
        ok: true,
        result: {
          status: "queued",
          sessionID: session.id,
          workspace,
          agent: "plan",
          safety: "shell, edits, web access, and external directories are denied"
        }
      });
      return;
    }

    if (request.method === "shutdown") {
      send({ id, ok: true, result: { status: "shutting-down" } });
      closing = true;
      await host.close();
      process.exit(0);
    }

    throw new Error(`Unsupported method: ${request.method}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    send({ id, ok: false, error: message });
  }
}

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of input) {
  if (line.length > 256_000) {
    send({ id: null, ok: false, error: "Request exceeds the 256 KB limit" });
    continue;
  }

  let request: Request;
  try {
    request = JSON.parse(line) as Request;
    if (!request || typeof request !== "object" || typeof request.method !== "string") {
      throw new Error("Request must contain a method string");
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    send({ id: null, ok: false, error: `Invalid JSON request: ${message}` });
    continue;
  }

  await handle(request);
}

closing = true;
await host.close();
await eventTask;
