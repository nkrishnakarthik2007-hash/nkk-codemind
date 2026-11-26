# Model and Runtime Research

This file is an evaluation plan, not a declaration that any candidate is the best.

## Runtime candidates

| Runtime | Why investigate | Notes |
|---|---|---|
| llama.cpp | Mature CPU inference, GGUF quantization, broad model support | Baseline candidate |
| BitNet.cpp | Specialized low-bit CPU inference | Test supported models and real coding quality |
| Ollama | Convenient local model lifecycle and API | Useful development option; measure overhead |
| ONNX Runtime GenAI | Deployment/runtime option for supported models | Check model and CPU support |
| Transformers + CPU | Broad Hugging Face compatibility | May have higher memory/runtime overhead |

## Model candidates

Candidate availability, licence, model card, tokenizer, context length and quantization must be rechecked at evaluation time.

| Candidate family | Candidate size | Evaluation purpose |
|---|---:|---|
| Qwen2.5-Coder Instruct | 1.5B | Primary small coding baseline |
| Qwen2.5-Coder Instruct | 0.5B / 3B | Smaller/larger comparisons where available |
| StarCoder2 | 3B | Code generation/completion comparison |
| SmolLM2 / other compact instruct models | 1.7B class | Planning and lightweight instruction following |
| Microsoft BitNet family | supported small variants | CPU efficiency research |
| Hosted models | provider-dependent | Escalation baseline |

Do not assume all models are OSI open source. Use the more precise term **open-weight** where model weights are available under a licence that may impose conditions. Verify each licence before redistribution or commercial use.

## Benchmark protocol

For each model/runtime/quantization combination record:

- Exact model ID and revision
- Licence and model-card URL
- Quantization format and file size
- CPU model, core count and RAM
- Operating system and runtime version
- Peak resident memory (RSS)
- Prompt processing time
- Generation tokens/second
- Time to first token
- Task success rate
- Tool-call reliability
- Failure examples

## Task set

1. Explain a short function.
2. Write a small function with tests.
3. Fix a seeded bug.
4. Modify two related files.
5. Follow a provided API reference.
6. Diagnose a failing test from its output.
7. Respect an existing project convention.

Evaluate actual tests, not only subjective response quality.

## Model collaboration experiment

Compare:
- One model doing the complete task
- One small planner + one coder sequentially
- One coder + independent reviewer sequentially
- Local small model with cloud escalation

Measure total latency, total tokens, provider cost/quota use, RAM peak and task success. Multiple agents can increase token use and latency; collaboration is not automatically better.

## Model merging experiment

Only investigate after strong individual baselines exist. Check architecture, tensor shape, tokenizer and licence compatibility. Evaluate merged checkpoints against each original model on the same task set. Keep the experiment optional and never require merging for normal operation.