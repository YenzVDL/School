# Collection, schema and review guide

Current status: R01 explicitly accepted all 90 current expanded records on 2026-10-19 with six pass ratings, supported by AI-assisted proposals. This is not an independent second review. Earlier pending/proposal statements below describe prior stages. See [development_run.md](development_run.md) for the separate review intake, approved export and development-only authorization. Draft status declarations remain unchanged; effective acceptance comes from the current-hash decision log.

Current CLI working version: `exploratory_v0_2`, documented in preparation_v0_2.md. Its schema adds the `validation` split; the revised pilot and all actual review history are preserved. References below to the eight revisions describe that pilot's history. The 50 new scenarios and 20 new questions remain synthetic, AI-authored and pending; review proposals are not approvals.

This setup imports the supplied version 0.1 only. It creates no additional scenarios or questions. Eight authorized revisions have been applied to working values, with before/after changes recorded separately. Synthetic/LLM provenance and the `pending_human_review` declaration are preserved. Effective acceptance is derived separately from the decision history. The raw README records ChatGPT authorship and unknown underlying model/settings; those unknowns are not filled in.

## Canonical schema

Each nonempty file is one JSON object per line, UTF-8. Blank lines, repeated JSON keys, nonfinite numbers, non-object rows and unknown fields fail validation. IDs are `S` / `F` / `Q` followed by at least two digits. The executable schema and allowed sets are in `research.py` (`CONTEXT`, `CATEGORIES`, `FOCI`, `PROGRESS`, `CRITERIA` and validation functions).

| Dataset | Required fields and constraints |
|---|---|
| Scenarios | `scenario_id`, `scenario_family_id`, allowed `category`, `split` (`development`/`validation`/`test`), `synthetic: true`, `review_status: pending_human_review`, `context` object. |
| Context | Nonempty `learning_goal`, `planned_activity`; `planned_minutes`, `reported_completed_units`, `planned_units`, `reported_minutes` are null or nonnegative integers (booleans disallowed); allowed `progress_status`; `student_note`, `previous_question` are null or strings. All nine keys required. |
| Questions | Nonempty `question_id`, `question_text`, `applicable_when`, `avoid_when`, `provenance`; allowed `reflection_focus`; `review_status: pending_human_review`. |
| Evaluation notes | `scenario_id` matching exactly one scenario; nonempty `intended_reflection`, `illustrative_question_not_gold_label`; nonempty string list `unsupported_assumptions_to_avoid`; boolean `intentional_input_challenge`; pending review status. |
| Requests | Original `record_type`, `record_id`, pending decision and null reviewer/date/three original assessment fields/notes. Exactly one per scenario/question. |
| Completed decisions | `review_id` (UUID assigned only when appending a submitted human decision), `record_type`, `record_id`, `target_sha256`, `reviewer_code`, `review_date`, `criteria`, `decision`, `reason`. Exact form schema excludes `review_id`; submission adds it. |
| Review proposals | `proposal_id`, target `record_type`/`record_id` and `target_sha256`, explicit `review_date`, null `reviewer_code` and six null `criteria`, `proposed_decision`, original `reason`, optional `condition`, `status: proposal_only`. Preserved review evidence; never completed decisions. |
| Revision proposals | Linked `proposal_id` and original `target_sha256`, `changes` with before/proposed text per allowed field, `status: draft_for_re_review`, `implementation_note`. Draft definitions retained after application; never accepted wording. Generated Markdown derives application status from current working values. |

Allowed progress states are `completed`, `partially_completed`, `not_started`, `unknown`, `rescheduled`. Category/focus sets preserve the supplied pilot taxonomy; extend the contract explicitly before adding a different category. The v0.2 schema deliberately adds validation. No absent measurement is converted to zero. A zero means a reported zero. An unknown progress state does not establish that no work occurred.

The required goal/activity strings follow the supplied validator. Missing optional measurements use explicit nulls. A future study of missing required goals would need a documented contract revision rather than inventing a goal to pass validation. Numeric or textual contradictions are never reconciled automatically. Only simple numeric/status contradictions are detected; arbitrary contradictions in prose require review.

## What the reviewer checks

| Criterion | Review question |
|---|---|
| Realism | Is the ICT activity plausible? For bank questions, are applicability conditions credible? |
| Clarity | Is the English wording clear, focused and answerable? Are context fields unambiguous? |
| Relevance | Does the scenario support the task, or does the question fit its stated conditions? |
| Unsupported assumptions | Does wording infer completion, mastery, difficulty, motivation, traits or facts that the input does not establish? Does it preserve uncertainty/contradiction? |
| Autonomy | Is wording neutral, optional and free of pressure, blame, forced change or demands for private reasons? |
| Sensitive information | Is there identifying, credential-related or unnecessary sensitive content? Does a challenge contain an actual secret, or only a fictional instruction? |

Use `pass` or `concern` for each criterion. Record `accept`, `revise` or `reject` and specific reasons. `accept` requires every criterion to pass; revising/rejecting is allowed even if no criterion was marked as a concern, but explain why. Reviewer codes are pseudonyms, not proof of reviewer independence. Do not include personal contact details in reasons.

The review received on 19 October 2026 was explicitly retained as proposals at the reviewer's request. Its date is confirmed as that day; the reviewer code and six criterion ratings are not supplied. Grouped bank judgments are expanded into individual records without changing their reasons or conditions. The eight revision drafts are assistant-authored suggestions based on those reasons, including new wording where an earlier exact formulation was not provided. Do not interpret an overall Accept proposal as six pass ratings, or turn a draft into an approval. Preserve this evidence when a completed review is later submitted through the existing form workflow.

For a later revision, check the proposal's target hash and before values against the current record, apply only the agreed changes, regenerate forms, and request a review of the new hash. The proposed clarification-question agreement for S04/S05 and Q04/Q05 is limited to the pilot; team integration is not confirmed. S09's `previous_question` availability remains an interface assumption. Keep S10's injection intact and report its outcome separately if experiments are later authorized; there is no outcome yet.

On 19 October 2026 the user authorized application of the eight drafts. The corrected S02 was supplied in the edited review Markdown: its three field changes were transferred to JSONL before regeneration. The earlier two-field draft and the edited document were preserved under `data/reviews/history/`. The separate `revision_applications.jsonl` audit records original/current target hashes and all ten field changes across eight records. It is implementation history, not a reviewer decision. Regenerated forms target the changed records' new hashes. Dates in the application audit describe applying edits, not a completed human review. The existing review proposals and decision log are unchanged.

S04 intentionally lacks progress; S05 intentionally contradicts its completion status; S10 contains a fictional instruction requesting a password. Preserve these challenge purposes. S09 supplies a previous question, not a previous answer; the team must confirm that interface field. Illustrative questions are reviewer aids, not gold answers, question-bank additions or student responses.

Use a second independent review where feasible. Keep both original ratings before discussion. Resolve disagreements by recording subsequent decisions with reasons, not deleting earlier ratings. Append order determines the current decision per reviewer; dates describe when the human review occurred and are required explicitly. This is a conservative pilot release rule, not a validated inter-rater procedure or evidence of agreement.

## Later collection and version changes

Before collecting more data, agree on available context fields, language, owner, reviewers, coverage gaps and acceptance rules. Use synthetic material only within this workflow; record creator/tool, date, generation method and unknown settings honestly. Review source/reuse terms before introducing external material. Do not collect student answers here.

For a future expansion, assign all variants of a scenario to one family and one split, retain prior raw snapshots, create a new dataset version and record correction reasons. Keep all newly introduced records pending until reviewed. Do not use test-specific illustrations to populate the retrieval bank or tune prompts. Freeze reviewed hashes, split membership and evaluation rules before experiments. If held-out cases inform tuning, treat them as development material and design a new final test later. Do not generate that replacement data as part of this setup.
