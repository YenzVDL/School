# Initial inspection and implementation decisions

Inspected 19 October 2026. The requested workspace was initially empty and not a Git repository. No `AGENTS.md` was present in the workspace, archive or applicable ancestor directories. No repository conventions were available to override. A related local research proposal and English collection plan were read for scope; they remain proposals, not evidence of completed data collection or evaluation.

`Reflection_Question_Pilot_v0_1.zip` was found locally in Downloads. Its exact bytes and all ten extracted files are preserved under `data/raw/reflection_pilot_v0_1/`. The ZIP SHA-256 is pinned in `research.py` and recorded in the snapshot manifest. A later set of nine files supplied in the workspace matched ZIP entries byte-for-byte, but their names were shifted (for example, the uploaded `validate (1).py` is actually `scenarios.jsonl`). They were moved unchanged into `data/raw/supplied_files/`; its `mapping.jsonl` records each supplied name, hash and matching original filename. The archive resolves the naming ambiguity without guessing at data content.

Material conflicts were explained before implementing the replacement workflow:

- The original `build_pilot.py` resets reviews. It is preserved but never used to rebuild the working dataset. `init` copies only missing files; completed decisions live in a separate append-only JSONL file.
- The original validator writes a model-input export even on structural failure and has no acceptance gate. Its `check()` is reused after stricter validation, but its `main()` is never run against raw or working files. Tests execute the unchanged main script only in a disposable copy.
- The uploaded filenames do not describe their contents. Raw bytes are preserved; correctly named ZIP files supply canonical records.
- The earlier research proposal suggests eventual development/validation/test splits. The actual pilot supplies only six development and four test cases. This setup preserves that provisional allocation, checks family overlap and does not invent a validation set or expand the pilot.
- The broader collection plan mentions optional CSV reflection data and future external datasets. This task explicitly requires JSONL, synthetic provenance and no external processing, so no CSV source or external dataset is introduced.

The implementation uses only the standard library. The local Python 3.14.0 installation was used to create `.venv` with `--without-pip`; no interpreter, dependency, NLP model or model weights were downloaded. No external requests, dataset uploads, inference, training or answer processing are part of the workflow.
