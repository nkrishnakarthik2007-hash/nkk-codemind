# CPU-first Model Lab

Target: CPU-only Windows PCs. Initial hardware target is Intel Core i7-1185G7 with 16 GB RAM and no discrete GPU; preserve an 8 GB RAM design target.

## Combining models
1. Routing: select the best measured specialist per task. Build this first.
2. Sequential collaboration: one model drafts and another reviews only when useful.
3. Weight merging/distillation: experimental; requires compatible architecture, tensor shapes, tokenizer, data and evaluation. Merging unrelated models is not a shortcut and can reduce quality.

On CPU, load one model at a time by default. Concurrent 3B/4B models can exhaust RAM and reduce speed.

## Candidate pool
| Candidate | Initial role |
|---|---|
| Qwen3.5 0.8B / 2B | quick classification and extraction |
| Qwen3.5 4B | general and multilingual baseline |
| Qwen2.5-Coder 3B | code generation and repair |
| Phi-4-mini | compact reasoning and structured output |
| Gemma 4 E2B | compact instruction / multimodal experiment |

These are candidates, not winners. Verify exact tags, quantized sizes, revisions and licences before redistribution. Gemma has its own terms; do not call every open-weight model OSI open source.

## Runtime plan
- Ollama first: existing adapter and easy local model lifecycle.
- llama.cpp next: GGUF quantization and CPU tuning.
- OpenVINO: test Intel CPU acceleration on identical prompts.
- BitNet.cpp: research only supported architectures/checkpoints.

## Evaluation
Use identical explanation, coding, debugging and JSON tasks. Record model, runtime, CPU, context, latency, tokens/sec and raw output. Later add peak RSS, quantization and tool-call reliability. Score correctness by running tests, not by speed or parameter count. The initial harness measures performance and saves outputs; it does not automatically judge code quality.

## References
- https://huggingface.co/Qwen/Qwen3.5-4B
- https://ollama.com/library/qwen3.5
- https://ollama.com/library/qwen2.5-coder
- https://ollama.com/library/phi4-mini
- https://ollama.com/library/gemma4
- https://github.com/ggml-org/llama.cpp/blob/master/docs/models.md
- https://docs.openvino.ai/2026/about-openvino/performance-benchmarks/generative-ai-performance.html

Automatic task routing, extra runtime adapters, agent collaboration, model merging and a verified winner remain future work.
