# Base-model shortlist — 19 October 2026

Historical recommendation: superseded by the user's subsequent selection of **qwen3:8b**. See [the selected-model rationale and actual setup](qwen3_8b_setup.md). The shortlist below records the earlier investigation; its unselected/no-download status described that earlier stage, not the current configuration.

**Recommendation for later acquisition/evaluation: Qwen3-4B-Instruct-2507, Q4_K_M. No model is selected, downloaded or tested in this step.** Base-model selection chooses the shared generator; approach selection later compares fixed bank, retrieval generation and direct generation using one selected generator artifact. A cached model is not a suitability argument.

Observed hardware is the existing RTX 2070 SUPER, **8,192 MiB VRAM**, Ryzen 5 3600X and approximately 16 GiB system RAM. The existing runtime is AnythingLLM's bundled Ollama **0.11.4**. The three shortlisted tags were absent from the inspected model store; the unrelated cached model was `llama3.2-vision:11b`. No runtime/model request was made for this shortlist.

## Documented facts from primary sources

| Base model | Instruction-following evidence in its author's card | Published local artifact, storage and licence | Availability here |
|---|---|---|---|
| **Qwen3-4B-Instruct-2507** | 4.0B parameters; updated instruction-tuned, non-thinking model. The author describes improved instruction following and open-ended text generation; it explicitly omits thinking blocks. These are general claims, not reflection-task evidence. [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) | `qwen3:4b-instruct-2507-q4_K_M`: **2.5 GB**, Q4_K_M, Apache 2.0. Published short artifact ID `0edcdef34593`; resolve the full actual digest after any authorized acquisition. [Ollama artifact](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M) | Not cached; requires an explicit weight download. Runtime compatibility with this exact artifact is untested. Do not substitute generic `qwen3:4b`, which identifies a different variant. |
| **Qwen2.5-7B-Instruct** | 7.61B parameters. The author highlights instruction adherence, structured/JSON output and resilience to varied system prompts. Those capabilities are relevant to the output contract but do not establish pedagogical quality. [Qwen model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) | `qwen2.5:7b-instruct-q4_K_M`: **4.7 GB**, Q4_K_M, Apache 2.0; published short ID `845dbda0ea48`. [Ollama artifact](https://ollama.com/library/qwen2.5:7b-instruct-q4_K_M) | Not cached; requires a larger download. Exact template, JSON adherence and hardware behaviour here are untested. |
| **Phi-4-mini-instruct** | 3.8B parameters; supervised instruction tuning and preference optimization. Microsoft identifies memory/compute-constrained use and warns that downstream suitability must be evaluated. Its Transformers instructions note Flash Attention hardware constraints and an eager-attention alternative; this is not a guarantee for GGUF execution. [Microsoft model card](https://huggingface.co/microsoft/Phi-4-mini-instruct) | `phi4-mini:3.8b-q4_K_M`: **2.5 GB**, Q4_K_M, MIT; published short ID `78fad5d182a7`. Ollama lists minimum version 0.5.13, below the inspected 0.11.4. [Ollama artifact](https://ollama.com/library/phi4-mini:3.8b-q4_K_M) | Not cached; requires an explicit download. Passing a documented runtime-version minimum is not a measured compatibility or quality result. |

Sizes are rounded **artifact disk/download sizes**, not peak RAM/VRAM requirements. They refer to these quantized tags, not full-precision repositories. Keep extra disk space for metadata, temporary download overhead and any retained artifacts; downloading all three would add approximately 9.7 GB of weights rather than only the recommended 2.5 GB. The unrelated 7.8 GB cache would remain unless the user separately requests removal. No automatic downloads, installations or cache deletion are supplied.

Published licence labels are documented facts, not a compliance finding. Retain the actual downloaded licence/attribution files and review intended use. Tags can change; record full digest, quantization, template and runtime after acquisition. Author benchmarks use different protocols, hardware and sometimes precision; they do not rank these quantized candidates for English reflection questions.

## Hardware and task hypotheses requiring measurement

| Candidate | Planning assumption, not a measured requirement | Required later checks |
|---|---|---|
| Qwen3 4B Q4_K_M | A 2.5 GB artifact should leave useful room on an 8 GB GPU for short prompts and cache. Non-thinking output is a good design fit for a short question. | Exact Ollama 0.11.4 compatibility; peak GPU/system memory at 2,048 context; short JSON output, refusal/overproduction, latency and question quality. |
| Qwen2.5 7B Q4_K_M | The larger 4.7 GB artifact leaves less nominal GPU headroom; extra parameters might help wording but might not. | Same checks, including any CPU offload. Neither better quality nor slower runtime is established here. |
| Phi-4 mini Q4_K_M | Small weights and instruction tuning make it a plausible low-resource alternative. Its reasoning-focused training may or may not transfer to neutral reflective language. | Same checks; investigate template/attention backend behaviour on the Turing GPU, without assuming Transformers recommendations describe Ollama's backend. |

Start with context length 2,048 and one request at a time as the experiment specification proposes, not each model's advertised maximum context. KV cache, buffers, runtime kernels, other applications and quantization change actual memory. A successful unrelated one-word prompt does not measure any shortlisted model or this task.

## Recommendation and decision boundary

Qwen3's explicit non-thinking variant, modest published artifact size, permissive published licence and instruction-tuning focus make it the best **first candidate to evaluate** on this hardware. This is an engineering recommendation, not a measured winner. Phi is a similarly small alternative; Qwen2.5 offers a larger instruction-tuned comparison at a higher storage budget. Do not run a three-model contest on final-test notes to choose the generator.

No acquisition is authorized by the recommendation. The next user decision would be whether to acquire the **approximately 2.5 GB** Qwen3 artifact; after explicit authorization, resolve its real digest and check compatibility on development-only setup material under a separately agreed protocol. Leave `model.selected` and `model.artifact_digest` null until selection is explicit; `experiments_enabled` remains false now. Use the same resolved model, template and generation settings for retrieval-augmented and direct approaches. Fixed-bank selection has no base model.

## Why the cached vision model is not shortlisted

The user confirms `llama3.2-vision:11b` was downloaded for unrelated work. It offers no demonstrated benefit for this text-only task, occupies about 7.8 GB of weight storage, has more complicated unassessed reuse terms, and has no reflection-question evaluation here. The historical READY probe establishes only that those cached weights could execute once. It neither selects that model nor proves instruction adherence, educational suitability or latency for this study. Keep its historical report unchanged; remove it from active generator defaults.
