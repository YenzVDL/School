# Selected base model: qwen3:8b

Historical setup evidence below precedes the later explicit R01 acceptance of all 90 current records and development-only inference authorization. See [development_run.md](development_run.md) for that subsequent stage; setup-probe latencies are not development results. The repository default remains disabled, with execution enabled only in an explicitly invoked development run's saved configuration.

**Selected by the user on 19 October 2026.** This supersedes the earlier 4B recommendation. The unrelated cached vision model is not selected. This is a justified base-model choice for a later approach comparison, not evidence that Qwen3 beats another model or that either generative approach beats the fixed baseline.

## Rationale and official sources

Qwen3-8B is a text model with instruction-following capabilities and a supported non-thinking mode, making it a plausible generator for short English questions with a constrained output contract. The [official Qwen card](https://huggingface.co/Qwen/Qwen3-8B) describes both mode controls and suggests non-thinking sampling settings: temperature 0.7, top_p 0.8, top_k 20, min_p 0. The [official Ollama artifact record](https://ollama.com/library/qwen3:8b) identifies the quantized package and Apache 2.0 licence. Neither source evaluates this project's reflection questions; their general capabilities do not establish pedagogical suitability or safety.

The local quantized package avoids full-precision weight storage. Its actual size and successful generic setup calls make it technically plausible on this machine, but peak GPU memory, longer-prompt latency and reflection quality remain unmeasured. No performance superiority, fairness, learning benefit or compliance finding is claimed.

## Actual installed configuration

| Item | Observed value |
|---|---|
| Tag | `qwen3:8b` |
| Actual resolved digest | `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` |
| Quantization / parameters | Q4_K_M / runtime reports 8.2B |
| Model storage | 5,225,388,164 bytes |
| Runtime | AnythingLLM-bundled Ollama **0.11.4**, unchanged |
| Bundled executable SHA-256 before and after | `31f53cfb4f211072952037d225ac5d52eba43e4cf578a4a5b986f6b421e96664` |
| GPU | NVIDIA GeForce RTX 2070 SUPER, 8,192 MiB VRAM; driver 617.42 |
| CPU / RAM | Ryzen 5 3600X, 6 cores / 12 logical processors; 17,121,849,344 bytes RAM |
| Request endpoint | `http://127.0.0.1:11435/api/chat` only; no proxy routing |

The user explicitly authorized downloading this one model. It was absent, then successfully pulled through the existing local server. No installation, replacement or upgrade of the bundled runtime occurred. The unrelated cached model was not removed. Acquisition evidence is in `reports/qwen3_8b_acquisition.json`; setup evidence, full generic requests and unmodified responses are in `reports/qwen3_8b_setup.json`. The experiment configuration also records template and licence hashes, hardware, runtime and the shared artifact pin.

## Thinking is disabled at the API boundary

Ollama's [0.9.0 release notes](https://github.com/ollama/ollama/releases/tag/v0.9.0) document the thinking API, including Qwen3. Installed 0.11.4 is newer; actual loading and generation also succeeded. There is **no observed compatibility blocker** and no silent upgrade.

Both future generative approaches send **top-level `"think": false`**, not a hidden-reasoning display option or an `options` field. The [Ollama thinking documentation](https://docs.ollama.com/capabilities/thinking) describes this native request control. The backend rejects nonempty thinking fields or thinking markup instead of removing them. Full raw generic responses are retained. It verifies runtime version and model digest before a call and the digest afterward.

Two generic probes requested exactly `{"question_text":"Is setup ready?"}` using the same shared sampler/context/output budget configured for future RAG and direct generation. The second input also contained `/think` to check the native false switch against that prompt hint. Both raw responses were valid expected JSON, had no nonempty thinking field and no thinking markup, and required no content stripping. Observed client wall times were **2.722 s** and **2.562 s**. Loading/unloading and cache state can affect these observations; they are not approach latency measurements or reflection-quality results. Zero research records, including all pending and test records, were used.

JSON output is requested through the [supported structured-output schema mechanism](https://docs.ollama.com/capabilities/structured-outputs), then validated separately. Format success does not prove good content.

## One base model, three separate approaches

`configs/experiment_v0_2.json` contains a single model tag/digest and one generation-settings object. RAG and direct requests use that same artifact and these settings: think=false, temperature=0.7, top_p=0.8, top_k=20, min_p=0, num_ctx=2048, num_predict=128, one request at a time, 180-second client timeout, no automatic retry. The configured seeds are 20261019–20261021. Only the retrieval reference block differs. The fixed-bank method never calls the generator.

`approaches.py` implements selection rules, eligibility-filtered lexical retrieval, direct/RAG prompt preparation, output validation and approved-bank fallback. `ollama_local.py` implements the explicit loopback transport; unit tests use fake clients and literal doubles, not language models. Lexical rules miss semantic cues, exact repetition checks miss paraphrases, and automatic output checks do not establish English quality or non-coerciveness. Exact selected-model tokenization/preflight for arbitrary long future prompts remains a runner integration concern; this setup does not claim arbitrary-prompt capacity validation.

**Research execution remains disabled:** `experiments_enabled=false`, all 90 records remain pending, and approved exports are empty. Configuring a backend is not permission to run the dataset. Model selection is complete; approach selection requires reviewed data, a frozen protocol and a separately authorized comparison.

## Safe next commands

Verify the cached artifact/configuration without downloading or generating:

```powershell
.\.venv\Scripts\python.exe scripts/setup_qwen3.py --check
.\.venv\Scripts\python.exe approaches.py
```

Then prepare the human review queue:

```powershell
.\.venv\Scripts\python.exe research.py review-docs
```

Complete selected review forms and submit them through `record-reviews`; do not turn on experiments just to bypass pending records. `setup_qwen3.py --smoke` explicitly repeats only the two generic setup prompts; it is not the next research command. No final comparison or presentation has been produced.
