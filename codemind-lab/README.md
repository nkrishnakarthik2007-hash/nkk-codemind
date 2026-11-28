# NKK CodeMind Lab — CPU-first small-model experiments

This is the first implementation package for the model-first CodeMind direction. It uses **GAMA** as the upstream composition and benchmarking foundation, then adds NKK-specific CPU memory checks, serialized inference and a sequential development pipeline.

## Why GAMA

Upstream: https://github.com/akihidem/gama  
Licence: MIT. Copyright and permission notice must be retained when redistributing GAMA source or substantial portions.

GAMA already provides:
- `GamaBackend`: task-class routing.
- `EnsembleBackend`: sequential model candidates and synthesis.
- `ToolBackend`: program-aided solving (not enabled by this initial lab).
- `MeshflowBackend`: verification-gated escalation.
- `ABMCTSBackend`: adaptive wider/deeper candidate search.
- Deterministic benchmark suites, measured routing proposals and configuration composition.

We depend on the upstream package instead of copying unreviewed source files. This keeps the upstream MIT attribution intact and lets us focus on the CPU-specific changes. Before vendoring or modifying upstream code, review the exact file, tests, licence notice and dependency impact.

## 6 GB RAM design

CPU inference still consumes RAM. The initial policy is deliberately conservative:
- One active model request at a time.
- Configurable Ollama CPU thread count (default 4) to avoid monopolizing every logical core.
- Sequential ensembles, never parallel model fan-out.
- Default 2,048-token context and bounded output.
- Ollama native API with `keep_alive=0` by default to request unloading after each response.
- Configurable safety reserve (default 1.5 GB).
- Optional user-supplied estimated runtime RAM per model. The estimate includes weights, KV cache and runtime overhead; file size alone is not sufficient.
- OpenAI-compatible endpoints (LM Studio / llama.cpp) are serialized, but the server may keep its model loaded. CodeMind cannot promise unload unless that runtime exposes and we implement its lifecycle API.

The 6 GB target is a test profile, not a guarantee. Windows, drivers and background apps use memory too. Start with one small quantized model and measure actual free RAM, process RSS and response speed.

## Install

Python 3.10+:

```powershell
cd codemind-lab
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item models.example.json models.json
```

The package installs GAMA from its public Git repository. Internet access is required for this initial install. No model weights are automatically downloaded.

## Configure

Edit `models.json`. Keep API keys out of the file; set the environment variable named by `api_key_env` for remote providers. For local use, start Ollama or the LM Studio local server.

Example first model:

```powershell
# Download through CodeMind Lab (uses Ollama's model cache)
codemind-lab --config models.json pull --model qwen-coder-small

# Or use Ollama directly
ollama pull qwen2.5-coder:0.5b
```

Then:

```powershell
codemind-lab --config models.json models
codemind-lab --config models.json ask --model qwen-coder-small "Write a Python function that reverses a string."
```

## Combine small models

```powershell
codemind-lab --config models.json combine --models qwen-coder-small,qwen-coder-1.5b "Find a robust approach to parse a CSV file."
```

GAMA runs the ensemble members sequentially and then asks the aggregator to synthesize. This is not a neural-weight merge; it is inference-time collaboration. It may improve some tasks and hurt others, so benchmark it.

## Sequential coding pipeline

```powershell
codemind-lab --config models.json develop --planner qwen-coder-small --coder qwen-coder-1.5b --reviewer qwen-coder-small "Add CSV import support"
```

This produces a plan, implementation proposal and review. It does not edit files or execute generated code.

## Benchmark

```powershell
codemind-lab --config models.json bench --models qwen-coder-small,qwen-coder-1.5b --suite qadeep
```

The initial safe suite uses deterministic question-answer graders and does not execute generated Python. Other GAMA suites include code-generation cases that execute model-produced code in subprocesses; those are intentionally not enabled until we add a stronger OS-level sandbox.

## Current limitations

- This is a CLI research harness, not yet the combined trained/merged model.
- The initial backend supports Ollama native API and OpenAI-compatible endpoints such as LM Studio and llama.cpp.
- Streaming, cancellation, model download management, provider rotation and a graphical Model Center are future work.
- GAMA's advanced composition algorithms are available as the upstream dependency; the initial CLI exposes routing/ensemble foundations first.
- No CPU benchmarks have been run on the target laptop yet. Do not treat the sample RAM estimates as measured facts.
