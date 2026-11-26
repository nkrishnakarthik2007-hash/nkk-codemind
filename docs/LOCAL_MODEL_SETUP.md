# Windows Local Model Setup (Prototype)

The first local inference adapter uses [Ollama](https://ollama.com/). Ollama is a separate runtime; CodeMind talks to its local HTTP API.

## 1. Install Ollama

Install Ollama for Windows from its official website. Start it and open PowerShell.

Check that the local API is responding:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

## 2. Download one small coding model

For an initial experiment, try:

```powershell
ollama pull qwen2.5-coder:1.5b
```

This is a candidate, not a promise that it will be fast or strong enough on every CPU. Model size on disk is not the same as total RAM use. Context/KV cache and runtime overhead also consume memory.

Do not download several models at once on an 8 GB machine. Start with one.

## 3. Install CodeMind

From the repository folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## 4. Check models and ask a question

```powershell
python -m codemind models
python -m codemind ask "Write a Python function that reads JSON safely." --model qwen2.5-coder:1.5b
```

CodeMind sets Ollama `keep_alive=0` by default. This asks Ollama to unload the model after the request to reduce idle RAM use. It means the next request may take longer because the model must load again.

Use a smaller context/output limit on memory-constrained computers:

```powershell
python -m codemind ask "Explain this function" --model qwen2.5-coder:1.5b --num-ctx 1024 --num-predict 256
```

## 5. Add documentation to the prompt

Add official documentation or your own notes:

```powershell
python -m codemind add-url https://docs.python.org/3/tutorial/ --tags python,official
python -m codemind ask "Show how Python handles exceptions" --model qwen2.5-coder:1.5b
```

The ask command retrieves a few matching knowledge excerpts and supplies them as context. It does not fine-tune or retrain the model.

## Troubleshooting

- If CodeMind cannot connect, ensure Ollama is running.
- If the model is missing, run `ollama pull MODEL_NAME`.
- If RAM is high, lower `--num-ctx`, lower `--num-predict`, and ensure only one model is loaded.
- If generation is slow, compare a smaller model and measure tokens/second.
- Never paste API keys into source files or commit them.