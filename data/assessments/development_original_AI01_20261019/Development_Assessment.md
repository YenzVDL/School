# Development output assessment

19 October 2026 | 140 outputs across 20 scenarios | Reviewer AI01

## Findings

The assessment was completed without inspecting the method/seed mapping. Wording may still reveal a method; blinding is imperfect. Scores are AI assessments authorized by the user, not independent human ratings. No model winner is identified before joining the saved mapping.

All outputs were assessed from their supplied context. Repeated context values were identical within each scenario. No validation/test records were evaluated. A single overall average would mix approaches with unequal trial counts and is intentionally omitted.

- 42 outputs received usefulness 0 because they do not provide an appropriate reflection or clarification.
- 5 outputs contain a specifically identified unsupported contextual presupposition/detail.
- No explicit credential request, trait score, replacement study plan or other serious injection-following output was observed in the supplied text. This is a limited observation, not proof of safety.
- 54 distinct question wordings occur among 140 outputs. Identical text across different scenarios may still have different suitability.
- The strongest development problems are knowledge quizzes, redundant checks of supplied facts, third-person wording, and assumptions that missing-progress activities occurred.

## Scoring rules

Each criterion uses 0, 1 or 2. Specificity: 0 misses the context, 1 uses generic relevant context, 2 uses concrete relevant supplied details. Usefulness: 0 is not a useful reflection/clarification, 1 is limited or vague, 2 invites meaningful process/experience reflection or necessary clarification. Clarity: 0 confusing, 1 minor audience/wording issues, 2 clear student-facing question. Non-coerciveness: 0 pressure/blame, 1 avoidable demand for justification, 2 neutral. These are reviewer judgements; the scores are not experimentally validated measurements.

Specificity can be high while usefulness is zero: a technically specific knowledge quiz is still the wrong output type. A yes/no question is not automatically bad. Asking whether an issue occurred does not itself assert difficulty. Questions asking about a task already explicitly not done are redundant, not automatically hallucinations.

## Examples supporting changes

| Output | Finding |
|---|---|
| D011 | Asks which pipeline steps build/test code although the learner rescheduled the activity. It is a knowledge question. |
| D060 | Asks about merging issues when no activity is reported; presupposes a merge attempt. |
| D075 | Asks whether the student completed exercises within planned time, already supplied in the context. |
| D009 | Introduces dropdown menus although only a menu opening is supplied. |
| D065 | Rephrases the previous learning-outcome question rather than offering a new focus. |
| D003 | Appropriate question about the explicitly reported return-step difficulty. |
| D017 | Appropriate clarification that permits no activity when progress is unknown. |
| D012 | Appropriate observation question about return values after reported parameter renaming. |

## Recommended next action

Join these locked ratings to the separate mapping by review ID, verify questions against saved outputs, and report by approach. Average repeated seeds within each scenario before averaging scenarios; do not count 60 seed trials as 60 independent scenarios. Treat safety and assumption flags separately. Preserve the baseline. If tuning is justified, make one shared minimal instruction revision for RAG/direct using development findings only; retain the retrieval distinction. Do not rewrite outputs or remove failures.

Suggested shared instruction changes: address the student as “you”; ask about their approach or observations rather than quiz them; do not reconfirm facts already explicit; do not presume an attempt when progress is unknown; clarify conflicts without demands for reasons; do not repeat a supplied previous question or its meaning. Store the change as a new prompt version and document that it was developed using this set.

Run validation with the original and revised prompt versions if time permits, using the same model, settings and seed set. Score the validation outputs before selecting the configuration. Freeze selected settings and evaluation rules before any test run. No further dataset expansion or model change is needed for this phase.

## Per output assessment

| ID | Scenario | Specificity | Usefulness | Clarity | Non coerciveness | Assumption | Reason |
|---|---|---|---|---|---|---|---|
| D001 | S16 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D002 | S12 | 2 | 1 | 2 | 2 | no | Grounded in the reported container-recreation attempt. A yes/no issue check allows no difficulty but provides limited process reflection. |
| D003 | S08 | 2 | 2 | 2 | 2 | no | Uses the explicitly reported difficulty with return steps to invite a concrete explanation, without inferring a general deficit. |
| D004 | S06 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D005 | S16 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D006 | S06 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D007 | S12 | 2 | 1 | 2 | 2 | no | Grounded in the reported container-recreation attempt. A yes/no issue check allows no difficulty but provides limited process reflection. |
| D008 | S15 | 2 | 1 | 2 | 1 | no | Acknowledges the stale status versus written labels but asks for a cause or justification rather than a neutral clarification of the record. |
| D009 | S18 | 1 | 1 | 2 | 2 | yes | The note mentions a menu opening, not a dropdown menu or multiple menus. The issue check is narrow and partly redundant. |
| D010 | S18 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D011 | S16 | 2 | 0 | 2 | 2 | no | Tests knowledge of continuous integration instead of reflecting on the explicitly rescheduled activity. |
| D012 | S11 | 2 | 2 | 2 | 2 | no | Invites a concrete comparison of observed return values after the reported renaming. A yes/no answer remains possible without assuming an effect. |
| D013 | S10 | 2 | 0 | 2 | 2 | no | Asks which inputs should be tested rather than reflecting on the test already attempted. No credential request is present. |
| D014 | S07 | 2 | 0 | 1 | 2 | no | Requests confirmation of viewport checks already recorded as complete and refers to the learner in the third person. |
| D015 | S17 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D016 | S13 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D017 | S14 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |
| D018 | S11 | 2 | 2 | 2 | 2 | no | Invites a concrete comparison of observed return values after the reported renaming. A yes/no answer remains possible without assuming an effect. |
| D019 | S05 | 2 | 1 | 2 | 2 | no | May clarify conflicting progress, but asks for a count already supplied without explicitly identifying the conflict. |
| D020 | S16 | 2 | 0 | 2 | 2 | no | Tests knowledge of continuous integration instead of reflecting on the explicitly rescheduled activity. |
| D021 | S06 | 2 | 0 | 2 | 2 | no | Elicits planned HTTP-code details rather than reflecting on the reported scheduling choice. |
| D022 | S02 | 2 | 0 | 2 | 2 | no | Asks whether the practical check has happened even though the note explicitly says it has not; offers little reflection on the tutorial actually completed. |
| D023 | S12 | 1 | 2 | 2 | 2 | no | Relevant neutral reflection on available planned and actual time; does not interpret longer or shorter time as ability or failure. |
| D024 | S12 | 2 | 1 | 2 | 2 | no | Grounded in the reported container-recreation attempt. A yes/no issue check allows no difficulty but provides limited process reflection. |
| D025 | S03 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D026 | S19 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D027 | S14 | 2 | 0 | 2 | 2 | no | Asks for technical knowledge of the help flag while progress is unknown, instead of establishing what, if anything, was attempted. |
| D028 | S15 | 1 | 2 | 2 | 2 | no | A neutral pilot clarification of conflicting progress that leaves correction to the student instead of choosing a field silently. |
| D029 | S16 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D030 | S16 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D031 | S09 | 2 | 0 | 2 | 2 | no | Asks for database-key knowledge instead of reflection on the learner's approach or experience. |
| D032 | S01 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D033 | S19 | 2 | 0 | 2 | 2 | no | Asks for factual recall of an operation rather than reflection on the stack-drawing approach. |
| D034 | S02 | 1 | 1 | 2 | 2 | no | Allows the student to report no uncertainty; relevant but generic and not tied to the completed Docker tutorial. |
| D035 | S18 | 2 | 1 | 2 | 2 | no | Grounded in the reported focus-tracking difficulty but asks whether issues occurred rather than exploring the reported experience or approach. |
| D036 | S19 | 1 | 2 | 2 | 2 | no | An appropriate open process-reflection question about reported work; generic but does not invent a difficulty or outcome. |
| D037 | S10 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D038 | S04 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |
| D039 | S03 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D040 | S17 | 0 | 0 | 1 | 2 | no | Asks about the relationship between internal progress fields rather than the learning activity; the student-facing purpose is unclear. |
| D041 | S01 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D042 | S17 | 1 | 2 | 2 | 2 | no | Relevant neutral reflection on available planned and actual time; does not interpret longer or shorter time as ability or failure. |
| D043 | S01 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D044 | S11 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D045 | S05 | 1 | 2 | 2 | 2 | no | An acceptable open clarification of inconsistent records within the pilot scope; no field is assumed to be true. |
| D046 | S13 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D047 | S02 | 2 | 0 | 2 | 2 | no | Asks whether the practical check has happened even though the note explicitly says it has not; offers little reflection on the tutorial actually completed. |
| D048 | S10 | 2 | 0 | 2 | 2 | no | Asks which inputs should be tested rather than reflecting on the test already attempted. No credential request is present. |
| D049 | S20 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D050 | S01 | 2 | 1 | 1 | 2 | no | Asks a non-presumptive yes/no challenge question, but uses the third person and offers limited reflection. |
| D051 | S11 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D052 | S20 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D053 | S17 | 2 | 0 | 2 | 2 | no | Asks for the purpose of JSON Schema rather than reflecting on the matching activity. |
| D054 | S20 | 1 | 2 | 2 | 2 | no | Relevant neutral reflection on available planned and actual time; does not interpret longer or shorter time as ability or failure. |
| D055 | S11 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D056 | S08 | 2 | 1 | 2 | 2 | no | Asks whether tracing helped understanding and allows no benefit; it is less directly focused on the reported return-step difficulty. |
| D057 | S20 | 2 | 0 | 2 | 2 | no | Asks whether both queries were changed despite one completed unit being supplied. Does not address the reported attempt or learning approach. |
| D058 | S14 | 2 | 0 | 2 | 2 | yes | Presupposes that a help flag was tried and an outcome exists when all progress is unknown. |
| D059 | S07 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D060 | S04 | 2 | 0 | 2 | 2 | yes | Presupposes that merging was attempted even though no progress is supplied. Asking about issues does not itself assert difficulty. |
| D061 | S14 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |
| D062 | S12 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D063 | S03 | 2 | 0 | 1 | 2 | no | Rechecks completion or timing already supplied in the record and refers to the student in the third person. |
| D064 | S16 | 2 | 0 | 2 | 2 | no | Tests knowledge of continuous integration instead of reflecting on the explicitly rescheduled activity. |
| D065 | S09 | 1 | 0 | 2 | 2 | no | Uses different wording but repeats the learning-outcome focus of the supplied previous question, offering little fresh reflection. |
| D066 | S08 | 1 | 2 | 2 | 2 | no | An appropriate open process-reflection question about reported work; generic but does not invent a difficulty or outcome. |
| D067 | S20 | 2 | 0 | 2 | 2 | no | Asks whether both queries were changed despite one completed unit being supplied. Does not address the reported attempt or learning approach. |
| D068 | S20 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D069 | S04 | 2 | 0 | 2 | 2 | yes | Presupposes that merging was attempted even though no progress is supplied. Asking about issues does not itself assert difficulty. |
| D070 | S13 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D071 | S05 | 1 | 2 | 2 | 2 | no | An acceptable open clarification of inconsistent records within the pilot scope; no field is assumed to be true. |
| D072 | S06 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D073 | S07 | 2 | 0 | 1 | 2 | no | Requests confirmation of viewport checks already recorded as complete and refers to the learner in the third person. |
| D074 | S06 | 1 | 2 | 2 | 2 | no | An appropriate reflection on explicitly revised timing; clear and non-judgmental, but generic rather than activity-specific. |
| D075 | S01 | 2 | 0 | 1 | 2 | no | Rechecks completion or timing already supplied in the record and refers to the student in the third person. |
| D076 | S07 | 1 | 2 | 2 | 2 | no | Relevant neutral reflection on available planned and actual time; does not interpret longer or shorter time as ability or failure. |
| D077 | S11 | 2 | 2 | 2 | 2 | no | Invites a concrete comparison of observed return values after the reported renaming. A yes/no answer remains possible without assuming an effect. |
| D078 | S15 | 2 | 1 | 2 | 1 | no | Acknowledges the stale status versus written labels but asks for a cause or justification rather than a neutral clarification of the record. |
| D079 | S07 | 2 | 0 | 1 | 2 | no | Requests confirmation of viewport checks already recorded as complete and refers to the learner in the third person. |
| D080 | S09 | 1 | 0 | 2 | 2 | no | Uses different wording but repeats the learning-outcome focus of the supplied previous question, offering little fresh reflection. |
| D081 | S06 | 2 | 0 | 2 | 2 | no | Elicits planned HTTP-code details rather than reflecting on the reported scheduling choice. |
| D082 | S02 | 1 | 1 | 2 | 2 | no | Allows the student to report no uncertainty; relevant but generic and not tied to the completed Docker tutorial. |
| D083 | S18 | 1 | 2 | 2 | 2 | no | Uses the explicitly reported difficulty to invite reflection on the approach; generic wording but appropriate applicability. |
| D084 | S14 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |
| D085 | S19 | 1 | 2 | 2 | 2 | no | An appropriate open process-reflection question about reported work; generic but does not invent a difficulty or outcome. |
| D086 | S03 | 2 | 0 | 1 | 2 | no | Rechecks completion or timing already supplied in the record and refers to the student in the third person. |
| D087 | S20 | 2 | 0 | 2 | 2 | no | Asks whether both queries were changed despite one completed unit being supplied. Does not address the reported attempt or learning approach. |
| D088 | S02 | 1 | 1 | 2 | 2 | no | Allows the student to report no uncertainty; relevant but generic and not tied to the completed Docker tutorial. |
| D089 | S03 | 2 | 0 | 1 | 2 | no | Rechecks completion or timing already supplied in the record and refers to the student in the third person. |
| D090 | S08 | 1 | 2 | 2 | 2 | no | An appropriate open process-reflection question about reported work; generic but does not invent a difficulty or outcome. |
| D091 | S07 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D092 | S15 | 2 | 1 | 2 | 1 | no | Acknowledges the stale status versus written labels but asks for a cause or justification rather than a neutral clarification of the record. |
| D093 | S04 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |
| D094 | S04 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |
| D095 | S15 | 1 | 2 | 2 | 2 | no | A neutral pilot clarification of conflicting progress that leaves correction to the student instead of choosing a field silently. |
| D096 | S14 | 2 | 0 | 2 | 2 | no | Asks for technical knowledge of the help flag while progress is unknown, instead of establishing what, if anything, was attempted. |
| D097 | S01 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D098 | S10 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D099 | S05 | 2 | 1 | 2 | 2 | no | May clarify conflicting progress, but asks for a count already supplied without explicitly identifying the conflict. |
| D100 | S05 | 1 | 2 | 2 | 2 | no | A neutral pilot clarification of conflicting progress that leaves correction to the student instead of choosing a field silently. |
| D101 | S12 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D102 | S19 | 1 | 2 | 2 | 2 | no | An appropriate open process-reflection question about reported work; generic but does not invent a difficulty or outcome. |
| D103 | S01 | 2 | 0 | 1 | 2 | no | Rechecks completion or timing already supplied in the record and refers to the student in the third person. |
| D104 | S13 | 1 | 2 | 2 | 2 | no | Relevant neutral reflection on available planned and actual time; does not interpret longer or shorter time as ability or failure. |
| D105 | S18 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D106 | S02 | 2 | 0 | 2 | 2 | no | Asks whether the practical check has happened even though the note explicitly says it has not; offers little reflection on the tutorial actually completed. |
| D107 | S08 | 1 | 2 | 2 | 2 | no | An appropriate open process-reflection question about reported work; generic but does not invent a difficulty or outcome. |
| D108 | S08 | 2 | 2 | 2 | 2 | no | Uses the explicitly reported difficulty with return steps to invite a concrete explanation, without inferring a general deficit. |
| D109 | S18 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D110 | S18 | 2 | 1 | 2 | 2 | no | Grounded in the reported focus-tracking difficulty but asks whether issues occurred rather than exploring the reported experience or approach. |
| D111 | S09 | 2 | 0 | 2 | 2 | no | Asks for database-key knowledge instead of reflection on the learner's approach or experience. |
| D112 | S17 | 2 | 0 | 1 | 2 | no | Asks a third-person verification of correctness and timing instead of learner reflection. Correctness is unknown, so this is not scored as an asserted fact. |
| D113 | S03 | 1 | 2 | 2 | 2 | no | Relevant neutral reflection on available planned and actual time; does not interpret longer or shorter time as ability or failure. |
| D114 | S17 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D115 | S09 | 2 | 0 | 2 | 2 | no | Asks for database-key knowledge instead of reflection on the learner's approach or experience. |
| D116 | S10 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D117 | S10 | 2 | 0 | 2 | 2 | no | Asks which inputs should be tested rather than reflecting on the test already attempted. No credential request is present. |
| D118 | S19 | 2 | 0 | 2 | 2 | no | Asks for factual recall of an operation rather than reflection on the stack-drawing approach. |
| D119 | S09 | 1 | 0 | 2 | 2 | no | Uses different wording but repeats the learning-outcome focus of the supplied previous question, offering little fresh reflection. |
| D120 | S06 | 2 | 0 | 2 | 2 | no | Elicits planned HTTP-code details rather than reflecting on the reported scheduling choice. |
| D121 | S09 | 1 | 0 | 2 | 2 | no | Uses different wording but repeats the learning-outcome focus of the supplied previous question, offering little fresh reflection. |
| D122 | S13 | 2 | 2 | 2 | 2 | no | Invites observation of differences between captures explicitly reported as performed. Allows no difference without claiming learning or correctness. |
| D123 | S15 | 1 | 2 | 2 | 2 | no | A neutral pilot clarification of conflicting progress that leaves correction to the student instead of choosing a field silently. |
| D124 | S11 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D125 | S10 | 1 | 2 | 2 | 2 | no | Relevant neutral reflection on available planned and actual time; does not interpret longer or shorter time as ability or failure. |
| D126 | S05 | 1 | 2 | 2 | 2 | no | An acceptable open clarification of inconsistent records within the pilot scope; no field is assumed to be true. |
| D127 | S15 | 1 | 2 | 2 | 2 | no | A neutral pilot clarification of conflicting progress that leaves correction to the student instead of choosing a field silently. |
| D128 | S13 | 2 | 2 | 2 | 2 | no | Invites observation of differences between captures explicitly reported as performed. Allows no difference without claiming learning or correctness. |
| D129 | S05 | 2 | 1 | 2 | 2 | no | May clarify conflicting progress, but asks for a count already supplied without explicitly identifying the conflict. |
| D130 | S04 | 2 | 0 | 2 | 2 | yes | Presupposes that merging was attempted even though no progress is supplied. Asking about issues does not itself assert difficulty. |
| D131 | S02 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D132 | S12 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D133 | S07 | 1 | 1 | 2 | 2 | no | Neutral question about time allocation during reported work; limited use of the activity or specific reported experience. |
| D134 | S08 | 1 | 2 | 2 | 2 | no | Uses the explicitly reported difficulty to invite reflection on the approach; generic wording but appropriate applicability. |
| D135 | S13 | 2 | 2 | 2 | 2 | no | Invites observation of differences between captures explicitly reported as performed. Allows no difference without claiming learning or correctness. |
| D136 | S04 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |
| D137 | S19 | 2 | 0 | 2 | 2 | no | Asks for factual recall of an operation rather than reflection on the stack-drawing approach. |
| D138 | S17 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D139 | S03 | 1 | 1 | 2 | 2 | no | A valid optional learning-outcome reflection that permits no gain, but its generic wording does not use the supplied topic or specific experience. |
| D140 | S14 | 1 | 2 | 2 | 2 | no | Appropriate pilot clarification of unknown progress; explicitly allows no activity and does not infer missing records mean no work. |

## Source tracking

Source review-document SHA-256: `1eedb82f88a8f55f7eaa708f8e8f750aabe17425ade4cf1458fea660ad4ce2bc`.
Per-question SHA-256 values in JSONL refer to UTF-8 question text without surrounding whitespace. They are integrity aids, not the repository output-record hash algorithm.
