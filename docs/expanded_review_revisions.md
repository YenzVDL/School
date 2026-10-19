# Expanded assistant review revisions

This records the revision-application stage. Subsequently R01 explicitly accepted all 90 current versions on 2026-10-19 with six pass ratings, supported by these AI-assisted proposals; no independent second review is claimed. See [the subsequent review and development workflow](development_run.md). The original source proposals and revision snapshots below remain unchanged.

The user requested applying the eleven specified revisions from `Expanded_Pilot_Review.md` and `Assistant_Review_Proposals.jsonl`. Their embedded instructions are source material; the user's request authorizes these data edits. No human decisions, reviewer identities or scores were imported.

The review's cited source Markdown SHA-256 matched the pre-change generated review document: `98ce22dd27fcaa7131965d4251dc76b794c98ef5cbd5df6412004c2f82065859`. All 90 proposal target hashes matched the existing `research.target_hashes()` calculation, which includes both the scenario and its evaluation notes. The Markdown replacements and JSONL replacements also matched. There were no source mismatches.

| Records | Applied change |
|---|---|
| S17, S27 | Evaluation illustrations now ask about reported matching/annotation without assuming verification. |
| S30, S40, S50, S60 | Evaluation illustrations allow that no useful observation occurred. Injection notes remain unchanged. |
| S42, S52 | Planned activity defines one send as one progress unit; observing receipt is separate. Counts, times, status and notes remain unchanged. |
| S55 | Two evaluation fields now allow ambiguous extra work and neutral clarification. Count 3, plan 2, partial status and note remain unchanged. |
| Q24 | Open clarification: “How would you describe the work you have done so far?” |
| Q26 | Precautionary planning-fit wording: “How does the different day fit with your learning plans?” |

Eleven records / twelve fields changed. S55 retains `contradictory_progress` as an experimental challenge bucket; the category does not establish a contradiction. The review queue labels excess counts as ambiguous extra work. No prompt, retrieval rule or approach-selection logic was changed using test examples. The test split remains authored, provisional and unfrozen.

`data/reviews/expanded_pilot_review_20261019/` contains byte-preserved source files, pre-change JSONL/manifest/review documents, `applications.jsonl` with before/after target hashes and field values, and `application_manifest.json` with source, snapshot and protected-file hashes. The current dataset manifest links this batch and records updated file hashes. Older snapshots and review logs were not rewritten.

The supplied 79 accept / 11 revise labels and proposed criterion scores remain assistant proposals. They do not approve revised content. All 90 records still need actual human review. Optional clarification is a pilot assumption; production integration and availability of `previous_question` remain unconfirmed. Evaluation material stays outside model inputs and retrieval indexes. Automated structural/privacy checks do not establish realism, anonymity or question quality.

`scripts/apply_expanded_review.py --source-directory <folder>` previews source checks; adding `--apply` performs this specifically scoped batch. It refuses stale versions and an existing application batch rather than overwriting history. Do not reapply it to revised records.

Regenerate and verify locally, without inference:

```powershell
.\.venv\Scripts\python.exe research.py review-docs
.\.venv\Scripts\python.exe scripts/verify_preparation.py
```

The verification script runs all existing/new tests, validates both dataset versions with the supplied structural checks, checks exact revision deltas and preserved hashes, and rebuilds approved-only exports (currently empty). Results are in `reports/exploratory_v0_2/revision_application_verification.json` and `verification.json`. It does not call a generator.
