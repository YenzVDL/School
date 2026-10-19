# Development-only shared prompt revision

Generated from the locked assessment comparison and prompt_revision.json.

All 140 AI01 rating identities, scenarios, question strings and hashes matched the original saved development review and results. Byte-preserved rating sources and the intake verification were saved before the method mapping was parsed or joined. The source declares mapping-blind assessment; wording may reveal methods. These are supplied AI ratings, not independent human judgments.

The attachment suggests later validation inference; that is not authorized by the current user request and was not executed.

## Original comparison

Seed trials were averaged within each method/scenario, then the 20 scenario means were averaged. See [the complete original comparison](../data/assessments/development_original_AI01_20261019/comparison.md), including criterion means, issue counts, output denominators and affected-scenario counts.

The source assessment rates technical specificity separately from usefulness: a concrete technical quiz can be specific but unsuitable for reflection. Assumption and serious-safety flags are reported separately from the four criterion means. Zero observed serious safety failures is not proof of safety. No overall quality/safety composite, confidence interval, or universal winner is invented.

## Exact instruction change

Only prompt_version and shared_system_constraints differ in the new versioned configuration. The entire old shared prompt remains intact; exactly one newline and the following text were appended for both generative approaches:

```text
Address the learner as "you". Ask about the learner's learning approach or observations, not a technical quiz. Do not ask for facts already explicitly supplied. When progress is unknown, do not presume any activity occurred; allow that none occurred. Clarify conflicting fields neutrally, without choosing which is true or demanding a reason. Do not repeat the wording or meaning of previous_question; choose a different reflection focus without inferring its answer.
```

Original config: `configs\experiment_v0_2.json` (SHA-256 `c33f3b9651291a85e338dc1f6e1faf750567c02380381bfc5f2415ce63c0387a`).
New config: `configs\experiment_v0_2_prompt_0_4.json` (SHA-256 `133df0259915503dc7f0d536c49ef954104f5de299b5e918c366ae9e714f90a7`).

Prompt version changes from `implementation_0.3_unmeasured` to `development_0.4_AI01_findings`. There are no removals, scenario-specific examples, answer templates, evaluation notes, or changes to the RAG-only instruction block. This is one shared revision developed on development findings, not an independently validated improvement.

## Preserved controls and rerun

The original run, original prompt/config, supplied source ratings, raw snapshot, canonical bank and human review history remain unchanged. Original executed code remains in that run's code_snapshot directory. The runner now accepts an explicit configuration path; the new run records that path/hash and its effective configuration.

The model artifact, native think:false setting, sampler, seeds (20261019, 20261020, 20261021), retrieval settings, applicability rules, bank, fallback and output limits remain unchanged. Development contains 20 scenarios; the scheduled rerun has 20 fixed selections and 60 outputs per generative method. It repeats the unchanged fixed baseline for a preservation check. These are 20 scenario units, not 60 independent scenarios.

The new shuffled review uses anonymous P001?P140 IDs, with context and delivered wording; method/seed mapping remains separate in review_mapping.jsonl. Raw outputs, actual requests/responses, latencies and all failures are retained. New outputs remain unscored; no inference on validation or final-test records is authorized.

```powershell
.\.venv\Scripts\python.exe scripts/run_development.py --run-development --config configs/experiment_v0_2_prompt_0_4.json --review-prefix P
```

This command creates a new run each time; do not repeat it merely to inspect saved outputs. The current run is linked by reports/exploratory_v0_2/development_run_latest.json. Use scripts/verify_development.py to verify a completed saved run without inference.

## Completed revised development run

Saved run: `runs/development_20261019T184942Z_e2b5c34c`. All 140 scheduled outputs completed: 20 fixed selections, 60 RAG and 60 direct outputs, with 120 model calls and zero recorded technical failures or fallbacks. New outputs remain unscored. Median elapsed times were 1.47 ms (fixed), 3.098 s (RAG) and 2.973 s (direct), including the documented per-call loading policy.

[Open the new anonymous P-series review](../runs/development_20261019T184942Z_e2b5c34c/output_review.md). The method/seed mapping is stored separately at `runs/development_20261019T184942Z_e2b5c34c/review_mapping.jsonl`. The raw-output review supplement is also available in the run directory.

The final audit verified all 19 original-run files and all supplied rating files byte-for-byte, exact append-only prompt changes, identical request payloads/options and generation schedule across runs, and unchanged fixed-bank questions. Model, sampler, seeds, bank, retrieval and applicability code remain unchanged. All 55 tests passed. Validation and final-test inference remained zero. See `reports/exploratory_v0_2/prompt_revision_verification.json`.
