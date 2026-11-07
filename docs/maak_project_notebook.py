"""Build the chronological, read-only project walkthrough from actual sources.

Run with Python; the builder itself needs only the standard library. Notebook
execution additionally requires a Python kernel with the project dependencies.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import textwrap
import uuid

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'docs' / 'Zelfregiekompas_projectopbouw_en_metrics.ipynb'
cells = []
source_manifest = {}


def markdown(value):
    cells.append({'cell_type':'markdown','id':uuid.uuid4().hex[:12],'metadata':{},'source':textwrap.dedent(value).strip()+'\n'})


def code(value):
    cells.append({'cell_type':'code','id':uuid.uuid4().hex[:12],'metadata':{},'source':textwrap.dedent(value).strip()+'\n','execution_count':None,'outputs':[]})


def snippet(path, symbol=None, start=None, end=None, limit=None):
    raw = (ROOT / path).read_bytes()
    source_manifest[path] = hashlib.sha256(raw).hexdigest()
    text = raw.decode('utf-8')
    lines = text.splitlines()
    if symbol:
        body = ast.parse(text).body
        for name in symbol.split('.'):
            node = next(n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
            body = node.body
        first,last = node.lineno,node.end_lineno
    else:
        first = next(i+1 for i,line in enumerate(lines) if start in line)
        last = next((i for i in range(first,len(lines)) if end and end in lines[i]),len(lines)) if end else len(lines)
    if limit: last = min(last,first+limit-1)
    excerpt = '\n'.join(lines[first-1:last])
    markdown(f'**Fragment uit `{path}`, regels {first}–{last}.** Dit is bestaande broncode, geen vervangende pseudocode.\n\n```python\n{excerpt}\n```')


markdown('''
# Van ICT-scenario naar onderbouwde beoordeling van een reflectievraag

## De opbouw van Zelfregiekompas Research Lab, stap voor stap

Deze notebook legt uit **hoe het project is opgebouwd, hoe de applicatie werkt
en hoe de vaste metrics zijn ontwikkeld**. De centrale onderzoeksvraag is welke
verschillen optreden tussen reflectievragen uit een **Fixed Question Bank**,
**RAG** en een **rechtstreeks aangestuurd LLM**.

De chronologie is een **logische bouw- en onderzoeksvolgorde**, gebaseerd op de
bestaande code en bewaarde v2/v3-rapporten. Het is geen verzonnen Git-commithistorie.
De beschreven onderzoeksbatch is uitgevoerd op 30 oktober 2026.

De notebook bevat echte bronfragmenten, kleine uitvoerbare demonstraties en
opgeslagen onderzoeksresultaten. **Geen enkele cel roept Ollama aan, start een
experiment, schrijft naar de onderzoeksdatabase of vervangt een bestaand rapport.**

### Hoe lees en gebruik je deze notebook?

Open hem in Jupyter of VS Code en voer de cellen van boven naar beneden uit.
Kies een Python-kernel met de projectdependencies, bij voorkeur de projectomgeving
`.venv`. Er zijn geen pandas- of matplotlib-installaties nodig. De codefragmenten
in Markdown laten de implementatie zien; de Python-cellen demonstreren het gedrag.

**Leesroute:** 1 onderzoeksvraag → 2 architectuur → 3 scenario's → 4 gecontroleerd
materiaal → 5 Fixed → 6 RAG → 7 direct LLM → 8 experimentuitvoering → 9 metrics v2
→ 10 audit → 11 metrics v3 → 12 gelijke beoordeling → 13 echte resultaten
→ 14 reproduceerbaarheid en verantwoorde conclusies.
''')

code('''
from pathlib import Path
import copy
import hashlib
import json
import sys
from collections import Counter

# Werkt zowel vanuit de projectroot als vanuit de map docs/.
ROOT = next(
    (p for p in [Path.cwd(), *Path.cwd().parents]
     if (p / 'backend' / 'schema.py').exists() and (p / 'docs').is_dir()),
    None,
)
if ROOT is None:
    raise RuntimeError('Open de notebook binnen de projectmap.')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import methods, script_evaluation
from backend.fixed_rules_v3 import score
from backend.schema import Inputs, prompt_inputs
import pydantic

def lees_json(relatief_pad):
    return json.loads((ROOT / relatief_pad).read_text(encoding='utf-8-sig'))

def toon_tabel(koppen, rijen):
    """Een eenvoudige tabel zonder extra analysebibliotheken."""
    rijen = [[str(waarde) for waarde in rij] for rij in rijen]
    breedtes = [max(len(str(kop)), *(len(r[i]) for r in rijen))
                for i, kop in enumerate(koppen)]
    print(' | '.join(str(kop).ljust(breedtes[i]) for i, kop in enumerate(koppen)))
    print('-+-'.join('-' * breedte for breedte in breedtes))
    for rij in rijen:
        print(' | '.join(waarde.ljust(breedtes[i]) for i, waarde in enumerate(rij)))

print('Projectroot:', ROOT)
print('Python:', sys.executable)
print('Pydantic:', pydantic.__version__)
print('Actuele vaste rubric:', script_evaluation.VERSION)
print('Deze notebook gebruikt alleen lokale code en opgeslagen bestanden.')
''')

markdown('''
## 1. Eerst het onderzoeksprobleem: wat willen we weten?

Een student wil bijvoorbeeld Python-functies leren en heeft twee van vier stappen
geregistreerd. De applicatie moet daarbij een reflectievraag **kiezen of opstellen**.
Het resultaat dat we onderzoeken is die vraag, niet het antwoord dat de student er
eventueel later op geeft.

Een passende vraag heeft meerdere aspecten:

| Aspect | Wat willen we inhoudelijk weten? |
| --- | --- |
| Reflectief karakter | Nodigt de vraag uit tot nadenken over leren, keuzes, aanpak of bewijs? |
| Context | Past zij bij het leerdoel en de concrete activiteit? |
| Feitelijke gronding | Kloppen de veronderstellingen met wat werkelijk is geregistreerd? |
| Duidelijkheid | Kan de student begrijpen waarop een antwoord wordt gevraagd? |
| Autonomie | Laat de formulering ruimte voor een eigen, niet-veroordeeld antwoord? |

Deze brede begrippen zijn het **onderzoeksconstruct**. Een script kan daarvan
slechts afgebakende onderdelen meten: de **operationalisatie**. Een goede
operationalisatie benoemt ook wat zij niet vaststelt.

De eerste ontwerpbeslissing is daarom om **materiaal maken**, **vragen verzamelen**
en **resultaten beoordelen** te scheiden. Zo wordt een gemaakte vraag niet vanzelf
als een goede vraag behandeld.
''')

markdown('''
## 2. Daarna de technische basis: een lokale onderzoeksapplicatie

```text
Onderzoeker
    ↓
React / TypeScript-interface
    ↓  /api
FastAPI-backend
    ├── onderzoeks- en versiebeheer ──→ SQLite
    ├── jobverwerking ──→ providerinterface ──→ lokale Ollama
    └── vaste beoordelingsscripts ──→ afzonderlijke evaluatierapporten
```

| Laag | Waarom zit deze in het project? |
| --- | --- |
| Frontend | Materiaal, instellingen, experimenten en bewijs inspecteerbaar maken. |
| API en schema's | Gegevens en handelingen controleren voordat zij worden verwerkt. |
| Onderzoekslogica | Versies, goedkeuringen, snapshots en experimentcondities vastleggen. |
| Eén achtergrondworker | Langdurige generatie uitvoeren en gedeeltelijke resultaten bewaren. |
| SQLite | Records lokaal en transactioneel opslaan. |
| Providerinterface | Modelcommunicatie scheiden van selectie, opslag en beoordeling. |
| Vaste evaluator | Dezelfde regels toepassen zonder een model als automatische beoordelaar. |

De hoofdwerkruimtes zijn **Scenarios**, **Question bank**, **Snapshots**,
**Experiments**, **Evaluation**, **Metrics**, **Models** en **Protocol & records**.
De vaste scripts kunnen lokaal op opgeslagen gegevens werken, ook zonder draaiende
webserver of Ollama. De volgende cellen demonstreren juist die leesroute.
''')
snippet('backend/store.py','Store.write')

markdown('''
De opslag gebruikt records met een type, ID en JSON-inhoud. Nieuwe vaste en
optionele semantische evaluaties mogen via deze schrijfroutine niet worden
overschreven. Dit is een applicatiebescherming: iemand met rechtstreekse toegang
tot het databasebestand heeft technisch meer mogelijkheden.
''')

markdown('''
## 3. Vervolgens de onderzoekseenheid: het ICT-scenario

Voordat we een methode vergelijken, moeten we exact vastleggen welke gegevens
die methode mag zien. Daarvoor is `Inputs` gemaakt. Een scenario kan onvolledig
zijn; onbekend is niet hetzelfde als nul, fout of succesvol.
''')
snippet('backend/schema.py','Inputs')
snippet('backend/schema.py','prompt_inputs')

code('''
voorbeeld = {
    'learning_goal': 'Understand Python functions',
    'planned_activity': 'Write and test a Python function',
    'progress': {'planned_units': 4, 'completed_units': 2, 'unit': 'steps'},
    'planned_time': {'value': 20, 'unit': 'minutes'},
    'reported_time': {'value': 35, 'unit': 'minutes'},
    'control_results': None,
    'student_note': 'I recorded two of four steps; the other steps are not complete.',
    'previous_question': None,
}
invoer = Inputs.model_validate(voorbeeld).model_dump()
print(json.dumps(prompt_inputs(invoer), indent=2, ensure_ascii=False))
''')

markdown('''
**Waarom deze expliciete velden?** Tijd en aantallen kunnen zo worden gecontroleerd
zonder ze uit vrije tekst te raden. Onderzoekslabels, categorieën, split en
reviewerfeedback staan buiten de generatie-invoer. Een AI-afgeleide beoordeling
van een controleantwoord mag geen geobserveerd studentfeit worden.

Een schema controleert de structuur, niet automatisch de waarheid. Twee getallen
kunnen technisch geldig zijn terwijl zij inhoudelijk botsen met een studentnotitie.
Dat wordt later als een conflict behandeld.
''')

code('''
# Demonstratie van de invoergrens: een afgeleid label verdwijnt uit modelinvoer.
met_afgeleid_label = copy.deepcopy(voorbeeld)
met_afgeleid_label['control_results'] = [{
    'question': 'What does double(3) return?',
    'student_answer': '6',
    'recorded_assessment': None,
    'ai_inferred_assessment': 'correct',
}]
toegestaan = prompt_inputs(met_afgeleid_label)
assert 'ai_inferred_assessment' not in toegestaan['control_results'][0]
assert toegestaan['control_results'][0]['recorded_assessment'] is None
print('Afgeleid label uitgesloten; geregistreerde beoordeling blijft onbekend.')
''')

markdown('''
## 4. Materiaal controleren en vastzetten vóór het experiment

Een vragenbank bevat de vraagtekst, toepassingsvoorwaarden, prioriteit en herkomst.
Nieuwe of gewijzigde scenario's en vragen worden als versies opgeslagen en vragen
controle. Een snapshot bevat de exacte goedgekeurde versies die in een experiment
worden gebruikt. Een expliciete experimentele bank mag voor ontwikkeling ook
onbeoordeelde versies bevatten, maar is geen gewone goedgekeurde bank.

Deze stap voorkomt dat een bankwijziging halverwege een experiment de vergelijking
ongemerkt verandert. Goedkeuring registreert een handeling en reviewer-ID; zij
bewijst niet vanzelf een onafhankelijke menselijke inhoudsvalidatie.
''')
snippet('backend/research.py','Research.snapshot',limit=24)

code('''
# Dit zijn de werkelijk gebruikte, opgeslagen snapshots; geen nieuwe databaseactie.
bank_snapshot = lees_json('docs/final-test-20261030/bank-snapshot.json')
dataset_snapshot = lees_json('docs/final-test-20261030/dataset-snapshot.json')
print('Bankvragen in snapshot:', len(bank_snapshot['records']))
print('Scenario’s in snapshot:', len(dataset_snapshot['records']))
print('Bank snapshot-ID:', bank_snapshot['id'])
print('Dataset snapshot-ID:', dataset_snapshot['id'])
print('Goedkeuringsstatussen bank:', dict(Counter(q['review_status'] for q in bank_snapshot['records'])))
print('Goedkeuringsstatussen scenario’s:', dict(Counter(s['review_status'] for s in dataset_snapshot['records'])))
''')

markdown('''
**Herkomst van deze batch:** lokale generatie leverde ongeldige bankvoorwaarden
en foutieve controleantwoorden op. De uiteindelijke 32 bankvragen en 36 scenario's
zijn daarom door Codex opgesteld/gecorrigeerd en vóór verzameling kort gecontroleerd.
De oorspronkelijke pogingen en versies zijn behouden. Dit is synthetisch
ontwikkelmateriaal met geassisteerde controle, geen onafhankelijk menselijk
gevalideerde testset.
''')

markdown('''
## 5. De eerste methode: Fixed Question Bank

Fixed selecteert bestaande tekst. De voorwaarden worden vergeleken met de
scenario-invoer. Bij meerdere geschikte specifieke vragen wordt gesorteerd op
prioriteit, genormaliseerde specificiteit en stabiele vraag-ID. Zonder specifieke
match kan een geschikte onvoorwaardelijke fallback worden gekozen.

De keuze gebruikt geen LLM. Deterministische selectie is echter nog geen bewijs
van inhoudelijke passendheid: een te brede voorwaarde of verkeerde prioriteit kan
een minder geschikte vraag opleveren.
''')
snippet('backend/methods.py','fixed')

code('''
# Kleine demonstratiebank, uitdrukkelijk geen vervanging van de echte onderzoeksbank.
demo_bank = [
    {'id':'demo-python-v1', 'question_id':'demo-python',
     'text':'Which Python approach would you practice next?',
     'conditions':{'contains':{'learning_goal':'Python'}}, 'priority':20},
    {'id':'demo-fallback-v1', 'question_id':'demo-fallback',
     'text':'What would you like to reflect on about this ICT activity?',
     'conditions':{}, 'priority':0},
]
fixed_trace = methods.prepare('fixed', voorbeeld, demo_bank)
print('Gekozen vraag:', fixed_trace['question'])
print('Terugval gebruikt:', fixed_trace['fallback'])
print('Onderbouwing:', fixed_trace['winning_reason'])
assert fixed_trace['selected_version_id'] == 'demo-python-v1'
''')

markdown('''
## 6. De tweede methode: RAG met lexicale retrieval

RAG gebruikt bankvragen als voorbeelden voor een nieuwe generatie. In dit project
is retrieval gebaseerd op **TF-IDF en cosinusvergelijking**, niet op embeddings.
Eerst worden alleen toepasselijke bankvragen toegelaten. Vervolgens worden hun
teksten gerangschikt ten opzichte van de tekstwaarden uit het scenario.

De standaardinstelling is maximaal drie suggesties en een minimumscore van 0,12.
Geen voldoende match wordt expliciet vastgelegd. Prioriteit uit Fixed bepaalt
deze ranking niet. De retrievalscore zegt iets over een lexicale match, **niet
over de kwaliteit van de uiteindelijke reflectievraag**.
''')
snippet('backend/methods.py','retrieve')

code('''
rag_trace = methods.prepare('rag', voorbeeld, demo_bank, top_k=3)
print('Retrievalstatus:', rag_trace['retrieval_status'])
print('Opgehaalde suggesties:', json.dumps(rag_trace['retrieved'], indent=2))
print('Promptvelden:', sorted(json.loads(rag_trace['prompt'])))
print('Dit stelt alleen de prompt samen; er wordt geen model aangeroepen.')
''')

markdown('''
## 7. De derde methode: direct, begrensd LLM

De methode `constrained` gebruikt het scenario en de algemene instructies zonder
bankinhoud. RAG en direct LLM delen de algemene generatiebeperkingen: één korte
Engelse reflectievraag, maximaal 40 woorden, geen verzonnen succes, emoties of
omstandigheden, en behoud van autonomie.

RAG krijgt opzettelijk extra suggesties. De prompts zijn daarom niet volledig
identiek; die extra retrievalcontext is juist onderdeel van het methodeonderzoek.
''')
snippet('backend/methods.py','prepare',limit=22)

code('''
llm_trace = methods.prepare('constrained', voorbeeld, [])
rag_data = json.loads(rag_trace['prompt'])
llm_data = json.loads(llm_trace['prompt'])
assert rag_trace['system_prompt'] == llm_trace['system_prompt']
assert rag_data['scenario_inputs'] == llm_data['scenario_inputs']
assert set(llm_data) == {'scenario_inputs'}
print('Algemene instructie gelijk: ja')
print('Scenario-invoer gelijk: ja')
print('Extra RAG-velden:', sorted(set(rag_data) - set(llm_data)))
print('Aantal modelaanroepen in deze demonstratie: 0')
''')

markdown('''
## 8. Van losse methoden naar een gecontroleerd experiment

Een experiment koppelt iedere case aan een exacte scenarioversie, methode, model,
instellingen en herhaling. Een achtergrondworker bewaart vragen en fouten per
uitvoerrecord. De gebruikte modeldigest wordt vastgezet, zodat een gewijzigd model
niet ongemerkt dezelfde onderzoeksconditie kan blijven voorstellen.

Een preflight voert vooraf een kleine echte controle via de onderzoeksroute uit.
Dat is geen kwaliteitsvalidatie. In de onderstaande cellen lezen we alleen de
opgeslagen preflight en het exportbestand; we voeren hem niet opnieuw uit.

Voor methodeonderzoek houden we RAG en direct LLM bij hetzelfde model en dezelfde
instellingen. Voor modelonderzoek vergelijken we verschillende modellen binnen
dezelfde methode. Fixed heeft geen generator en wordt niet per generator nog
eens als een nieuwe methode geteld.
''')
snippet('backend/jobs.py','Jobs._pin_models')

code('''
experiment = lees_json('docs/final-test-20261030/experiment-export.json')
outputs = experiment['outputs']
preflight = lees_json('docs/final-test-20261030/preflight.json')
config = experiment['job']['config']

toon_tabel(['Onderdeel', 'Opgeslagen waarde'], [
    ['Experiment', experiment['job']['name']],
    ['Scenario’s', len(dataset_snapshot['records'])],
    ['Bankvragen', len(bank_snapshot['records'])],
    ['Methoden', ', '.join(config['methods'])],
    ['Generator', ', '.join(config['models'])],
    ['Herhalingen', config['repetitions']],
    ['Geplande outputs', len(outputs)],
    ['Preflight geslaagd', preflight['passed']],
    ['Inline AI-beoordeling', config['ai_control']],
])
print('\\nGeneratie-instellingen:', json.dumps(config['settings'], indent=2))
print('Uitvoerstatussen:', dict(Counter(o['status'] for o in outputs)))
assert len(outputs) == 108
assert Counter(o['method'] for o in outputs) == {'fixed':36, 'rag':36, 'constrained':36}
''')

markdown('''
De batch bevat 36 synthetische scenario's: zes ICT-onderwerpen met zes situaties.
Bij één generator, drie methoden en één herhaling ontstaan 108 geplande resultaten.
Daarvan zijn 107 technisch geldig en heeft één RAG-resultaat een formaatfout.
Deze fout blijft bewaard en wordt niet selectief weggepoetst door een nieuwe poging.

Het historische validatierecord noemt ook backend- en browsertests. Die hebben
softwaregedrag getest; zij bewijzen geen betere leeropbrengst voor studenten.
''')

markdown('''
## 9. De eerste operationalisatie: waarom metrics v2 ontstonden

De eerste vaste rubric probeerde drie bredere begrippen meetbaar te maken:
`usefulness`, `context_fit` en `correctness`.

| Bedoeld begrip | V2-regel | Risico bij interpretatie |
| --- | --- | --- |
| Bruikbaarheid als reflectie | Herkende reflectiewoorden, formaat, geen bepaalde drukwoorden. | Een trefwoord kan ook in een kennisvraag staan. |
| Contextuele passendheid | ICT-context, technologieën en gedeelde inhoudswoorden. | Overlap is geen bewijs van semantische relevantie. |
| Kloppende aannames | Enkele patronen voor afronding, onjuiste antwoorden en technologie. | Niet herkende aannames blijven buiten beeld. |

De bedoeling was consequent beoordelen. De audit liet zien waarom **consequent**
en **valide** verschillende eisen zijn: een regel kan altijd hetzelfde doen en
toch een te ruim begrip suggereren.
''')
snippet('backend/legacy_metrics/v2/script_evaluation.py',start='REFLECTION =',limit=1)
snippet('backend/legacy_metrics/v2/script_evaluation.py','evaluate_pair.criterion')

code('''
v2 = lees_json('docs/final-test-20261030/fixed-metrics.json')
toon_tabel(['V2-criterium', 'Pass', 'Flag', 'Onbeslist', 'Beslisdekking'], [
    [naam, c['pass'], c['flag'], c['inconclusive'], f"{c['decision_coverage']:.1%}"]
    for naam, c in v2['criteria'].items()
])
print('\\nV2-formaatpercentage:', f"{v2['format_pass_rate']:.1%}")
print('Let op: v2 gebruikte hiervoor alleen de reeds toegelaten outputs.')
''')

markdown('''
## 10. Daarna de audit: welke problemen zijn daadwerkelijk gevonden?

1. **Valse reflectie-indicatie.** `plan` in een SQL *query plan* kon als
   reflectiewoord tellen. Dat bewijst geen reflectie op een leerproces.
2. **Gemiste feitenclaim.** Eén modelvraag noemde 15 geregistreerde minuten,
   terwijl het scenario 35 minuten bevatte. V2 had daarvoor geen tijdclaimcontrole.
3. **Te ruime contextinterpretatie.** Eén gedeeld woord kon voldoende zijn voor
   een context-pass. Een parafrase kon juist onbeslist blijven.
4. **Onvolledige formaatnoemer.** De ongeldige respons werd uitgesloten van het
   formaatpercentage, waardoor dat 100% werd terwijl één van 108 outputs ongeldig was.
5. **Rapporttoegang.** De hoofdverwijzing naar een evaluatie kon worden vervangen;
   versiegewijze toegang moest sterker en duidelijker worden.

Methodeblindheid werkte wél. Veel `inconclusive`-uitkomsten waren bovendien een
eerlijke beperking, geen bewijs dat al die vragen slecht waren.

We hebben dus geen regels aangepast om een methode hogere cijfers te geven.
We hebben eerst vastgesteld **welke claim een regel verantwoord kan doen**.
''')

code('''
# Een werkelijk opgeslagen geval, geen nieuw verzonnen modelresultaat.
tijd_output = next(o for o in outputs if o['id'] == 'out_aba96dc4990346ce')
oud_geval = next(p for p in v2['pairs'] if p['output_id'] == tijd_output['id'])
print('Opgeslagen vraag:', tijd_output['question'])
print('Gerapporteerde tijd:', tijd_output['inputs']['reported_time'])
print('Oude feitelijke beoordeling:', oud_geval['criteria']['correctness']['status'])
''')

markdown('''
## 11. De herziening: van brede kwaliteitsetiketten naar afgebakende v3-indicatoren

De vijf v3-dimensies staan hieronder. Diversiteit blijft een apart beschrijvend
onderdeel en wordt geen zesde kwaliteitsoordeel.

| Dimensie | Wat is geoperationaliseerd? | Wat blijft open? |
| --- | --- | --- |
| `format` | Punctuatie, lengte, regelvorm, herkenbare extra respons, exacte vorige-vraagherhaling. | Semantisch tellen van vragen en betrouwbare taalidentificatie. |
| `reflection_structure` | Herkenbare leerlinggerichte vraagpatronen versus technische kennisstructuren. | Echte reflectie en pedagogische meerwaarde. |
| `contextual_grounding` | Expliciete ondersteunde veld- en technologieverwijzingen. | Volledige betekenis, relevantie en parafrases. |
| `factual_grounding` | Herkende claims over tijd, aantallen, voortgang, controleantwoorden en prestaties. | Arbitrary code-/wereldkennis en niet-herkende aannames. |
| `agency_wording` | Herkenbare druk, oordelen en onbewezen persoonlijke aannames. | Volledige tooninterpretatie en pedagogische gepastheid. |

De statussen krijgen een afgebakende betekenis:

- **pass:** de specifieke regel wordt ondersteund; geen totale kwaliteitsgoedkeuring.
- **flag:** een specifieke overtreding is gedetecteerd; geen oordeel dat ieder aspect fout is.
- **inconclusive:** de gegevens of regels geven geen uitsluitsel; geen pass of afkeuring.
- **skipped:** inhoudelijke beoordeling is niet mogelijk, bijvoorbeeld door een uitvoeringsfout.

`requires_review` is daarnaast een workflowstatus. Een mechanisch geldige vraag
kan nog steeds inhoudelijke beoordeling nodig hebben.
''')
snippet('backend/fixed_rules_v3.py','score.add')

markdown('''
Dit resultaatobject maakt een signaal controleerbaar: we zien welke regel iets
vaststelt, op basis van welke velden en met welke interpretatiegrens. Dat vervangt
een ondoorzichtig totaalcijfer door onderbouwde afzonderlijke metingen.
''')

markdown('''
### 11.1 Reflectiestructuur: de zin doet ertoe

V3 kijkt bij herkenbare gevallen naar leerlinggerichte zinsstructuur, niet alleen
naar losse woorden. Een technische kennisvraag kan inhoudelijk bij ICT passen en
toch geen reflectievraag zijn. Een herkend reflectiepatroon bewijst nog steeds
geen leerwinst.
''')
snippet('backend/fixed_rules_v3.py',start='    # Recognize syntax',end='    # Conflicts')

code('''
vragen = [
    'What is the default TCP port for HTTPS?',
    'What is one possible reason why the SQL query plan changed?',
    'What would you record about your progress to help you plan your next ICT learning step?',
]
toon_tabel(['Vraag', 'Structuur', 'Regelstatus'], [
    [vraag, (r := score(vraag, voorbeeld))['classification'],
     r['criteria']['reflection_structure']['status']]
    for vraag in vragen
])
''')

markdown('''
### 11.2 Feiten: tijd normaliseren en beweringen onderscheiden van opties

Een tijdclaim wordt vergeleken met het passende gestructureerde veld. Hiervoor
worden seconden, minuten en uren naar dezelfde eenheid omgerekend. De rol van de
claim — gepland of gerapporteerd — moet ook herkenbaar zijn.

Een toekomstige keuze van 15 minuten is iets anders dan doen alsof eerder
15 minuten is geregistreerd. Ook een hypothetisch klinkende hoofdvraag kan nog
een onjuiste feitelijke premisse bevatten.
''')
snippet('backend/fixed_rules_v3.py','seconds')
snippet('backend/fixed_rules_v3.py','hypothetical')
snippet('backend/fixed_rules_v3.py',start='    for match in TIME.finditer(question):',end='    duration=re.search')

code('''
tijdvragen = [
    'Why did you spend only 15 minutes on this activity?',
    'Why did you record 2100 seconds?',
    'Could you spend 15 minutes on practice next time?',
    'What might explain why you recorded 15 minutes?',
]
for vraag in tijdvragen:
    r = score(vraag, voorbeeld)
    relevante_checks = [c for c in r['checks'] if c['rule_id'].startswith(
        ('facts.numeric_', 'facts.hypothetical_time'))]
    print('\\nVraag:', vraag)
    for c in relevante_checks:
        print(' ', c['rule_id'], '→', c['status'])
        print(' ', c['evidence'])
''')

markdown('''
### 11.3 Een conflict is geen uitnodiging om waarheid te verzinnen

Als de studentnotitie zegt dat vier stappen klaar zijn en de gestructureerde
registratie twee van vier noemt, bewaren we beide bronnen. Een claim over
afronding wordt dan onbeslist in plaats van dat één bron automatisch wint.
''')
snippet('backend/fixed_rules_v3.py',start='    # Conflicts are evidence properties.',end='    note_times =')

code('''
tegenstrijdig = copy.deepcopy(voorbeeld)
tegenstrijdig['student_note'] = 'I completed all four planned steps.'
conflict = score('How did you complete all four steps?', tegenstrijdig)
print('Conflicterende bronnen:', conflict['evidence_conflicts'])
print('Feitelijke dimensie:', conflict['criteria']['factual_grounding']['status'])
for c in conflict['checks']:
    if c['rule_id'].startswith(('facts.scenario_progress_conflict', 'facts.completed_task')):
        print(c['rule_id'], c['status'], c['evidence'])
assert conflict['criteria']['factual_grounding']['status'] == 'inconclusive'
''')

markdown('''
### 11.4 Context en autonomie: herkenning zonder te ruime conclusies

Een ontbrekende Python-verwijzing in een scenario over encryptie kan een
onondersteunde technologiepremisse opleveren. Maar geen woordoverlap is geen
bewijs van irrelevantie. Een vraag naar een mogelijke toekomstige aanpak kan
bovendien een legitieme optie zijn, in plaats van een claim over uitgevoerde stappen.

Evenzo is onbekende voortgang geen bewijs van falen. Geen gevonden drukwoord is
op zijn beurt geen bewijs dat de volledige toon goed is. Daarom blijft brede
inhoudelijke interpretatie afzonderlijk zichtbaar.
''')

code('''
grensgevallen = [
    ('Onondersteunde technologie',
     'What is a common approach for inspecting the encryption configuration in Python?',
     {'learning_goal':'Inspect encryption', 'planned_activity':'Inspect a local network service'}),
    ('Onbewezen falen', 'Why did you fail to complete the activity?',
     {**voorbeeld, 'progress':None}),
    ('Mogelijk relevante parafrase', 'Which approach would you revisit?',
     {'learning_goal':'Design data storage', 'planned_activity':'Sketch tables'}),
]
for label, vraag, context in grensgevallen:
    r = score(vraag, context)
    print('\\n', label)
    print({k:c['status'] for k,c in r['criteria'].items()})
    print('Semantische review:', r['review_state'])
''')

markdown('''
## 12. Dezelfde regels voor alle drie de methoden

De inhoudelijke scorer krijgt alleen de vraagtekst en toegestane scenario-invoer.
Pas nadat het resultaat is berekend, worden methode, generator en onderzoeksconditie
toegevoegd voor de rapportage. Bankprioriteit, retrievalscore en eerdere labels
mogen dus geen voordeel geven bij beoordeling.
''')
snippet('backend/script_evaluation.py','evaluate_pair',limit=24)
snippet('backend/script_evaluation.py','evaluate',limit=10)

code('''
basis_output = {
    'id':'demo-uitvoer', 'version':1, 'scenario_version_id':'demo-scenario-v1',
    'status':'completed', 'inputs':voorbeeld,
    'question':'Which Python approach would you practice next?',
}
referentie = script_evaluation.evaluate_pair(basis_output)
for methode in ['fixed', 'rag', 'constrained']:
    met_herkomst = {**basis_output, 'method':methode, 'model':'ander-model',
                   'priority':999, 'origin':'vooraf goedgekeurd',
                   'trace':{'retrieved':[{'score':1.0}], 'conditions':{'missing':['progress']}},
                   'research_labels':{'verwachte_kwaliteit':'hoog'}}
    assert script_evaluation.evaluate_pair(met_herkomst) == referentie
print('Dezelfde vraag en context krijgen exact hetzelfde resultaat voor Fixed, RAG en LLM.')
''')

markdown('''
### Hergebruik is geen individuele kwaliteitsfout

Een bank is ontworpen om vragen te hergebruiken. We beschrijven duplicaten en
hergebruik over scenario's, maar geven een vraag daarvoor geen foutlabel. Ook
een unieke modelzin verdient niet automatisch een kwaliteitsbonus.
''')

code('''
hergebruik = [
    {**basis_output, 'id':f'demo-{n}', 'scenario_version_id':f'demo-scenario-{n}',
     'method':'fixed', 'repetition':1}
    for n in range(3)
]
beschrijvend = script_evaluation.evaluate(hergebruik)
print('Unieke genormaliseerde vragen:', beschrijvend['unique_question_count'])
print('Hergebruik over scenario’s:', beschrijvend['diversity']['cross_scenario_reuse_groups'])
print('Herhalingsaandeel:', f"{beschrijvend['diversity']['repetition_rate']:.1%}")
assert beschrijvend['pairs'][0]['criteria'] == beschrijvend['pairs'][1]['criteria']
print('De individuele regelbeoordeling blijft gelijk.')
''')

markdown('''
## 13. Nu de echte onderzoeksuitvoer: wat veranderde van v2 naar v3?

We laden de twee bewaarde rapporten. Er is voor deze herbeoordeling geen vraag
opnieuw gegenereerd en geen AI-beoordelaar gebruikt. V3 is retrospectief naar
aanleiding van de audit ontworpen; het is dus geen vooraf onafhankelijk
gevalideerd eindmeetinstrument.

De constructen zijn veranderd. De volgende cijfers zijn geen bewijs dat dezelfde
modeluitvoer ineens beter of slechter is geworden.
''')

code('''
v3 = lees_json('docs/fixed-metrics-v3/fixed-metrics-v3.json')
toon_tabel(['V3-dimensie', 'Pass', 'Flag', 'Onbeslist', 'Overgeslagen', 'Beslisdekking'], [
    [naam, c['pass'], c['flag'], c['inconclusive'], c['skipped'],
     f"{c['decision_coverage']:.1%}" if c['decision_coverage'] is not None else 'n.v.t.']
    for naam,c in v3['criteria'].items()
])
op = v3['operational']
print('\\nFormaat in v3:', op['format_compliant'], '/', op['format_checked'],
      '=', f"{op['format_rate_per_present']:.2%}")
print('Succesvolle outputs:', op['successful'], '/', op['planned'])
print('Uitvoeringsfouten:', op['execution_failures'])
''')

markdown('''
### Waarom de noemer ertoe doet

V2 rapporteerde 100% formaatcompliance over de 107 al toegelaten vragen.
V3 onderzoekt ook de niet-lege ongeldige respons: 107 van 108, oftewel ongeveer
99,07%. Het gaat om dezelfde oorspronkelijke uitvoer, met een duidelijker noemer.

Beslisdekking is `(pass + flag) / beoordeeld`. Een hoog pass-aandeel onder alleen
beslisbare gevallen is geen algemene kwaliteitsmaat als bijna alles onbeslist is.
De rapportage toont daarom aantallen, onzekerheid en noemers afzonderlijk.
''')

code('''
oud_per_id = {p['output_id']:p for p in v2['pairs']}
nieuw_per_id = {p['output_id']:p for p in v3['pairs']}
vergelijk_ids = [
    ('out_41b4b6eb41cd46bb', 'Query plan is geen reflectiebewijs'),
    ('out_aba96dc4990346ce', '15 minuten tegenover 35 geregistreerd'),
    ('out_5d521bdee31846ad', 'Technische kennisvraag'),
    ('out_bcea91b7df814590', 'Vraag met aanhalingstekens'),
]
for output_id, reden in vergelijk_ids:
    oud, nieuw = oud_per_id[output_id], nieuw_per_id[output_id]
    print('\\nGeval:', reden)
    print('Vraag:', nieuw['question'])
    print('V2:', {k:c['status'] for k,c in oud['criteria'].items()})
    print('V3:', {k:c['status'] for k,c in nieuw['criteria'].items()})
''')

markdown('''
### Vergelijking per methode, met dezelfde scenario's

We vergelijken exact dezelfde scenarioversies en herhalingen. De kennisstructuur-
flags betekenen dat een herkenbaar kennisvraagpatroon is gevonden; zij zijn geen
totale afwijzing van ieder inhoudelijk aspect van die vraag.
''')

code('''
def drie_statussen(c):
    return f"{c['pass']} / {c['flag']} / {c['inconclusive']}"

toon_tabel(
    ['Methode', 'Succes/gepland', 'Structuur: pass/flag/?', 'Feiten: pass/flag/?', 'Unieke vragen'],
    [[g['method'], f"{g['evaluated']}/{g['total']}",
      drie_statussen(g['criteria']['reflection_structure']),
      drie_statussen(g['criteria']['factual_grounding']),
      g['unique_question_count']]
     for g in v3['by_condition']],
)
print('\\nGedeelde scenario/herhaling-combinaties:', v3['comparison']['common_scenario_repetitions'])
print('Iedere conditie dezelfde cases:', v3['comparison']['same_case_sets'])
assert v3['comparison']['common_scenario_repetitions'] == 36
''')

markdown('''
**Verantwoorde interpretatie:** in deze synthetische ontwikkelset levert de
gecontroleerde bank vaker een herkenbare reflectiestructuur. RAG en direct LLM
leveren ook veel herkenbare kennisvragen. De feitelijke dimensie en agency blijven
vaak onbeslist. Er wordt geen totaalscore gemiddeld en geen algemeen beste
architectuur aangewezen.

We hebben één model en één herhaling gebruikt. Deze batch bewijst dus geen
algemene modelrangorde, representativiteit voor alle studenten of hogere leerwinst.
Voor een sterkere inhoudelijke conclusie zijn onafhankelijke deskundige
beoordelingen en vooraf vastgelegde validatie-/testcases nodig.
''')

markdown('''
## 14. Tenslotte: reproduceerbaarheid en de grens van het oordeel

Een scriptmeting moet opnieuw uitvoerbaar zijn op dezelfde opgeslagen gegevens.
Daarvoor bewaart het project rubric- en regelversies, inputhashes, implementatiehashes
en onafhankelijke rapporten. De onderstaande bron laat zien dat `save` een nieuw
record toevoegt in plaats van de oorspronkelijke experimentuitvoer te herschrijven.
**We tonen die functie, maar roepen haar in deze notebook niet aan.**
''')
snippet('backend/script_evaluation.py','implementation_hash')
snippet('backend/script_evaluation.py','save')

code('''
# Lees-only controle: past de huidige implementatie nog bij het bewaarde v3-rapport?
huidige_hash = script_evaluation.implementation_hash()
print('Opgeslagen implementatiehash:', v3['implementation_hash'])
print('Huidige implementatiehash:   ', huidige_hash)

if huidige_hash == v3['implementation_hash']:
    opnieuw = script_evaluation.evaluate(outputs)  # alleen berekenen, niets opslaan
    vaste_inhoud = {k:v for k,v in v3.items()
                   if k not in ['id','job_id','created_at','dataset_snapshot_id','bank_snapshot_id']}
    assert opnieuw == vaste_inhoud
    print('V3 exact gereproduceerd: ja; geen database gewijzigd.')
else:
    print('Broncode gewijzigd: dit is niet meer dezelfde implementatie. Geen exacte reproductie geclaimd.')

from backend.legacy_metrics.v2.script_evaluation import evaluate as beoordeel_met_gearchiveerde_v2
oude_reproductie = beoordeel_met_gearchiveerde_v2(outputs)
assert oude_reproductie == {k:v for k,v in v2.items() if k not in ['id','job_id','created_at']}
print('V2 met gearchiveerde bron exact gereproduceerd: ja.')
''')

markdown('''
### Hoe uitleggen of een gekozen vraag daadwerkelijk goed is?

De meest nauwkeurige conclusie bestaat uit drie lagen:

1. **Wat is mechanisch vastgesteld?** Bijvoorbeeld één vraagteken, de woordlimiet
   en geen exacte vorige-vraagherhaling.
2. **Wat ondersteunen of weerspreken de gegevens?** Bijvoorbeeld een ondersteunde
   technologieverwijzing of juist een onjuiste tijdclaim, met expliciet bewijs.
3. **Wat blijft een inhoudelijk oordeel?** Of de student werkelijk tot zinvolle
   reflectie wordt uitgenodigd, hoe goed de vraag wordt begrepen en welke
   pedagogische waarde zij heeft.

Een passende onderzoeksformulering is:

> Deze vraag voldoet aan de gecontroleerde vormregels en vertoont een herkenbaar
> reflectiepatroon. De herkende aannames zijn met het scenario vergeleken.
> Niet alle semantische eigenschappen zijn vastgesteld; volledige pedagogische
> passendheid volgt niet automatisch uit deze regeluitkomsten.

De bestaande menselijke review kan een inhoudelijk oordeel vastleggen. Er is ook
een afzonderlijke optionele lokale AI-laag met zes geankerde schattingen, standaard
uitgeschakeld. Die schattingen zijn geen grondwaarheid en wijzigen de vaste metrics
niet. Deze notebook gebruikt geen van beide beoordelaars om nieuwe labels te maken.

### Responsible AI en onderzoeksverantwoording

De opbouw ondersteunt beperkte modelinvoer, lokale verwerking, inspecteerbare
keuzes, bewaarde fouten, methodeblindheid en zichtbare onzekerheid. Een reviewer-ID
is geen identiteitscontrole; lokale opslag is geen automatische anonimisering;
methodeblindheid bewijst geen fairness voor studentgroepen. Voor die bredere claims
zijn aanvullende afspraken en validatie nodig.

De historische v3-validatie vermeldt 203 backendtests en drie browsertests. Deze
notebook herhaalt die volledige testsets niet: de uitvoer hieronder leest het
vastgelegde validatierecord. De notebook heeft eigen demonstraties en asserts.
''')

code('''
validatie = lees_json('docs/fixed-metrics-v3/validation.json')
print('Eerder vastgelegde softwarevalidatie:', json.dumps(validatie, indent=2))
print('\\nConclusie: vaste regels leveren reproduceerbaar bewijs over afgebakende eigenschappen,')
print('maar zijn geen zelfstandig bewijs van de volledige pedagogische kwaliteit van een vraag.')
''')

markdown('''
## Verder lezen en gebruiken in een toelichting

- [Totaaldocument architectuur, Responsible AI en onderzoek](APPLICATIE_ARCHITECTUUR_RESPONSIBLE_AI_EN_ONDERZOEK.md)
- [Audit van v2](fixed-metrics-v3/AUDIT.md)
- [Definities en beperkingen van v3](fixed-metrics-v3/PROTOCOL.md)
- [Werkelijke vergelijking v2–v3](fixed-metrics-v3/COMPARISON.md)
- [Oorspronkelijk testprotocol](final-test-20261030/protocol.json)
- [Oorspronkelijk experimentexport](final-test-20261030/experiment-export.json)

De codefragmenten in deze notebook zijn bij het maken uit de bronbestanden gehaald.
De bestandsidentiteiten zijn opgenomen in de notebookmetadata (`project_sources`).
Bij latere codewijzigingen beschrijven deze vastgelegde fragmenten de toenmalige
implementatie; de hashes helpen dat verschil zichtbaar maken.

**Vervolgonderzoek:** bevries de rubric vóór een nieuwe bevestigende test, vergelijk
modellen binnen dezelfde methode, neem meerdere seeds/herhalingen waar zinvol en
valideer inhoudelijke passendheid met onafhankelijke deskundigen. Optimaliseer
meetregels niet achteraf om een voorkeursmethode te laten winnen.
''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=TARGET)
    parser.add_argument('--overwrite',action='store_true')
    args = parser.parse_args()
    if args.output.exists() and not args.overwrite:
        parser.error('Notebook already exists; use a new filename or explicitly pass --overwrite.')
    notebook = {
        'nbformat':4,'nbformat_minor':5,
        'metadata':{
            'kernelspec':{'display_name':'Python 3 (project .venv)','language':'python','name':'python3'},
            'language_info':{'name':'python','file_extension':'.py','mimetype':'text/x-python'},
            'project_sources':source_manifest,
            'project_walkthrough':{'language':'nl','chronology':'logical build sequence; no invented commit history',
                                   'execution_policy':'read-only; no model calls, database writes or experiment creation'},
        },
        'cells':cells,
    }
    args.output.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(f'Notebook created: {args.output}')
    print(f'{len(cells)} cells, {sum(c["cell_type"]=="code" for c in cells)} executable Python cells')


if __name__=='__main__':
    main()
