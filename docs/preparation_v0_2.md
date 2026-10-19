# Preparation change record — 19 October 2026

This records the earlier data-preparation stage. The subsequent user-selected qwen3:8b acquisition and generic setup are documented in [the current model setup](qwen3_8b_setup.md); research execution remains disabled.

The attachment requests expansion and experiment preparation for the 20 October deadline, superseding the earlier prohibition on additional scenarios. It does not authorize the final comparison or presentation. No applicable AGENTS.md or Git repository was found in this workspace or its applicable ancestors.

## Preserved work

The original ZIP/extracted bytes remain under `data/raw/reflection_pilot_v0_1`. The revised ten-scenario/ten-question pilot remains unchanged under `data/pilot_v0_1`. Its eight applied revisions, including S02's three corrections, were checked against their application-audit hashes before copying. The existing Q01 provenance metadata edit remains intact. Original user review proposals, draft history, requests, application history and the empty completed-decision log remain byte-identical. The new dataset manifest records their source hashes for verification.

## Deliberate version changes

New working version: `data/exploratory_v0_2`, 60 scenarios, 60 separate evaluation notes, 30 questions and 90 pending requests. The existing completed-decision history remains shared and append-only; hash-bound acceptance never transfers automatically to changed records. No human decisions or criterion scores were invented.

All ten pilot cases are development in the new version, including the four previously called test. S11/S12 are related development variants of F01/F02. Validation and candidate-test families are disjoint from development. S21/S31, S22/S32, S41/S51 and S42/S52 are explicit within-split variants. There are 54 family labels (18 per split). Exactly 20 records and two per category occur in each split; these convenient counts are exploratory, not a sample-size justification. The authoring assistant has seen every case; candidate test is not frozen or independently unseen.

Fifty new scenarios were explicitly AI-authored with different activities, reported observations, progress conditions and wording, rather than only substituting topic names. Twenty additional candidate questions were authored, and Q04/Q05 applicability now explicitly limits clarification to the provisional pilot. Author/tool/date, unknown model settings, source hashes and limitations are in `manifest.json`. Serialization is deterministic; semantic realism, novelty and representativeness are unverified. No real student data or external dataset was used. Evaluation expectations describe acceptable behaviours and prohibited assumptions; illustrative wording remains optional and evaluation-only.

The old validator only knows development/test. Its source is preserved. A copy of expanded scenario metadata maps validation to test solely when reusing that original function; the extended validator independently checks all three real split values and cross-split family overlap first. This adapter is explicit in the validation report. Exact duplicate contexts/records remain errors. Wording similarity is flagged at token Jaccard >= 0.72 or normalized sequence ratio >= 0.88, with row positions and no text snippets; the heuristic misses semantic duplicates. Five pairs were flagged in this authored version, all within the correct family/split. Family F02 also remains grouped based on author judgment even though the lexical threshold did not flag its wording.

CLI commands now default to exploratory_v0_2. Use `--dataset pilot_v0_1` for the preserved pilot. Python library imports retain pilot defaults for backwards-compatible existing tests; CLI configuration selects the version explicitly. Expanded init verifies existing versioned files and refuses to silently rebuild missing data from the original pilot. Expanded reports/exports have separate version directories. Full review documents and compact queues are generated from JSONL, with assistant issue proposals separate from human decisions.

## Confirmed and unresolved

| Confirmed preparation requirement | Unresolved/provisional |
|---|---|
| English fictional ICT learning contexts; selection/generation only | Whether upstream systems supply all proposed context fields |
| Compare fixed bank, controlled retrieval generation and direct generation | Final base model and intended-use license assessment |
| Same model/settings for the two generative methods | `previous_question` interface availability; no previous answers assumed |
| Separate review/evaluation data and approved-only export | Product-team acceptance of clarification questions |
| No final comparison in this task | Final freeze, thresholds, reviewers and output-assessment procedure |
| Local runtime and cached model passed a generic READY-only smoke | Research-prompt memory use, quality, safety and latency are untested |

No training, student-answer processing, trait prediction, learning-plan generation or presentation was implemented. No research model outputs were produced. The inference probe is explicitly technical readiness evidence, not a result of any of the three experimental methods.
