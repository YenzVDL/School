# Original development comparison

Supplied AI01 assessments; not independent human ratings.
Average seed trials within each method/scenario, then average 20 scenario means per method.
Scores use 0–2. Each approach has n=20 scenarios; 60 seed outputs are not 60 independent scenarios.
No pooled overall score, inferential significance, model superiority or pedagogical validation is claimed.
Unsupported assumptions and observed serious safety failures remain separate from criterion means.

| Approach | Scenarios | Outputs | Specificity | Usefulness | Clarity | Non-coerciveness |
|---|---:|---:|---:|---:|---:|---:|
| fixed | 20 | 20 | 1.000 | 1.700 | 2.000 | 2.000 |
| rag | 20 | 60 | 1.000 | 1.350 | 2.000 | 2.000 |
| direct | 20 | 60 | 1.950 | 0.500 | 1.817 | 1.950 |

## Separate assumption and safety findings

| Approach | Unsupported: outputs / scenarios | Serious safety: outputs / scenarios | Usefulness-zero outputs |
|---|---:|---:|---:|
| fixed | 0 / 0 | 0 / 0 | 1 |
| rag | 0 / 0 | 0 / 0 | 3 |
| direct | 5 / 3 | 0 / 0 | 38 |

Zero observed serious safety failures in these supplied AI ratings is not proof of safety.

## Issue counts

Each cell is flagged outputs / affected scenarios. Tags overlap; counts must not be summed as distinct failures.
Scenario-balanced issue rates are retained in comparison.json.

| Issue | Fixed | RAG | Direct |
|---|---:|---:|---:|
| already_known_fact | 0 / 0 | 0 / 0 | 11 / 4 |
| already_supplied_count | 0 / 0 | 0 / 0 | 3 / 1 |
| already_supplied_progress | 0 / 0 | 0 / 0 | 3 / 1 |
| assumes_unreported_activity | 0 / 0 | 0 / 0 | 4 / 2 |
| factual_recall_question | 0 / 0 | 0 / 0 | 3 / 1 |
| generic | 4 / 4 | 33 / 11 | 0 / 0 |
| invented_context_detail | 0 / 0 | 0 / 0 | 1 / 1 |
| knowledge_or_next_task_question | 0 / 0 | 0 / 0 | 3 / 1 |
| knowledge_question | 0 / 0 | 0 / 0 | 9 / 4 |
| limited_clarification | 0 / 0 | 0 / 0 | 3 / 1 |
| limited_reflection | 0 / 0 | 0 / 0 | 11 / 5 |
| metadata_question | 0 / 0 | 0 / 0 | 1 / 1 |
| misses_completed_work | 0 / 0 | 0 / 0 | 3 / 1 |
| misses_missing_progress | 0 / 0 | 0 / 0 | 2 / 1 |
| misses_rescheduling | 0 / 0 | 0 / 0 | 6 / 2 |
| plan_detail_question | 0 / 0 | 0 / 0 | 3 / 1 |
| semantic_repetition | 1 / 1 | 3 / 1 | 0 / 0 |
| third_person | 0 / 0 | 0 / 0 | 10 / 4 |
| unnecessary_justification | 0 / 0 | 0 / 0 | 3 / 1 |
| verification_instead_of_reflection | 0 / 0 | 0 / 0 | 1 / 1 |

The original ratings and source documents were locked before this mapping join.
The source declares blinded assessment; wording could reveal approaches. Reviewer AI01 is an AI assessor, not a second human.
Only development findings can inform the separately versioned shared prompt revision. Revised outputs need new assessment.
