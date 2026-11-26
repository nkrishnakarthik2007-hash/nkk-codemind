# Optional Hosted Model Setup

CodeMind defaults to local Ollama inference. Hosted inference is an explicit choice using:

```powershell
python -m codemind ask "Your task" --provider openai-compatible --model "provider/model-id"
```

## Configure credentials

Set the API key in the current PowerShell session:

```powershell
$env:CODEMIND_API_KEY = "your-api-key"
```

Do not paste keys into source code, commit them, or share terminal screenshots containing them.

## OpenRouter (default endpoint)

```powershell
python -m codemind ask "Write a Python unit test" --provider openai-compatible --model "provider/model-id"
```

The default base URL is `https://openrouter.ai/api/v1`. Select an actual model ID from the provider's current model catalogue. Free model availability, rate limits and quotas change; CodeMind does not guarantee free inference.

## Other OpenAI-compatible providers

Supply the provider's documented HTTPS base URL:

```powershell
python -m codemind ask "Review this code" --provider openai-compatible --base-url https://api.groq.com/openai/v1 --model "provider-model-id"
```

The adapter uses the standard `/chat/completions` endpoint. Compatibility varies: some providers use different token-limit fields or additional required headers. Those differences may require a dedicated adapter later.

## Privacy

Selecting `--provider openai-compatible` sends the task prompt and any retrieved knowledge excerpts to the configured provider. Do not use hosted inference for confidential code unless you have checked the provider's data handling terms and have permission to share that code.

Hosted endpoints must use HTTPS. API keys are sent in the Authorization header and are never written to the CodeMind knowledge database.

## Local-only mode

Omit `--provider` to use Ollama. The default is local inference. No cloud fallback is currently implemented, and CodeMind will not silently send local prompts to a hosted provider.