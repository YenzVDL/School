# Zelfregiekompas — reflection-question research setup

Subtask 5, English, exploratory study: **60 synthetic scenarios and 30 bank questions**, accepted at their current hashes by **R01 on 2026-10-19**, with pass on all six data-review criteria. This is human review supported by AI-assisted proposals, **not an independent second review**. Only development inference is authorized. Validation and final-test inference remain untouched. Student-answer processing belongs to subtask 6 and is excluded.

The original pilot, eight applied revisions (including all three S02 changes), raw snapshot and review history are preserved. Earlier **12 accept / 8 revise human proposals** remain unchanged historical evidence. Effective approval comes from the append-only current-hash decision log; original draft `review_status` declarations remain unchanged. Exports contain **20 scenarios per split and 30 shared bank questions**. Approval does not authorize held-out inference or establish output quality. See [the preparation change record](docs/preparation_v0_2.md).

The separately supplied expanded assistant review contains 79 accept / 11 revise proposals, with no approval effect of its own. All source hashes matched before applying **11 revisions / 12 fields**. Sources, snapshots and the application log remain in `data/reviews/expanded_pilot_review_20261019/`; the later explicit R01 endorsement is separate in `data/reviews/r01_exploratory_v0_2_20261019/` and the decision log. See [the revision change record](docs/expanded_review_revisions.md).

## Setup and commands

Use an existing Python 3.10+ installation. The delivered environment uses Python 3.14.0. Runtime and tests have **no third-party dependencies**; `requirements.txt` documents this. Nothing installs or downloads packages automatically.

```powershell
# From this project directory, if recreating the environment:
python -m venv --without-pip .venv
# If Python is absent from PATH on this computer, use the installed interpreter:
# & "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" -m venv --without-pip .venv

.\.venv\Scripts\python.exe research.py init
.\.venv\Scripts\python.exe research.py validate
.\.venv\Scripts\python.exe research.py review-docs
.\.venv\Scripts\python.exe research.py export
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

CLI commands default to `exploratory_v0_2`; add `--dataset pilot_v0_1` to inspect the preserved pilot. Start review with **[the compact queue](reports/exploratory_v0_2/review_summary.md)**, then use the full `review.md` and `review_forms.jsonl` in that directory. No packages or weights need installation for data work.

On macOS/Linux use `python3` to create the environment and `.venv/bin/python` for subsequent commands. Activation and `pip install` are unnecessary. Commands resolve project paths relative to `research.py`.

For the expanded version, `init` verifies the versioned files and refuses to reconstruct missing records from pilot data. For the pilot it copies only missing working files. Neither mode resets existing data or reviews. Do not run raw `build_pilot.py` in working data: it resets reviews. Validation/review rendering never exports inputs.

## File roles

| Path | Role |
|---|---|
| `data/raw/reflection_pilot_v0_1/` | Unchanged original ZIP, byte-identical extracted package, version/hash manifest. Never edit or execute in place. |
| `data/raw/supplied_files/` | Unchanged separately supplied files, with a JSONL filename/hash mapping. Their upload filenames did not match their contents. |
| `data/exploratory_v0_2/` | Active 60-scenario/30-question canonical JSONL, separate evaluation notes, 90 pending requests and authoring/hash manifest. |
| `data/pilot_v0_1/scenarios.jsonl` | Canonical scenario inputs, synthetic declaration, category and provisional split. |
| `data/pilot_v0_1/question_bank.jsonl` | Canonical candidate questions, applicability conditions and original synthetic provenance. |
| `data/pilot_v0_1/evaluation_notes.jsonl` | Evaluation-only intent, assumptions to avoid, illustrative questions and challenge flags. Never model or retrieval data. |
| `data/reviews/requests.jsonl` | Original 20 pending review requests; keep blank. |
| `data/reviews/decisions.jsonl` | Canonical append-only completed decision history; initially empty. |
| `data/reviews/proposals.jsonl` | User-supplied review proposals, original reasons/conditions, date and reviewed hashes. No approval effect. |
| `data/reviews/revision_proposals.jsonl` | Before/proposed definitions for eight applied revisions, including the corrected S02; still awaiting human re-review. |
| `data/reviews/revision_applications.jsonl` | Application audit: changed fields and before/after target hashes, separate from human decisions. |
| `data/reviews/history/` | Earlier draft definitions and the user-edited review document preserved before application. |
| `reports/review.md` | Generated readable catalogue, evaluation notes, review rubric and decision history; local reviewer use only. |
| `reports/review_forms.jsonl` | Generated blank form per record; copy selected lines before editing. |
| `reports/validation_report.json` | Structural results, data quality flags, privacy screening, approval counts and SHA-256 hashes. |
| `reports/verification.json` | Original setup check summary: 17 passing tests; describes that delivery. |
| `reports/review_intake_verification.json` | Checks after recording proposal-only review evidence. |
| `reports/revision_application_verification.json` | Current revision checks, validation and existing-test results. |
| `reports/exploratory_v0_2/` | Current full/compact review documents, blank forms, separate assistant issue proposals, validation and verification reports. |
| `docs/experiment_plan.md`, `configs/experiment_v0_2.json` | Proposed methods, contracts, rules, settings, rubric and freeze requirements; not executed experiments. |
| `scripts/start_local_inference.ps1`, `scripts/probe_local_inference.py` | Explicit local readiness tools; never install/download models or run dataset comparisons. |
| `approaches.py`, `ollama_local.py` | Fixed-bank, filtered lexical RAG and direct-generation implementations with a shared pinned local generator; research execution disabled. |
| `scripts/setup_qwen3.py` | Explicitly authorized one-model acquisition, metadata checking and generic-only JSON smoke tests; never processes research records. |
| `docs/qwen3_8b_setup.md`, `reports/qwen3_8b_setup.json` | Selected-model rationale, actual artifact/runtime/hardware and unmodified generic smoke evidence. |
| `exports/<input-and-workflow fingerprint>/` | Derived approved model inputs, approved retrieval-bank candidates and hash manifest. No index is built. |
| `exports/latest.json` | Pointer created by the latest successful export; removed if export fails. |
| `docs/` | Schema, collection/review rules, inspection decisions and optional privacy workflow. |

JSONL is the source of truth. Regenerate Markdown after changes; do not edit generated Markdown as a dataset. Raw Markdown is retained solely as original evidence. Generated review forms, exports, the virtual environment and local reviewer drafts are ignored by Git; raw/canonical JSONL and review history are not ignored. This folder initially had no Git repository; the versioned snapshot is identified by its directory, manifest and pinned ZIP hash, ready for the team's private version control. No remote or upload was configured.

## Human review

1. Run validation and `review-docs`. Read `reports/exploratory_v0_2/review_summary.md` and the full `review.md` alongside it. Confirm the input contract with the team, especially `previous_question`.
2. Copy selected lines from `reports/exploratory_v0_2/review_forms.jsonl` into `local_reviews/completed.jsonl`. Keep `record_type`, `record_id` and `target_sha256` unchanged. Fill `reviewer_code` (2–24 uppercase letters/digits/underscores/hyphens), an explicit `YYYY-MM-DD` date, all six criteria (`pass` or `concern`), `decision` (`accept`, `revise`, `reject`) and a nonempty `reason`. Do not submit untouched pending lines. Use reviewer codes, not names; keep reasons free of identifying or sensitive details. Assistant issue proposals in the report directory are not review decisions.
3. Submit the explicit human decisions, then rebuild:

```powershell
.\.venv\Scripts\python.exe research.py record-reviews --file local_reviews/completed.jsonl
.\.venv\Scripts\python.exe research.py validate
.\.venv\Scripts\python.exe research.py review-docs
.\.venv\Scripts\python.exe research.py export
```

Acceptance requires `pass` for realism, clarity, relevance, unsupported assumptions, autonomy and sensitive information. R01 explicitly endorsed all six for the current 90 versions. See [the collection and review guide](docs/data_contract.md). Scripts check form completeness, not reviewer judgment. No record is automatically approved. No independent second review is claimed.

History is appended, never rewritten by commands. A later decision by the same reviewer supersedes their earlier decision in append order; every participating reviewer's latest decision must accept the current record hash. Changed scenario context **or evaluation notes** invalidate earlier scenario acceptance; changed question data invalidates question acceptance. Re-review changed records rather than editing an old decision. Keep one writer at a time; this is a local file workflow without authentication or concurrent-write locking.

## Safe exports and validation

`export` validates again, blocks structural errors and contact-pattern findings, and includes only accepted current records. **The current export contains 60 scenarios and 30 questions; earlier pending-stage exports were empty.** `model_inputs.jsonl` contains only `scenario_id` and an explicit allowlist of context fields; pass only `context` to a method. `retrieval_bank.jsonl` contains only approved question IDs, text, focus and use/avoid conditions. Evaluation notes, illustrative wording, provenance metadata, splits and review decisions are excluded. Unknown schema fields block export rather than being silently forwarded.

Always regenerate exports after changes and resolve `exports/exploratory_v0_2/latest.json` (the pilot uses `exports/latest.json`). Old bundles are historical artifacts, not current authorization. Manifests include canonical input hashes, workflow hash and output hashes. Never index review data/documents, raw exports or evaluation notes. No directory-wide retrieval ingestion is provided.

The validator reuses the supplied `check()` after stricter schema checks. It checks required/unknown fields, types (including bool-versus-integer), nonnegative values, allowed values, IDs, exact duplicate records/contexts, normalized duplicate question text, cross-file links and family overlap between splits. It preserves `null`, zero, conflicting completion data and the fictional injection note. Missing values and contradictions are reported as review flags; they are not imputed or corrected. Structural success, narrow regex privacy screening and human acceptance are separate report sections.

Reports use fixed issue codes and row positions, not matched text or untrusted IDs. **Presidio has not run**. The optional offline procedure is in [privacy.md](docs/privacy.md). No check proves anonymity, realism, educational value, fairness or legal compliance. Review documents contain full authored content and need local access control.

The active dataset has **20 development / 20 validation / 20 candidate test**, with **two records per category in each split**, and 54 family labels kept within splits. All ten original pilot cases are development in this version because they informed revisions. The earlier 6/4 allocation remains only in the preserved pilot. The small purposeful sample is **not a validated benchmark**; the authoring assistant has seen all records and test is not frozen. Five near-duplicate wording pairs are flagged for review, all within their family/split. Automated checks miss semantic duplicates and cannot establish realism or representativeness.

The user selected **qwen3:8b**, acquired through unchanged bundled Ollama **0.11.4**. Actual digest, hardware and shared settings are pinned in the config. Generic setup used zero research records; the later development run is separate. See [qwen3_8b_setup.md](docs/qwen3_8b_setup.md) for rationale and limits, and [the development workflow](docs/development_run.md) for outputs. The repository default remains `experiments_enabled=false`; only the explicitly invoked development runner enables execution in its saved run-specific configuration. Model selection and format success do not prove reflection quality or a winning approach.

The original development outputs now have a separately preserved **AI01 assessment**; it is not an independent human review or a change to R01 data acceptance. All 140 identities/texts were verified before joining the method mapping. The [original comparison](data/assessments/development_original_AI01_20261019/comparison.md) averages seeds within each scenario first and reports assumption/safety flags separately. A single shared prompt append is versioned in `configs/experiment_v0_2_prompt_0_4.json`; see [the exact change and development-only protocol](docs/development_prompt_revision.md). The original run/config remain untouched; new outputs use P-series review IDs and remain unscored.

Safe setup check (no generation or download):

```powershell
.\.venv\Scripts\python.exe scripts/setup_qwen3.py --check
.\.venv\Scripts\python.exe approaches.py
```
