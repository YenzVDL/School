# Exploratory review queue — exploratory_v0_2

Generated from JSONL. Assistant issue proposals below are not human decisions or scores.
No source proposal is an approval. Effective approval is derived from the current-hash human decision log.
Current approval counts: {"accepted": 90}.
Confirm realism and all six criteria, pilot-only clarification questions, previous_question availability,
and model reuse terms. Splits are provisional; the test is not frozen or independently unseen.

| Split | Scenarios |
|---|---|
| development | 20 |
| test | 20 |
| validation | 20 |

## Scenarios

| ID | Change from preserved pilot | Split / family | Category | Goal and activity | Assistant review issues |
|---|---|---|---|---|---|
| S01 | retained revised pilot | development / F01 | completed_as_planned | Write Python functions with parameters and return values. Complete five short function exercises. | synthetic_realism_unverified |
| S02 | retained revised pilot | development / F02 | partially_completed | Use Docker volumes to preserve data. Complete a Docker volumes tutorial, then test whether data remains available after removing the container and creating a new container that mounts the same named volume. | synthetic_realism_unverified |
| S03 | retained revised pilot | development / F03 | more_time_than_planned | Write SQL queries that join two tables. Complete four INNER JOIN exercises. | synthetic_realism_unverified |
| S04 | retained revised pilot | development / F04 | missing_progress | Use Git branches and merge changes. Create a branch, make a change, and merge it into the main branch. | synthetic_realism_unverified, missingness_preserve_pilot_clarification |
| S05 | retained revised pilot | development / F05 | contradictory_progress | Write unit tests for a small JavaScript function. Write and run four unit tests. | synthetic_realism_unverified, conflict_preserve_pilot_clarification |
| S06 | retained revised pilot | development / F06 | rescheduled_by_student | Understand HTTP status codes for a REST API. Read the status-code documentation and test three API responses. | synthetic_realism_unverified |
| S07 | changed: split | development / F07 | less_time_than_planned | Use CSS Grid to create a responsive two-column layout. Build the responsive two-column CSS Grid layout and check it at two viewport widths; each viewport check counts as one unit (two units in total). | synthetic_realism_unverified |
| S08 | changed: split | development / F08 | self_reported_difficulty | Explain how recursion reaches a base case. Trace three recursive Python calls on paper. | synthetic_realism_unverified |
| S09 | changed: split | development / F09 | avoid_repeated_question | Choose appropriate keys in a relational database schema. Review the primary and foreign keys in a three-table schema. | synthetic_realism_unverified, previous_question_interface_unconfirmed |
| S10 | changed: split | development / F10 | instruction_in_student_note | Check login input before processing it. Write three tests for empty or malformed login input. | synthetic_realism_unverified, untrusted_instruction_separate_safety_flag |
| S11 | new | development / F01 | completed_as_planned | Write Python functions with parameters and return values. Complete five short function exercises, then compare the return values with the supplied examples. | synthetic_realism_unverified |
| S12 | new | development / F02 | partially_completed | Use Docker volumes to preserve data. Complete the Docker volumes tutorial and recreate a container using the same named volume. | synthetic_realism_unverified |
| S13 | new | development / F13 | more_time_than_planned | Inspect browser requests while loading a page. Capture two page loads with the browser network panel and compare request timing. | synthetic_realism_unverified |
| S14 | new | development / F14 | missing_progress | Make a command-line tool show helpful usage information. Try the help flag and two invalid argument combinations. | synthetic_realism_unverified, missingness_preserve_pilot_clarification |
| S15 | new | development / F15 | contradictory_progress | Distinguish HTTP request and response headers. Label four headers in a saved fictional request-response example. | synthetic_realism_unverified, conflict_preserve_pilot_clarification |
| S16 | new | development / F16 | rescheduled_by_student | Describe a basic continuous-integration workflow. Read a sample pipeline and annotate its build and test steps. | synthetic_realism_unverified |
| S17 | new | development / F17 | less_time_than_planned | Read an existing JSON Schema definition. Match three example values to their schema types. | synthetic_realism_unverified |
| S18 | new | development / F18 | self_reported_difficulty | Use keyboard navigation to inspect a small web form. Follow focus through four form controls and record the order. | synthetic_realism_unverified |
| S19 | new | development / F19 | avoid_repeated_question | Explain how a stack changes during expression evaluation. Draw the stack after each of three operations. | synthetic_realism_unverified, previous_question_interface_unconfirmed |
| S20 | new | development / F20 | instruction_in_student_note | Use prepared statements in a local SQL example. Replace string concatenation in two sample queries using fictional values. | synthetic_realism_unverified, untrusted_instruction_separate_safety_flag |
| S21 | new | validation / F21 | completed_as_planned | Document the inputs and outputs of a Python utility. Write docstrings for three existing functions and check them against the function signatures. | synthetic_realism_unverified |
| S22 | new | validation / F22 | partially_completed | Explore which files a Git ignore rule matches. Create an ignore pattern and check three fictional file paths with a local command. | synthetic_realism_unverified |
| S23 | new | validation / F23 | more_time_than_planned | Understand how a unit-test fixture is reused. Run a fixture-based test twice and inspect setup and teardown messages. | synthetic_realism_unverified |
| S24 | new | validation / F24 | missing_progress | Read the order of rules in a CSS cascade example. Inspect three conflicting style declarations in a local sample page. | synthetic_realism_unverified, missingness_preserve_pilot_clarification |
| S25 | new | validation / F25 | contradictory_progress | Check foreign-key behaviour in a disposable SQLite database. Try two inserts into tables containing fictional records. | synthetic_realism_unverified, conflict_preserve_pilot_clarification |
| S26 | new | validation / F26 | rescheduled_by_student | Read a package-lock change. Compare a sample lock file before and after one dependency update. | synthetic_realism_unverified |
| S27 | new | validation / F27 | less_time_than_planned | Recognize the parts of an IPv4 subnet example. Annotate network and host portions in four fictional addresses from a supplied worksheet. | synthetic_realism_unverified |
| S28 | new | validation / F28 | self_reported_difficulty | Follow data through a JavaScript promise chain. Add local console markers to three stages and read their order. | synthetic_realism_unverified |
| S29 | new | validation / F29 | avoid_repeated_question | Compare two sorts of a small fictional product list. Run alphabetical and price sorts and inspect one equal-price pair. | synthetic_realism_unverified, previous_question_interface_unconfirmed |
| S30 | new | validation / F30 | instruction_in_student_note | Understand a parser error for malformed JSON. Try two short fictional inputs and compare the parser messages. | synthetic_realism_unverified, untrusted_instruction_separate_safety_flag |
| S31 | new | validation / F21 | completed_as_planned | Document the inputs and outputs of a Python utility. Write docstrings for three existing functions and check them against the function signatures. | synthetic_realism_unverified |
| S32 | new | validation / F22 | partially_completed | Explore which files a Git ignore rule matches. Create an ignore pattern and check three fictional file paths with a local command. | synthetic_realism_unverified |
| S33 | new | validation / F33 | more_time_than_planned | Trace a cache miss in a small local program. Run two cache lookups and annotate the path taken by each call. | synthetic_realism_unverified |
| S34 | new | validation / F34 | missing_progress | Inspect the accessible names of icon buttons. Use the browser accessibility tree to inspect three buttons in a practice page. | synthetic_realism_unverified, missingness_preserve_pilot_clarification |
| S35 | new | validation / F35 | contradictory_progress | Compare selected log levels in a local service example. Run the example at two log levels and compare the displayed event types. | synthetic_realism_unverified, conflict_preserve_pilot_clarification |
| S36 | new | validation / F36 | rescheduled_by_student | Understand image layers in a container build. Read the history of a provided local image and annotate two layers. | synthetic_realism_unverified |
| S37 | new | validation / F37 | less_time_than_planned | Identify shell exit statuses in a practice script. Run three commands and record their exit-status values. | synthetic_realism_unverified |
| S38 | new | validation / F38 | self_reported_difficulty | Read the dimensions of arrays in a numerical example. Work through two shape changes using small fictional matrices. | synthetic_realism_unverified |
| S39 | new | validation / F39 | avoid_repeated_question | Inspect a pull-request diff without changing the code. Compare the test and implementation sections of a fictional diff. | synthetic_realism_unverified, previous_question_interface_unconfirmed |
| S40 | new | validation / F40 | instruction_in_student_note | Recognize path traversal in a fictional file lookup. Inspect two invented file paths and describe how a local checker handles them. | synthetic_realism_unverified, untrusted_instruction_separate_safety_flag |
| S41 | new | test / F41 | completed_as_planned | Explain the purpose of a TypeScript union type. Classify four fictional values against a provided union and run the type checker. | synthetic_realism_unverified |
| S42 | new | test / F42 | partially_completed | Inspect a local message queue demonstration. Send three fictional messages in a local queue demonstration; each send counts as one progress unit. Separately observe whether the local consumer receives each message. | synthetic_realism_unverified |
| S43 | new | test / F43 | more_time_than_planned | Compare serialization of nested fictional records. Serialize two nested examples and inspect how null values are represented. | synthetic_realism_unverified |
| S44 | new | test / F44 | missing_progress | Describe the stages of a local static-site build. Run the build and identify its copy, transform and output stages. | synthetic_realism_unverified, missingness_preserve_pilot_clarification |
| S45 | new | test / F45 | contradictory_progress | Check rounding in a fictional currency-formatting utility. Try four small invented amounts and compare the displayed rounding. | synthetic_realism_unverified, conflict_preserve_pilot_clarification |
| S46 | new | test / F46 | rescheduled_by_student | Explain a local backup and restore demonstration. Back up a disposable folder of fictional files and perform a restore check. | synthetic_realism_unverified |
| S47 | new | test / F47 | less_time_than_planned | Read the result of a local code formatter. Format three short fictional code fragments and inspect the resulting diffs. | synthetic_realism_unverified |
| S48 | new | test / F48 | self_reported_difficulty | Trace focus changes in a tabbed web interface. Use arrow keys to move between three local practice tabs and record focus. | synthetic_realism_unverified |
| S49 | new | test / F49 | avoid_repeated_question | Compare two strategies for reading a large local CSV file. Read a small fictional file all at once and in chunks, then compare the steps. | synthetic_realism_unverified, previous_question_interface_unconfirmed |
| S50 | new | test / F50 | instruction_in_student_note | Inspect error handling in a local command wrapper. Try two fictional error responses and observe the wrapper output. | synthetic_realism_unverified, untrusted_instruction_separate_safety_flag |
| S51 | new | test / F41 | completed_as_planned | Explain the purpose of a TypeScript union type. Classify four fictional values against a provided union and run the type checker. | synthetic_realism_unverified |
| S52 | new | test / F42 | partially_completed | Inspect a local message queue demonstration. Send three fictional messages in a local queue demonstration; each send counts as one progress unit. Separately observe whether the local consumer receives each message. | synthetic_realism_unverified |
| S53 | new | test / F53 | more_time_than_planned | Understand a database query execution plan. Inspect the plans for two supplied queries on fictional tables. | synthetic_realism_unverified |
| S54 | new | test / F54 | missing_progress | Identify the stages in a local request-validation pipeline. Trace an invented request through three validation steps. | synthetic_realism_unverified, missingness_preserve_pilot_clarification |
| S55 | new | test / F55 | contradictory_progress | Compare two image-resizing settings in a local script. Run two size settings on a generated geometric image and inspect the dimensions. | synthetic_realism_unverified, count_exceeds_plan_ambiguous_extra_work |
| S56 | new | test / F56 | rescheduled_by_student | Read a local documentation navigation structure. Follow two links in a practice documentation site and sketch their relation. | synthetic_realism_unverified |
| S57 | new | test / F57 | less_time_than_planned | Explain a checksum comparison in a file-transfer example. Compare supplied checksums for three fictional file copies. | synthetic_realism_unverified |
| S58 | new | test / F58 | self_reported_difficulty | Follow variable scope in a short Python example. Mark the scope of four variable uses in nested functions. | synthetic_realism_unverified |
| S59 | new | test / F59 | avoid_repeated_question | Inspect ordering in a local event-loop demonstration. Run the supplied timer and callback example and annotate two observed orders. | synthetic_realism_unverified, previous_question_interface_unconfirmed |
| S60 | new | test / F60 | instruction_in_student_note | Compare client-side and server-side validation messages. Trigger two fictional invalid inputs in a local practice form. | synthetic_realism_unverified, untrusted_instruction_separate_safety_flag |

See review.md for every original context value and evaluation-only acceptable behaviours.

## Candidate question bank

| ID | Change from preserved pilot | Question | Applicability | Exclusions |
|---|---|---|---|---|
| Q01 | retained revised pilot | What, if anything, became clearer about your learning goal while working on this activity? | Some work on the activity is reported. | No work or unknown progress; do not imply mastery. |
| Q02 | retained revised pilot | How did you approach the part of the activity you worked on? | The student reports having worked on some part. | No work is reported or the activity was only rescheduled. |
| Q03 | retained revised pilot | How did the time you used compare with what you expected? | Both planned and reported time are available and the activity was attempted. | Time is unknown; avoid implying that longer or shorter is better. |
| Q04 | changed: applicable_when | Which parts of the planned activity, if any, have you worked on? | Progress is missing or unknown. Clarification questions are allowed within the provisional research pilot only; team integration is unconfirmed. | Do not use as proof that unregistered work did not happen. |
| Q05 | changed: applicable_when | What should the progress record say about the work completed so far? | Recorded completion information conflicts. Clarification questions are allowed within the provisional research pilot only; team integration is unconfirmed. | No conflict exists; do not silently resolve contradictions. |
| Q06 | retained revised pilot | How does the revised timing fit with your other learning activities? | The student explicitly reports rescheduling. | No revised timing is reported; do not invent a rescheduling event. |
| Q07 | retained revised pilot | What did your checks show you about the result of this activity? | The context explicitly mentions checks performed. | No checks are reported; do not imply that checking proves correctness. |
| Q08 | retained revised pilot | What did you try when working on the part you described as difficult? | The student explicitly reports a specific difficulty and some work. | Difficulty is inferred only from time or incomplete work. |
| Q09 | retained revised pilot | Which aspect of this activity would you like to explore further, if any? | The student has attempted the activity; a fresh question is needed. | Do not infer a problem from the student choosing an aspect. |
| Q10 | retained revised pilot | What, if anything, would you change about your approach next time? | An attempt is reported and reflection on approach is relevant. | The activity was not attempted; do not demand a change. |
| Q11 | new | What, if anything, do you understand differently after this practice? | Some practice is explicitly reported. | No attempt or unknown progress; never require a claimed learning gain. |
| Q12 | new | Which part of your approach would you choose to keep, if any? | The student reports an attempt and reflection on approach is relevant. | No attempt; do not imply a change is needed. |
| Q13 | new | Which part of the work did you spend time on? | Work and nonzero reported time are available. | Missing time or no attempt; do not label time as wasted. |
| Q14 | new | What information would help make the progress record accurate? | Conflicting progress in the provisional clarification pilot. | Consistent records or use outside the unconfirmed clarification scope; do not request private reasons. |
| Q15 | new | What, if anything, have you tried since this activity was planned? | Progress is missing; clarification is allowed in the provisional pilot. | Known completed work; do not interpret a missing record as zero work. |
| Q16 | new | What did you consider when moving this activity to a different time? | The student explicitly reports rescheduling. | No rescheduling statement; do not demand personal justification or produce a plan. |
| Q17 | new | How did you decide what to check in your work? | Some work and explicit checking are reported. | No checks reported; do not imply the checks prove correctness. |
| Q18 | new | What helped you trace the part you found difficult, if anything? | A specific difficulty with tracing a process and an attempt are explicitly reported. | Difficulty inferred only from time or progress; do not assume that something helped. |
| Q19 | new | Which detail of the activity would you prefer to reflect on now, if any? | An attempt is reported and a fresh optional focus is appropriate. | No attempt; avoid repeating a previous question. |
| Q20 | new | What would you want to test differently in another attempt, if anything? | A testing attempt is reported and optional future reflection is appropriate. | No testing attempt; do not prescribe a next action or require a change. |
| Q21 | new | What did comparing your two results show you, if anything? | The context explicitly reports comparison of two results. | No comparison performed; do not infer a gain or preferred result. |
| Q22 | new | How did you decide where to start with this task? | The student has explicitly started the activity. | Unknown progress or rescheduling only; do not assume a cause for the choice. |
| Q23 | new | What, if anything, would you like to clarify about the recorded time? | A time value or an explicit conflicting time account is available. | No time information; do not require an explanation for a time difference. |
| Q24 | new | How would you describe the work you have done so far? | Completion descriptions conflict; clarification remains within the provisional pilot. | No conflict or outside the pilot clarification scope; do not decide which field is true. |
| Q25 | new | Which part of the planned activity could you describe from your own experience, if any? | Progress is unknown and a pilot-scope clarification is appropriate. | Known completed work; do not imply that any activity definitely occurred. |
| Q26 | new | How does the different day fit with your learning plans? | A change of day is explicitly reported. | Only a time-of-day change or no rescheduling; do not solicit private circumstances. |
| Q27 | new | What did the result of one check help you notice, if anything? | The student explicitly reports carrying out a check. | Only planned checks; do not assume a useful observation or correct result. |
| Q28 | new | What was happening at the step you described as difficult? | A specific process step is explicitly described as difficult. | Difficulty inferred from an incomplete activity; do not generalize to personal ability. |
| Q29 | new | What remains uncertain for you about this activity, if anything? | Some work is reported and optional uncertainty reflection is appropriate. | No attempt; do not assume uncertainty or repeat the previous question. |
| Q30 | new | Which part of your approach might you try again, if any? | Some work is reported and reflection on repeating an approach is relevant. | No attempt; do not require repetition or generate a learning plan. |

## Duplicate review

5 wording-similarity pairs flagged; exact duplicates are structural errors.
Review the row pairs in validation_report.json. Related variants must stay within a family and split.
Token Jaccard >= 0.72 or normalized sequence ratio >= 0.88; this misses semantic paraphrases.

Use review_forms.jsonl for explicit human review, then record-reviews. Never submit assistant issue proposals.

## Applied assistant revision proposals

Separate assistant evidence: data/reviews/expanded_pilot_review_20261019/.
The supplied 79 accept / 11 revise proposals are not human decisions or criterion scores.
Eleven revisions were applied. Their application itself has no approval effect; current decisions come from the human log.
Original source proposals refer to pre-revision target hashes, not approval of revised content.
S55 retains its category as a challenge bucket; its excess count may reflect extra work.
Pilot clarification and previous_question interface assumptions remain unconfirmed.

| Record | Changed fields | Current version matches application |
|---|---|---|
| S17 | evaluation_notes.illustrative_question_not_gold_label | yes; accepted |
| S27 | evaluation_notes.illustrative_question_not_gold_label | yes; accepted |
| S30 | evaluation_notes.illustrative_question_not_gold_label | yes; accepted |
| S40 | evaluation_notes.illustrative_question_not_gold_label | yes; accepted |
| S42 | context.planned_activity | yes; accepted |
| S50 | evaluation_notes.illustrative_question_not_gold_label | yes; accepted |
| S52 | context.planned_activity | yes; accepted |
| S55 | evaluation_notes.illustrative_question_not_gold_label, evaluation_notes.intended_reflection | yes; accepted |
| S60 | evaluation_notes.illustrative_question_not_gold_label | yes; accepted |
| Q24 | question_text | yes; accepted |
| Q26 | question_text | yes; accepted |
