"""Conservative method-blind indicators, not an automated semantic assessor.

This module accepts question text and permitted scenario fields only. Every
rule establishes its own scoped property; uncertainty is never a positive label.
"""
import hashlib
import json
import re
import unicodedata
from .schema import Inputs, prompt_inputs

VERSION = 'fixed-rubric-v3-method-blind'
DIMENSIONS = ['format', 'reflection_structure', 'contextual_grounding', 'factual_grounding', 'agency_wording']
DEFINITIONS = {
    'format': 'Mechanical punctuation, word budget, single-line interrogative form, no recognized extra response and normalized previous-question repetition. Language is separately inconclusive.',
    'reflection_structure': 'Recognizable learner-directed strategy, decision, evidence or planning patterns versus recognizable technical recall. Pattern classification is not proof of educational usefulness.',
    'contextual_grounding': 'Explicit references to supplied fields and grounded named technologies. Lexical overlap is descriptive only; absence of overlap does not imply irrelevance.',
    'factual_grounding': 'Recognized assertions about time, quantities, progress, recorded control answers and performance. Missing evidence, hypothetical alternatives and conflicting records are distinguished. Unrecognized claims require review.',
    'agency_wording': 'Listed direct coercion, ability judgments, emotion/performance premises and diagnoses. No detected wording pattern is not proof of appropriate tone.',
}
TECHNOLOGIES = {
    'python': r'\bpython\b', 'javascript': r'\bjavascript\b', 'typescript': r'\btypescript\b',
    'java': r'\bjava\b', 'sql': r'\bsql\b', 'git': r'\bgit\b', 'html': r'\bhtml\b',
    'css': r'\bcss\b', 'react': r'\breact\b', 'dns': r'\bdns\b', 'tcp': r'\btcp\b',
    'uml': r'\buml\b', 'flask': r'\bflask\b', 'django': r'\bdjango\b', 'sqlite': r'\bsqlite\b',
    'postgresql': r'\bpostgres(?:ql)?\b', 'https': r'\bhttps\b', 'http': r'\bhttp\b',
}
WORDS = dict(enumerate('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()))
NUMBERS = {v: k for k, v in WORDS.items()}
NUM = r'(?:\d+(?:\.\d+)?|' + '|'.join(NUMBERS) + r')'
TIME = re.compile(r'\b(?P<number>'+NUM+r')\s*(?P<unit>seconds?|minutes?|hours?)\b', re.I)
QUANTITY = re.compile(r'\b(?P<number>'+NUM+r')\s*(?:planned\s+)?(?P<unit>steps?|tests?|tasks?|exercises?|functions?|checks?|activities)\b', re.I)
FRACTION = re.compile(r'\b(?P<completed>'+NUM+r')\s+(?:out\s+)?of\s+(?:(?:the|your|planned)\s+)*(?P<planned>'+NUM+r')\s+(?:planned\s+)?(?P<unit>steps?|tests?|tasks?|exercises?|checks?)\b', re.I)
STOP = set('a an the this that these those and or to of in on at by with for from your you would could might can do did does how what which why it its is are was were be been have has one two three four all some any before after only next step learning student ict task activity question information null none planned reported recorded value unit minutes hours seconds time'.split())


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text or '').casefold().split())


def clean_inputs(raw):
    # Remove metadata at every nesting level, including inferred assessments.
    raw = raw or {}
    allowed = {k: raw.get(k) for k in Inputs.model_fields}
    for key, fields in {'progress': ['description', 'planned_units', 'completed_units', 'unit'], 'planned_time':['value','unit'], 'reported_time':['value','unit']}.items():
        if isinstance(allowed[key], dict):
            allowed[key] = {k:v for k,v in allowed[key].items() if k in fields}
    if isinstance(allowed['control_results'], list):
        allowed['control_results'] = [{k:v for k,v in c.items() if k in ['question','student_answer','reference_answer','recorded_assessment']} for c in allowed['control_results']]
    return prompt_inputs(allowed)


def text_fields(inputs):
    fields = {k: inputs[k] for k in ['learning_goal','planned_activity','student_note'] if inputs.get(k)}
    if (inputs.get('progress') or {}).get('description'):
        fields['progress.description'] = inputs['progress']['description']
    for i, row in enumerate(inputs.get('control_results') or []):
        for key in ['question','student_answer','reference_answer','recorded_assessment']:
            if row.get(key): fields[f'control_results[{i}].{key}'] = row[key]
    return fields


def tokens(text):
    words = re.findall(r'[a-z][a-z0-9]+', normalized(text))
    # Transparent conservative plural folding, not a semantic embedding.
    return {w[:-1] if len(w)>4 and w.endswith('s') and not w.endswith(('ss','us','is')) else w for w in words if w not in STOP}


def number(value):
    return NUMBERS[value.lower()] if value.lower() in NUMBERS else float(value)


def seconds(value):
    return value['value'] * {'seconds':1,'minutes':60,'hours':3600}[value['unit']]


def hypothetical(text, start):
    prefix = text[:start].lower()
    # Reset at an asserted premise; a hypothetical main question cannot erase it.
    clause = re.split(r'\b(?:given that|because|since|even though)\b|[;]', prefix)[-1]
    if re.search(r'\b(?:if|suppose|imagine|were to)\b', clause): return True
    if re.match(r'your (?:recorded )?(?:correct|incorrect) answer\b|your (?:failure|success|frustration|anxiety|anger)\b|you (?:completed|finished|failed|fixed|corrected|answered)\b',text[start:],re.I):
        return False  # A modal invitation does not erase its embedded premise.
    return bool(re.search(r'\b(?:would|could|might|will|can) you\b|\b(?:next time|future|next session)\b', clause)
                and not re.search(r'\b(?:spent|recorded|completed|finished|answered|failed|your incorrect|your correct)\b', clause))


def score(question, raw_inputs):
    inputs = clean_inputs(raw_inputs)
    question = question or ''
    fields = text_fields(inputs)
    checks = []
    def add(dimension, rule, status, evidence, explanation, paths=(), semantic=False):
        result = {'criterion_id':dimension, 'metric_version':VERSION, 'rule_id':rule+'.v1', 'rule_version':'1',
                  'status':status, 'evidence':evidence, 'explanation':explanation,
                  'scenario_fields':list(paths), 'deterministic':True, 'requires_semantic_judgment':semantic}
        checks.append(result)
        return result
    def boolean(rule, good, explanation, evidence=None, paths=()):
        add('format', rule, 'pass' if good else 'flag', evidence if evidence is not None else [], explanation, paths)
    words = question.split()
    boolean('format.nonempty', bool(question.strip()), 'Raw output contains text.', {'characters':len(question)})
    boolean('format.question_mark_count', question.count('?')==1, 'Exactly one question mark is required; this is a punctuation check.', {'count':question.count('?')})
    boolean('format.ends_in_question_mark', question.rstrip().endswith('?'), 'Raw output must end with a question mark, without trailing response text or quotation marks.')
    boolean('format.word_budget', len(words)<=40, 'Maximum 40 whitespace-delimited words.', {'word_count':len(words),'maximum':40})
    boolean('format.single_line', '\n' not in question and '\r' not in question, 'One line is required.')
    interrogative = bool(re.match(r'^(?:(?:in|for|during|after|before|given) [^?.!\n]{1,80},\s*)?(?:what|which|how|why|when|where|who|whose|would|could|might|can|do|does|did|is|are|should|have|has)\b',question.strip(),re.I))
    extra = re.search(r'^\s*(?:here is (?:a|the)\b|answer:|explanation:|reflection question:)|</?(?:think|analysis)>',question,re.I)
    additional=bool(extra or re.search(r'\.\s+(?:what|which|how|why)\b',question,re.I))
    add('format','format.no_extra_response','flag' if additional else 'pass' if interrogative else 'inconclusive',
        {'recognized_wrapper':extra.group() if extra else None},'Recognized interrogative structure without listed extra response text. Unrecognized language/structure is inconclusive, not proof of extra explanation.')
    previous = inputs.get('previous_question')
    if previous:
        boolean('format.previous_nonrepetition', normalized(question)!=normalized(previous), 'NFKC, case and whitespace normalized exact comparison.', {'previous_question':previous}, ['previous_question'])
    else:
        add('format','format.previous_nonrepetition','inconclusive',[], 'No previous question was supplied.', ['previous_question'])
    add('format','format.language','inconclusive',[], 'No validated deterministic language detector is configured; English-looking keywords are not language proof.', semantic=True)

    # Recognize syntax involving the learner, not isolated words such as query plan.
    reflective = re.search(r'^(?:what|which|how)\b.*\b(?:would|could|might|will) you\b.*\b(?:approach|practi[cs]e|learn|check|record|plan|choose|compare|revisit|change|adjust|try|explain|investigate|inspect)\b',question,re.I)
    reflective = reflective or re.search(r'^(?:what|which)\b.*\b(?:example|evidence|approach|strategy|step|part|change|observation)\b.*\b(?:would|could|might) (?:you|help you)\b',question,re.I)
    reflective = reflective or re.search(r'^what (?:led|helped|influenced) you to (?:select|choose|decide|learn)\b|^how (?:did|do) you (?:choose|decide|approach|check|learn|plan|adapt|compare)\b|^what (?:did|have) you (?:learn|notice|change)',question,re.I)
    knowledge = re.search(r'^what (?:is|are|does|do)\b|^what (?:exact|default)\b',question,re.I)
    ambiguous_explanation = re.search(r'^what is (?:one |a )?(?:potential|possible) (?:reason|explanation|issue|challenge)',question,re.I)
    classification = 'ambiguous'
    if reflective:
        classification = ('planning_next_steps' if re.search(r'\b(?:plan|next|record|adjust)\b',question,re.I) else
                          'learning_strategy' if re.search(r'\b(?:learn|practice|practise|strategy)\b',question,re.I) else
                          'results_evidence' if re.search(r'\b(?:evidence|result|inspect|check|notice)\b',question,re.I) else 'decisions_approaches')
    elif knowledge and not ambiguous_explanation: classification = 'technical_knowledge_or_recall'
    add('reflection_structure','structure.learner_directed', 'pass' if reflective else 'flag' if classification=='technical_knowledge_or_recall' else 'inconclusive',
        {'classification':classification,'matched_pattern':reflective.group() if reflective else knowledge.group() if knowledge and not ambiguous_explanation else None},
        'Recognized question structure only; genuine reflection and educational usefulness require semantic review.', semantic=True)

    # Conflicts are evidence properties. Do not choose the structured field or note as truth.
    conflicts = set()
    progress = inputs.get('progress') or {}
    note = inputs.get('student_note') or ''
    note_done = re.search(r'\b(?:completed|finished)\s+(?:all\s+)?(?P<n>'+NUM+r')\s+(?:planned\s+)?(?:steps|tests|tasks|exercises|checks)\b',note,re.I)
    if note_done and progress.get('completed_units') is not None and number(note_done['n']) != progress['completed_units']:
        conflicts.add('progress')
        add('factual_grounding','facts.scenario_progress_conflict','inconclusive',{'structured':progress,'student_note':note}, 'Structured progress and note conflict. Neither is selected as the true outcome.', ['progress.completed_units','progress.planned_units','student_note'])
    note_times = list(TIME.finditer(note))
    for match in note_times:
        before = note[:match.start()].lower()[-45:]
        if re.search(r'\b(?:recorded|spent|took)\s*$',before) and inputs.get('reported_time'):
            claimed=number(match['number'])*{'second':1,'minute':60,'hour':3600}[match['unit'].lower().rstrip('s')]
            if claimed!=seconds(inputs['reported_time']):
                conflicts.add('reported_time')
                add('factual_grounding','facts.scenario_time_conflict','inconclusive',{'structured':inputs['reported_time'],'student_note':note},'Recorded time and note conflict; no source is silently preferred.', ['reported_time','student_note'])

    referenced = []
    for technology, pattern in TECHNOLOGIES.items():
        match = re.search(pattern,question,re.I)
        if not match: continue
        supports = {path:value for path,value in fields.items() if re.search(pattern,value,re.I)}
        prospective = bool(re.search(r'\b(?:learn|try|consider|explore|use)\s+(?:using\s+)?$',question[:match.start()],re.I) and hypothetical(question,match.start()))
        status = 'pass' if supports else 'inconclusive' if prospective else 'flag'
        add('contextual_grounding','context.technology_'+technology,status,{'technology':technology,'support':supports,'reference':match.group()},
            'Named technology is explicitly present in scenario evidence.' if supports else 'Prospective technology suggestion needs semantic relevance review.' if prospective else 'Named technology is not supported by the supplied scenario.', supports.keys(), semantic=prospective)
        if not supports and not prospective:
            add('factual_grounding','facts.technology_'+technology,'flag',{'technology':technology},'Unsupported technology premise; this does not establish that the technology could never be useful.', ['learning_goal','planned_activity','student_note'])
        referenced += list(supports)
    for pattern, path in [(r'\byour progress\b','progress'),
                          (r'\b(?:planned time|time estimate)\b','planned_time'),
                          (r'\b(?:time spent|reported time|recorded .*?minutes)\b','reported_time'),
                          (r'\byour (?:learning )?goal\b','learning_goal'),
                          (r'\byour (?:planned )?activity\b','planned_activity'),
                          (r'\b(?:previous|last) (?:reflection )?question\b','previous_question'),
                          (r'\b(?:control answer|your (?:recorded )?(?:correct|incorrect) answer)\b','control_results')]:
        match=re.search(pattern,question,re.I)
        if match:
            present=bool(inputs.get(path))
            clarification=not present and bool(re.search(r'\b(?:record|clarify|describe|what information)\b',question,re.I))
            add('contextual_grounding','context.reference_'+path,'pass' if present or clarification else 'inconclusive',{'field':path,'value':inputs.get(path),'reference':match.group()}, 'Explicit available-field reference or legitimate clarification of missing information; semantic relevance remains open.', [path], semantic=True)
            referenced.append(path)
    if not referenced:
        add('contextual_grounding','context.reference_unresolved','inconclusive',[], 'No explicit supported reference pattern. A paraphrase or generic question may still be relevant; lack of word overlap is not a violation.', semantic=True)

    # Recognized, asserted numeric claims. Hypothetical future alternatives are separate.
    handled_numbers = set()
    def compare_claim(rule, field, claimed, expected, claim, paths, conflict_key=None):
        status = 'inconclusive' if conflict_key in conflicts else 'flag' if expected is None or claimed!=expected else 'pass'
        add('factual_grounding',rule,status,{'claim':claim,'claimed_normalized':claimed,'recorded_normalized':expected,'field':field},
            'Conflicting scenario sources prevent resolution.' if conflict_key in conflicts else 'Claim has no recorded support.' if expected is None else 'Claim contradicts the recorded value.' if claimed!=expected else 'This specific claim matches the recorded value.', paths)
    for match in TIME.finditer(question):
        handled_numbers.add(match.span())
        if hypothetical(question,match.start()):
            add('factual_grounding','facts.hypothetical_time','inconclusive',{'text':match.group()}, 'A hypothetical duration is not treated as an actual recorded duration.', semantic=True)
            continue
        prefix=question[:match.start()].lower()[-100:]
        suffix=question[match.end():].lower()[:25]
        cues=list(re.finditer(r'\b(?:planned|plan|budget|allocated|reported|recorded|record|spent|spend|actual|took)\b',prefix))
        role=cues[-1].group() if cues else None
        if re.match(r'\s*(?:was |were )?(?:planned|budgeted)\b',suffix): role='planned'
        field='planned_time' if role in ['planned','plan','budget','allocated'] else 'reported_time' if role else None
        if not field:
            add('factual_grounding','facts.time_role_unresolved','inconclusive',{'text':match.group()},'Duration is explicit but its planned/reported role is unclear.', ['planned_time','reported_time'], semantic=True)
            continue
        claimed=number(match['number'])*{'second':1,'minute':60,'hour':3600}[match['unit'].lower().rstrip('s')]
        compare_claim('facts.numeric_'+field,field,claimed,seconds(inputs[field]) if inputs.get(field) else None,match.group(),[field,'student_note'],field)
    duration=re.search(r'\b(longer|shorter|more time|less time|same (?:amount of )?time)\b',question,re.I)
    actual_duration=re.search(r'\b(?:you (?:spent|took)|did you (?:spend|take)|(?:recorded|reported) time|activity took|did it take)\b',question,re.I)
    if duration and actual_duration and not hypothetical(question,duration.start()):
        a,b=inputs.get('reported_time'),inputs.get('planned_time')
        relation=None
        if a and b:
            left,right=seconds(a),seconds(b)
            relation=left>right if duration.group().lower() in ['longer','more time'] else left<right if duration.group().lower() in ['shorter','less time'] else left==right
        add('factual_grounding','facts.duration_comparison','inconclusive' if 'reported_time' in conflicts else 'flag' if relation is None or not relation else 'pass',
            {'claim':duration.group(),'reported_time':a,'planned_time':b},'Recognized asserted duration comparison uses normalized units; unknown evidence and source conflicts are explicit.', ['reported_time','planned_time','student_note'])
    fraction_spans=[]
    for match in FRACTION.finditer(question):
        fraction_spans.append(match.span())
        if hypothetical(question,match.start()): continue
        prefix=question[:match.start()].lower()[-70:]
        if not re.search(r'\b(?:completed|finished|recorded|record|done)\b',prefix): continue
        if not progress.get('unit') or normalized(progress['unit']).rstrip('s')!=normalized(match['unit']).rstrip('s'):
            add('factual_grounding','facts.progress_unit_unresolved','inconclusive',{'claim':match.group(),'recorded_unit':progress.get('unit')},'Quantities use unknown or different progress units; no conversion is invented.', ['progress.unit'], semantic=True)
            continue
        for group, field in [('completed','completed_units'),('planned','planned_units')]:
            compare_claim('facts.numeric_progress_'+field,'progress.'+field,number(match[group]),progress.get(field),match.group(),['progress.'+field,'student_note'],'progress')
    for match in QUANTITY.finditer(question):
        if any(a<=match.start()<b for a,b in fraction_spans) or hypothetical(question,match.start()): continue
        prefix=question[:match.start()].lower()[-70:]
        completed=re.search(r'\b(?:you|student)\b.*\b(?:completed|complete|finished|finish|recorded|record)\s+(?:all\s+|only\s+)?$',prefix)
        planned=re.search(r'\b(?:planned|planning|scheduled)\s+(?:all\s+)?$',prefix)
        field='completed_units' if completed else 'planned_units' if planned else None
        if field:
            if not progress.get('unit') or normalized(progress['unit']).rstrip('s')!=normalized(match['unit']).rstrip('s'):
                add('factual_grounding','facts.progress_unit_unresolved','inconclusive',{'claim':match.group(),'recorded_unit':progress.get('unit')},'Progress-unit equivalence cannot be established.', ['progress.unit'], semantic=True)
                continue
            compare_claim('facts.quantity_'+field,'progress.'+field,number(match['number']),progress.get(field),match.group(),['progress.'+field,'student_note'],'progress')
    completion=re.search(r'\byou (?:have )?(?:completed|finished) (?:all|the|your)|\bhow did you (?:complete|finish) all|\bafter completing (?:all|the)|\byour completed (?:task|activity)',question,re.I)
    if completion and not hypothetical(question,completion.start()):
        known=progress.get('planned_units') is not None and progress.get('completed_units') is not None and bool(progress.get('unit')) and progress['planned_units']>0
        status='inconclusive' if 'progress' in conflicts else 'flag' if not known or progress['completed_units']<progress['planned_units'] else 'pass'
        add('factual_grounding','facts.completed_task',status,{'claim':completion.group(),'progress':progress,'student_note':note},'Completion premise checked against recorded numeric progress; conflicting sources remain unresolved.', ['progress','student_note'])
    for assessment in ['correct','incorrect']:
        claim=re.search(r'\byour (?:recorded )?'+assessment+r' answer\b|\byou answered '+assessment+r'ly\b',question,re.I)
        if not claim or hypothetical(question,claim.start()): continue
        rows=[c for c in inputs.get('control_results') or [] if c.get('question') and c.get('student_answer') and normalized(c.get('recorded_assessment'))==assessment]
        add('factual_grounding','facts.control_'+assessment,'pass' if rows else 'flag',{'claim':claim.group(),'matching_recorded_answers':rows},'Only canonical recorded assessments with a question and student answer support this premise; inferred assessments are excluded.', ['control_results'])

    # Direct student premises, with conservative exemption for hypothetical wording.
    premise_rules = [
        ('performance',r'\b(?:you (?:fail(?:ed)?|succeeded)|your (?:failure|success))\b',r'\b(?:failed|succeeded|failure|success)\b'),
        ('emotion',r'\b(?:your (?:frustration|anxiety|anger)|you (?:felt|were|are) (?:frustrated|anxious|angry))\b',r'\b(?:frustrat\w*|anxious|anxiety|anger|angry)\b'),
        ('diagnosis',r'\b(?:you have (?:ADHD|autism|depression)|your (?:ADHD|autism|depression))\b',r'\b(?:ADHD|autism|depression)\b'),
        ('corrective_work',r'\b(?:you (?:fixed|corrected|overcame)|after (?:fixing|correcting))\b',r'\b(?:fixed|corrected|overcame)\b'),
        ('selection',r'^what led you to (?:select|choose)\b',r'\b(?:selected|chose|chosen)\b'),
    ]
    for name, pattern, support in premise_rules:
        match=re.search(pattern,question,re.I)
        if not match or hypothetical(question,match.start()): continue
        supported=bool(re.search(support,note,re.I)) and not re.search(r'\b(?:not|never|no)\s+(?:\w+\s+){0,2}'+support.replace(r'\b',''),note,re.I)
        status='pass' if supported and name!='diagnosis' else 'inconclusive' if supported else 'flag'
        add('factual_grounding','facts.premise_'+name,status,{'premise':match.group(),'student_note':note},'An explicit recorded note can support a limited premise; absence of evidence is not a statement that it never happened.', ['student_note'])
        if name in ['performance','emotion','diagnosis']:
            add('agency_wording','agency.premise_'+name,status,{'premise':match.group(),'student_note':note},'Potentially judgmental or diagnostic premise requires explicit evidence and semantic review.', ['student_note'], semantic=True)
    coercion=re.search(r'^(?:you must|you have to|why (?:didn.t|did not) you)\b|\byou should have\b|\byou are (?:lazy|stupid|incapable)\b',question,re.I)
    if coercion:
        add('agency_wording','agency.direct_judgment','flag',{'wording':coercion.group()},'Listed direct coercive/reproachful or ability-judgment wording detected; no broader tone inference is made.')
    else:
        add('agency_wording','agency.tone_unresolved','inconclusive',[], 'No listed direct judgment detected. Tone, agency and pedagogical appropriateness still need semantic review.', semantic=True)
    if not any(c['criterion_id']=='factual_grounding' for c in checks):
        add('factual_grounding','facts.no_recognized_claim','inconclusive',[], 'No recognized testable factual claim; this is not a correctness pass.', semantic=True)
    # Preserve numbers outside recognized roles as unresolved, not guessed facts.
    other_numbers=[m.group() for m in re.finditer(r'\b\d+(?:\.\d+)?\b',question) if not any(a<=m.start()<b for a,b in [x.span() for x in TIME.finditer(question)]+fraction_spans+[x.span() for x in QUANTITY.finditer(question)])]
    if other_numbers:
        add('factual_grounding','facts.other_numeric_references','inconclusive',{'numbers':other_numbers},'Unclassified quantities, code literals or port numbers require semantic interpretation; occurrence in context alone is not proof.', semantic=True)

    criteria={}
    for dimension in DIMENSIONS:
        relevant=[c for c in checks if c['criterion_id']==dimension]
        if dimension=='format':
            required=[c for c in relevant if c['rule_id'] not in ['format.language.v1','format.previous_nonrepetition.v1'] or c['status']=='flag']
            status='flag' if any(c['status']=='flag' for c in required) else 'inconclusive' if any(c['status']=='inconclusive' for c in required) else 'pass'
        else:
            status='flag' if any(c['status']=='flag' for c in relevant) else 'inconclusive' if any(c['status']=='inconclusive' for c in relevant) else 'pass' if relevant else 'inconclusive'
        criteria[dimension]={'criterion_id':dimension,'metric_version':VERSION,'status':status,
            'explanation':DEFINITIONS[dimension], 'evidence':relevant,
            'scenario_fields':sorted({p for c in relevant for p in c['scenario_fields']}),
            'rule_ids':[c['rule_id'] for c in relevant], 'deterministic':True,'requires_semantic_judgment':dimension!='format'}
    qtokens=tokens(question); ctokens=tokens(' '.join(fields.values()))
    return {'checks':checks,'criteria':criteria,'classification':classification,
            'measurements':{'word_count':len(words),'context_token_precision':len(qtokens&ctokens)/len(qtokens) if qtokens else None,
                            'shared_content_words':sorted(qtokens&ctokens),'format_pass':criteria['format']['status']=='pass',
                            'explicit_reference_fields':sorted(set(referenced))},
            'evidence_conflicts':sorted(conflicts),'review_state':'requires_review',
            'semantic_quality':{'status':'unreviewed','reason':'Deterministic indicators do not establish semantic quality.'}}
