# R01 review and development-only execution

This records the first development protocol. The original run remains at `runs/development_20261019T183222Z_0bed5093/`. Its later supplied AI01 ratings and scenario-balanced comparison are separate from R01 data approval. A new explicitly versioned prompt append and P-series review are documented in [development_prompt_revision.md](development_prompt_revision.md); the latest-run pointer may refer to that later run. No validation/test inference is authorized by either stage.

The user explicitly accepted all 90 current records under the documented exploratory pilot conditions, with reviewer code **R01**, date **2026-10-19**, and pass for all six data-review criteria. This is **human review supported by AI-assisted proposals**, not an independent second review. It does not score or approve model outputs. The former proposals, applied-revision history, original raw files and canonical synthetic declarations remain intact.

Completed forms and the original decision-log snapshot are in `data/reviews/r01_exploratory_v0_2_20261019/`. Submission used `research.py record-reviews` and appended 90 UUID-bearing decisions. Effective acceptance is derived from current record hashes; the canonical draft `review_status` fields are not rewritten. The shared decision log can retain decisions from another version without applying them to a different hash.

| Type / split | Approved | Exported |
|---|---:|---:|
| Development scenarios | 20 | 20 |
| Validation scenarios | 20 | 20 |
| Candidate-test scenarios | 20 | 20 |
| Shared bank questions (no split) | 30 | 30 |

`reports/exploratory_v0_2/human_review_r01_verification.json` records current-hash checks and the export bundle. Exporting approved held-out context is not permission to run it. The development runner restricts its known IDs and contexts to the development split before creating the engine. Evaluation notes are joined only while rendering human review documents, never during generation/retrieval. Scenario category, split, family and review metadata are excluded from prompts.

## Run protocol

The explicit command is:

```powershell
.\.venv\Scripts\python.exe scripts/run_development.py --run-development
```

This command creates a new timestamped `runs/development_*` directory and would perform a **new run** each time. Do not repeat it just to view saved outputs. The repository configuration remains disabled by default. Its run-specific copy enables execution under the user's development-only authorization; no sampler, prompt, selection rule or retrieval setting is changed based on outputs.

There are 20 fixed selections (once per scenario), 60 RAG attempts and 60 direct attempts (three configured seeds each). The generative schedule is shuffled with the configured seed. Both methods use the identical qwen3:8b digest, Q4_K_M quantization, native API think:false, JSON schema, sampling options, context/output budget, timeout and no-retry policy. The fixed baseline never calls the model. No additional generic warm-ups are performed. `keep_alive=0` requests unloading per call; measured latency includes loading and is not a warm-throughput benchmark. Seeded output need not be reproducible across hardware/runtime changes.

The runner verifies runtime version, executable, artifact and template hashes. A conservative ASCII-only Qwen2 byte-BPE token-budget preflight uses merge metadata from the already installed model, with 64 tokens reserved for the pinned two-message chat template. It refuses unsupported/non-ASCII input and oversize requests rather than truncating. This narrow implementation follows the [Qwen2 pretokenization definition](https://github.com/ggml-org/llama.cpp/blob/master/src/llama-vocab.cpp); it is not a general tokenizer for future multilingual datasets. Runtime prompt counts are saved for checking the preflight against observations. No tokenizer/model package is downloaded.

## Saved artifacts

| File | Role |
|---|---|
| `manifest.json` | Scope, approved source hashes, development IDs, model-loading policy, code hashes, preflight bounds, timing and artifact hashes. |
| `repository_config.json`, `effective_config.json` | Exact default and run-specific configuration snapshots. |
| `prepared_requests.jsonl` | Prompt strings/options and local budget checks; no evaluation material. |
| `requests.jsonl`, `api_events.jsonl` | Exact structured API requests, request-byte hashes, unmodified responses, runtime duration/token metrics and client latency. |
| `results.jsonl`, `failures.jsonl` | Raw text, delivered question, format/failure codes, fallback information and timings; failures remain in denominators. |
| `summary.json` | Observed completion/failure counts and latency summaries, without quality scores. |
| `output_review.md`, `review_mapping.jsonl` | Shuffled delivered-question review and separate method/seed/status mapping. Repeated wording may compromise blinding. |
| `output_review_with_raw.md` | Supplementary blind review including raw and delivered wording separately; generated by the verification command below. |

`reports/exploratory_v0_2/development_run_latest.json` points to the saved run. Inspect outputs locally; do not upload them or index review documents. Human review must assess relevance, clarity, usefulness, autonomy, unsupported assumptions, repetition, missing/conflicting input and safety. Neither data approval nor valid JSON establishes output quality. No scores, winner, learning effect, independent agreement or compliance finding is invented. Validation/final-test inference remains unauthorized and untouched; the authored test set is still unfrozen and not independently unseen.

Verify an existing run and regenerate the raw/delivered review supplement, **without inference**:

```powershell
.\.venv\Scripts\python.exe scripts/verify_development.py
```
