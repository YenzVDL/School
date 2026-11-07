# Audit vóór implementatie van rubric v3

Onderzocht: `script_evaluation.evaluate_pair`, zijn interne `criterion`-functie, `aggregate`, `save` en `report`; `question_metrics.assess`; scenario-/vraagschema's, selectie/generatie, exports, opslag, Evaluation en regressietests.

## Bevestigde fouten en te ruime interpretaties

- `REFLECTION` herkent `plan` en `planned` zonder zinsstructuur. Daardoor kan een technische vraag over een SQL query plan als `usefulness: pass` eindigen. Een trefwoord bewijst geen reflectie.
- Feitencontrole herkent slechts enkele completion/incorrect-answer-patronen en technologieën. De werkelijk waargenomen 15-minutenclaim tegenover 35 geregistreerde minuten wordt niet gecontroleerd. `ASSUMPTIONS` verwijdert slechts positieve evidentie; het signaleert zelf geen unsupported premise.
- `context_fit` slaagt zodra één inhoudswoord overlapt. Dit voert de gedocumenteerde v2-regel uit, maar meet geen volledige contextuele passendheid. Meervoud/parafrase en generieke woorden beperken de bruikbaarheid verder.
- `format_pass_rate` gebruikt alleen voltooide uitvoer. De ene ongeldige uitvoer verdwijnt uit deze noemer: 1.0 beschrijft de 107 toegelaten vragen, niet 108 geplande outputs.
- `save` bewaart oudere rapporten in job history, maar vervangt de hoofdverwijzing. `report` verbergt een ouder resultaat wanneer versie/hash verandert. Onafhankelijke toegang tot oude versies ontbreekt in de interface.
- Individuele resultaten missen stabiele regel-ID's, afzonderlijke regelversies, veldverwijzingen en expliciete verklaringen van wat wel/niet vastgesteld is.

## Werkende onderdelen en beperkingen

- De scorer gebruikt een allow-list en voegt methode/model pas na beoordeling toe. Methodeblindheid is bevestigd; dit is geen gevonden fout.
- `inconclusive` wordt niet automatisch een pass. De 98 onbesliste feitelijke beoordelingen zijn deels een eerlijke uiting van beperkte regels, geen bewijs dat deze vragen onjuist zijn.
- Hergebruik van bankvragen wordt al beschrijvend geteld. Hogere diversiteit bewijst geen hogere onderwijskwaliteit.
- Geen AI-evaluator wordt automatisch aangeroepen. Bestaande menselijke labels staan apart. De nieuwe optionele semantische laag moet dit behouden.

## Voorgenomen wijzigingen

V3 splitst mechanisch formaat, herkenbare vraagstructuur, expliciete contextverwijzingen, controleerbare feitelijke claims en agency-signalen. Lexicale overlap en diversiteit blijven beschrijvend. Tijdseenheden en getallen worden genormaliseerd; conflicten tussen notitie en gestructureerde velden worden expliciet onbeslist gehouden. Een vaste regel kan alleen haar eigen afgebakende eigenschap vaststellen.

Nieuwe rapporten worden als afzonderlijke onveranderbare records toegevoegd. De originele jobs, snapshots, uitvoer, v2-rapporten en bestanden worden niet overschreven. Filters, versie-selectie en vergelijking tonen beide rubrics met hun verschillende betekenissen. Herbeoordeling is retrospectief: v3 is naar aanleiding van waargenomen problemen ontworpen en moet voor bevestigend vervolgonderzoek op nieuwe cases worden gevalideerd.

`preservation-before.json` bevat de oorspronkelijke hashes; de oude implementatie staat bytegetrouw in `backend/legacy_metrics/v2`. Er is vóór wijzigingen een SQLite-backup gemaakt.
