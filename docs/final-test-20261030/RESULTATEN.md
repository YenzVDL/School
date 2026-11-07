# ICT-vergelijking: Fixed Question Bank, RAG en LLM

Uitgevoerd op 30 oktober 2026. Nieuwe bank met 32 vragen en een nieuwe dataset met 36 synthetische scenario’s: zes ICT-onderwerpen × zes situaties.

De bank en scenario’s zijn door Codex opgesteld en kort gecontroleerd nadat lokale generatie ongeldige voorwaarden en foutieve controleantwoorden opleverde. Dit is een geassisteerde inhoudscontrole, geen onafhankelijke menselijke validatie. Mislukte generatiepogingen, correcties en eerdere snapshots zijn behouden.

RAG en LLM gebruiken hetzelfde geïnstalleerde `llama3.2:1b`-model, dezelfde instellingen en dezelfde scenario-versies. Eén herhaling per methode. Een echte preflight ging vooraf aan het experiment. Metrics zijn vooraf vastgelegd en tijdens het experiment niet aangepast. Er is geen AI-beoordelaar gebruikt.

Experiment: `job_b7f16c9da9684219`. Scriptbeoordeling: `script_assessment_3b18fac4a96c4e87`.

| Methode | Voltooide vragen / gepland | Reflectieve formulering: pass / flag / onbeslist | Contextregels: pass / flag / onbeslist | Feitelijke controles: pass / flag / onbeslist | Gem. woordoverlap | Unieke vragen |
| --- | ---: | --- | --- | --- | ---: | ---: |
| LLM | 36 / 36 | 8 / 0 / 28 | 34 / 2 / 0 | 0 / 2 / 34 | 48.1% | 36 |
| Fixed Question Bank | 36 / 36 | 36 / 0 / 0 | 33 / 0 / 3 | 1 / 0 / 35 | 21.5% | 18 |
| RAG | 35 / 36 | 22 / 0 / 13 | 31 / 4 / 0 | 2 / 4 / 29 | 40.6% | 34 |

Pass = voldoet aan de vastgelegde regels. Flag = een regel signaleert een probleem. Onbeslist = deze regels kunnen het inhoudelijke criterium niet vaststellen. Woordoverlap en variatie zijn beschrijvende indicatoren; hogere waarden bewijzen geen betere leervraag.

Alle methoden worden door dezelfde functie beoordeeld, uitsluitend met de vraag en het scenario. Methode, model, bankvoorwaarden, prioriteit en retrievalscore beïnvloeden de beoordeling niet. De vergelijking gebruikt dezelfde 36 scenario/herhaling-combinaties; uitvoeringsfouten blijven in de geplande aantallen staan.

Dit is een operationele vergelijking op synthetische ontwikkelcases met één generator en één seed. De resultaten onderbouwen verschillen op deze vaste indicatoren, maar wijzen geen algemeen beste methode aan en valideren niet de volledige semantische kwaliteit.
    
Metricversie: `fixed-rubric-v2-method-blind`. Implementatiehash: `fe1eeecce0fd839690b7a26a2de6ba58ce70946629aa5247647b0ed1e01e2b00`.

Bestanden: `protocol.json`, `preflight.json`, `bank-snapshot.json`, `dataset-snapshot.json`, `fixed-metrics.json`, `experiment-export.json` en de inhoudscontrole-/generatieverslagen in deze map.
