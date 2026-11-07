# V2 versus v3: retrospective reevaluation

All 108 original outputs were reused. No questions were regenerated and no AI semantic evaluator was run. Both old and new results are independently exportable.

## Confirmed changes

- Format denominator: v2 reported 100% over 107 accepted outputs; v3 reports 107/108 raw nonempty outputs (99.07%). The quoted RAG response is still one execution/format failure.
- V2 wording cues: 66 pass, 41 inconclusive. V3 structure: 44 recognizable learner-reflection patterns, 51 recognizable knowledge/recall patterns, 12 ambiguous, 1 skipped. These are different constructs, not a model improvement.
- V3 detects the previously missed assertion of 15 recorded minutes against 35 recorded minutes. Evidence is normalized to 900 versus 2100 seconds.
- SQL query-plan wording no longer establishes reflection merely through the word plan. Missing lexical overlap does not establish irrelevance.
- V3 contextual indicators: 65 pass, 6 flags, 36 inconclusive, 1 skipped. Factual indicators: 4 pass, 7 flags, 96 inconclusive, 1 skipped. These remain scoped checks, not complete semantic correctness.
- Agency interpretation remains inconclusive for all 107 valid questions; lack of a listed problematic phrase is not an agency-quality pass.

## Per-method v3 indicators

| Method | Success/planned | Format pass/flag | Structure pass/flag/inconclusive | Factual pass/flag/inconclusive |
| --- | --- | --- | --- | --- |
| constrained | 36/36 | 36/0 | 0/29/7 | 1/3/32 |
| fixed | 36/36 | 36/0 | 36/0/0 | 1/0/35 |
| rag | 35/36 | 35/1 | 8/22/5 | 2/4/29 |

Scores are not averaged into a quality index and no architecture is declared superior. The tokenizer and constructs changed between rubrics; lexical figures and contextual pass counts are not direct measures of improved output. New independent validation data is needed for confirmatory use.

## Preservation and provenance

- Original v2 report: `script_assessment_3b18fac4a96c4e87` / `fe1eeecce0fd839690b7a26a2de6ba58ce70946629aa5247647b0ed1e01e2b00`.
- New v3 report: `script_assessment_4a5b2cbd33ad4bb7` / `02efb554849ac9c1fbbb611465cc5fe7414771f54ec065e9503c8af3f5c23dab`.
- The archived v2 implementation exactly reproduces the saved v2 report; current v3 exactly reproduces the new report. Original file hashes, outputs, snapshots, labels, reviews, influences and jobs match their pre-upgrade hashes.
- During upgrade, the still-running v2 backend saved an additional legacy evaluation. That report is preserved separately as `legacy-upgrade-report.json` and as an immutable report record. The original job report reference was restored from the pre-upgrade backup. New code no longer rewrites job report fields.
- Regression inspection found the expected numeric, structure and denominator differences above. Additional inconclusive outcomes reflect deliberately narrower claims, not evidence that the original questions became worse. No rules were tuned after inspecting the new comparative method aggregates.

## Validation

- 203 backend tests passed; 3 browser tests passed; production frontend build passed.
- Optional semantic integration was tested with provider doubles only, including malformed ratings and digest drift. No live AI semantic assessment was executed.

Files: `AUDIT.md`, `PROTOCOL.md`, `fixed-metrics-v3.json`, `old-new-reports.json`, `observed-differences.json`, `preservation-before.json`, `preservation-after.json`, `frozen-rubric.json`, and archived implementation sources.
