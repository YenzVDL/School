# Local inference route inspection

Historical inspection, 19 October 2026, before base-model selection. At that stage no model weights or packages were downloaded, no paid API was used, and no research record was sent to a model. The user subsequently selected and authorized downloading **qwen3:8b**. See [the current model setup](qwen3_8b_setup.md) for the acquired artifact, native thinking control and generic JSON probes. The unrelated cached vision model is not selected. Ollama 0.11.4 remains unchanged.

## Observed environment

- Python 3.14.0, isolated standard-library-only `.venv`; no torch, transformers, llama_cpp, ollama Python client, openai client, requests or sentence_transformers installed in this environment.
- AMD Ryzen 5 3600X, 6 cores / 12 logical processors; 17,121,849,344 bytes installed RAM (about 15.95 GiB).
- NVIDIA GeForce RTX 2070 SUPER. WMI's truncated adapter-memory value was not trusted; actual `nvidia-smi` reports **8192 MiB VRAM**, driver 617.42.
- AnythingLLM Desktop is installed. Its existing bundled executable is `%LOCALAPPDATA%\Programs\AnythingLLM\resources\ollama\llm.exe`, Ollama version **0.11.4**.
- The existing model store is `%APPDATA%\anythingllm-desktop\storage\models\ollama`. Its cached tag is **llama3.2-vision:11b**, GGUF **Q4_K_M**, runtime-reported parameter size **10.7B**, total model metadata/weight size 7,816,589,186 bytes.
- Resolved tag digest during the probe: `6f2f9757ae97e8a3f8ea33d6adb2b11d93d9a35bef277cd2c0b1b5af8e8d0b1e`. Mutable tag names alone are not a reproducibility pin.
- Known provider variables were checked in process/user/machine scopes using presence only; none were detected. The existing AnythingLLM settings identify its local Ollama provider and native embedding engine. No nonempty API-key/token/secret setting was found in that inspected settings file. Credential values were neither printed nor copied. This is not an exhaustive credential audit of the computer.

## Actual readiness check

Started a separate hidden server at **127.0.0.1:11435** using the existing store; the AnythingLLM settings and default ports were not changed. The metadata endpoint returned the cached model. An explicit setup-only prompt asking for `READY` completed and returned exactly that word. Client wall time was **17.606 seconds** including possible loading. This is one setup observation, not a latency benchmark, safety test or reflection-question result. `reports/inference_probe.json` contains the actual result. `keep_alive: 0` requested unloading after the probe. The local server was left listening; it uses no dataset unless a later caller sends one.

To inspect it again without inference:

```powershell
.\.venv\Scripts\python.exe scripts/setup_qwen3.py --check
```

The current checker is hard-bound to IPv4 loopback and disables proxy routing. `--check` verifies Qwen3 metadata and configuration without download or generation. Research execution remains disabled.

If the local server has stopped:

```powershell
# Starts hidden; refuses an occupied port or missing existing files. No download.
.\scripts\start_local_inference.ps1
.\.venv\Scripts\python.exe scripts/setup_qwen3.py --check
```

The start script prints its PID and the exact `Stop-Process -Id ...` command. Stop only the server PID you started; do not stop another app's runtime blindly. Existing setup PID at this inspection was 21668; verify process identity before using a historical PID.

## Model decision completed subsequently

The user selected qwen3:8b and explicitly authorized its download. The original runtime was retained, with the same executable hash before and after setup. The selected Q4_K_M artifact is pinned by full digest in `configs/experiment_v0_2.json`; RAG and direct generation share that artifact and all generation settings. The fixed-bank method is independent of the LLM. This is base-model selection, not an approach ranking.

The cached model includes local license/AUP layers titled *Llama 3.2 Community License Agreement* and *Llama 3.2 Acceptable Use Policy*. Their digests are `sha256:fcc5a6bec9daf9b561a68827b67ab6088e1dba9d1fa2a50d7bbcc8384e0a265d` and `sha256:d3ed60b917572dd5aa69bf5ff7825f2db00d65e73dc07a43fbc31c60eb31449e`. Their applicability to the intended institution/use has not been established. Technical availability and a setup response are not license clearance. The multimodal capability is unnecessary for this text-only task; no images are used. Memory/latency under the planned research prompts is untested.

Earlier alternatives are retained in [the historical shortlist](base_model_shortlist.md). They do not override the user's selected model. Acquisition evidence is in `reports/qwen3_8b_acquisition.json`; raw generic setup responses are in `reports/qwen3_8b_setup.json`. No research record was used.

Before research execution, complete the independent dataset/bank human review and freeze the protocol. Do not bypass pending approvals. The generic setup establishes technical readiness only; reflection quality and approach performance remain unmeasured.
