# Fixed metrics v3

V3 introduces a new rubric, not a correction to the saved v2 results. Re-evaluation uses existing outputs only. It does not regenerate questions, alter snapshots, tune generation settings or call an AI evaluator.

## Measurements

1. **Format:** separate nonempty, question-mark count, ending, 40-word budget, single-line, recognizable extra-response and normalized previous-question checks. Language identification remains inconclusive. Punctuation alone does not prove exactly one semantic question.
2. **Question structure:** conservative learner-directed strategy/decision/evidence/planning patterns, recognizable knowledge/recall patterns, or ambiguous structure. A structural match does not establish genuine reflection or pedagogical usefulness.
3. **Contextual grounding:** explicit references to available fields and named technologies. Lexical overlap is separately descriptive; absent overlap never proves irrelevance.
4. **Factual grounding:** recognized time/quantity/progress/control-answer/performance premises. Times normalize to seconds. Unknown units are not invented. Conflicting notes and structured records remain unresolved. Hypothetical alternatives do not become observed facts.
5. **Agency signals:** listed direct coercion, judgments, emotional premises and diagnoses. Absence of a recognized pattern does not establish appropriate tone.
6. **Diversity:** raw and normalized uniqueness, duplicates, repetition and cross-scenario reuse. Reuse is not an individual error; novelty is not a reward.

Each check records its criterion, rubric version, rule ID/version, status, evidence, explanation, referenced fields and interpretation limits. `pass` establishes only the scoped check; `flag` identifies a detected violation; `inconclusive` retains uncertainty; `skipped` means content assessment is unavailable. Review workflow state is separate. There is no averaged or overall quality score.

## Denominators and comparability

Operational reporting distinguishes planned outputs, successful outputs and failures. Nonempty invalid outputs remain in format checks. Both nonempty-output and planned-output format denominators are explicit. Content checks skip execution failures. Per-method comparisons use exact shared scenario versions and repetitions. Inconclusive/skipped counts and decision coverage are shown beside violations; pass/(pass+flag) is not treated as model quality.

The content scorer accepts only permitted scenario fields and question text. Method, generator, priority, retrieval, origin, inferred assessments and research labels cannot affect it. Provenance is attached after scoring. The implementation hash includes the v3 scorer, orchestration and schema. Original v2 source and hash are archived under `backend/legacy_metrics/v2`.

## Immutable storage and exports

New reports are append-only `script_assessments` records, with timestamp, batch hash, implementation hash, rule versions and output/snapshot references. Legacy reports are read from their original job fields without migration writes. Re-evaluation never changes those fields. Exact report exports and version selection retain access to old and new evaluations. The CLI refuses to overwrite an existing file unless the caller explicitly requests it.

## Semantic review

Existing human review remains separate. The optional local semantic endpoint is disabled by default and requires an explicit enable flag, completed output/version and installed local model. Six anchored 1–4 ratings (or null) estimate reflection, relevance, factual grounding, pedagogical usefulness, clarity and agency. Exact model digest, prompt/rubric versions, settings, evidence, summaries, timestamps and failures are stored separately. Neither manual nor AI semantic judgments feed fixed metrics. Inline AI control remains disabled. No real semantic-model inference is used for this task's re-evaluation.

## Remaining limitations

English pattern coverage is limited. Arbitrary paraphrases, numerical reasoning, code semantics, nested negation and implied premises still require review. Explicit technology presence is not proof of relevance or correct use. The human form retains its existing binary criteria; these are not interchangeable with the six ordinal AI ratings, so no automatic cross-instrument agreement is reported. Unit tests establish specified behaviors, not educational validity.

The v3 re-evaluation is retrospective and informed by observed v2 problems. Validate the rubric on independent, human-annotated examples before treating it as a confirmatory semantic-quality instrument. Do not tune rules to favor comparative method scores.
