# Bokspecifikation

## Titel och undertitel
- Titel: *Från kod till körbar tjänst*
- Undertitel: *PWA med React och TypeScript, Quarkus, PostgreSQL och Docker*

## Bokprofil
- book_kind: factbook
- book_type: subject_overview
- Motivering: Boken ska ge en sammanhängande teknisk översikt och referensarkitektur för en komplett tjänst. Den ska förklara val, samband, konfiguration och leverans snarare än träna läsaren genom övningar eller lära ut programmeringsspråken från grunden.

## Språk och författare
- Språk: svenska
- Författare: Erland Lindmark

## Ämne och syfte
Boken beskriver hur en modern, portabel webbtjänst kan byggas med en PWA-frontend i React och TypeScript, en backend i Java på Quarkus med JPA och Flyway, PostgreSQL som databas samt Nginx som webbserver och reverse proxy. Hela tjänsten ska i slutänden kunna distribueras och startas med Docker Compose i en intressents egen miljö.

Syftet är att ge en erfaren utvecklare en konkret referensarkitektur, förståelse för teknikernas ansvar och gränser samt ett reproducerbart sätt att koppla samman, konfigurera, testa, containerisera och leverera lösningen.

## Målgrupp
Erfarna utvecklare som redan har god förståelse för TypeScript, React, Java och JPA. Läsaren behöver inte ha djup tidigare erfarenhet av Quarkus, PostgreSQL, Flyway, Nginx eller Docker Compose, men förväntas kunna läsa kod, konfiguration och terminalkommandon utan grundläggande introduktion.

## Nivå eller faktadjup
- difficulty: experienced
- Fokus ligger på arkitektur, integration, konfiguration, driftbarhet och leverans.
- TypeScript, React, Java och JPA behandlas endast så långt som behövs för referenslösningen.
- Quarkus och PostgreSQL introduceras praktiskt på den nivå som behövs för att sätta upp och förstå tjänsten, inte som separata fördjupningskurser.

## Omfattning och avgränsningar
- Cirka 17 numrerade kapitel plus inledning och källförteckning.
- En och samma referenstjänst används genom hela boken.
- En rekommenderad huvudlösning prioriteras framför att jämföra alla tänkbara alternativ.
- Autentisering och auktorisering behandlas på arkitektur- och konfigurationsnivå men ingen omfattande identitetsplattform byggs in i huvudcaset.
- Kubernetes, molnplattformar och avancerad orkestrering ligger utanför huvudlösningen och tas endast upp som möjliga nästa steg.
- CI/CD kan beröras som leveransprincip men bokens kärna är en reproducerbar Docker-baserad tjänst som kan köras i en egen miljö.

## Ton och stil
Teknisk, saklig och förklarande. Boken ska ligga mellan arkitekturhandbok och praktisk faktabok. Kod och konfiguration används när de förklarar ett verkligt arkitektur- eller integrationsval. Onödig boilerplate undviks.

Återkommande förklaringsmönster där det passar:
1. Vad gör delen?
2. Varför behövs den?
3. Hur kopplas den till resten av tjänsten?

## Omslag och illustrationer
- Omslagsbild: öppet beslut.
- Inre illustrationer: avstängda tills de uttryckligen beställs.
- Arkitekturdiagram kan senare skapas som tekniska figurer om användaren vill ha inre illustrationer.

## Faktaboksspecifikt
- Ämnesbredd/fördjupning: bred genomgång av hela leveranskedjan med fördjupning i integrationspunkter, arkitekturval, konfiguration och driftbarhet.
- Berättande/förklarande/referens: främst förklarande och referensorienterad, med ett återkommande konkret case.
- Centrala faktaområden: PWA, React/TypeScript, Nginx, REST/HTTP, Quarkus, JPA, PostgreSQL, Flyway, konfiguration, säkerhet, testning, Docker, Docker Compose, drift och reproducerbar leverans.
- Källkrav: hög teknisk källkvalitet; primärt officiell dokumentation och andra primärkällor.
- Tidskänslighet: hög för ramverk, container-images, CLI-kommandon, rekommenderade konfigurationer och versionsspecifika beteenden.
- Synliga referenser: ja.
- Källförteckning: ja.

## Återkommande exempel/case/berättargrepp
### TaskBoard
TaskBoard är en liten tjänst för hantering av arbetsuppgifter och används genom hela boken som referensimplementation.

Grundläggande funktioner:
- skapa, visa, ändra och arkivera uppgifter
- titel och beskrivning
- status: OPEN, IN_PROGRESS, DONE
- prioritet
- valfritt förfallodatum
- listning och filtrering

Grundmodell:
- id
- title
- description
- status
- priority
- dueDate
- createdAt
- updatedAt

Domänen ska hållas avsiktligt enkel. Ny funktionalitet införs endast när den behövs för att demonstrera en teknisk aspekt.

### Referensarkitektur
- React + TypeScript som PWA-frontend.
- Vite används som utvecklingsserver i frontendens utvecklingsflöde.
- I den färdiga körmiljön byggs frontend till statiska filer som serveras av Nginx.
- Nginx är tjänstens yttre entry point och reverse proxy för `/api` till Quarkus.
- Quarkus exponerar REST-API och använder JPA för persistence.
- Flyway äger versionshanteringen av databasschemat.
- PostgreSQL lagrar tjänstens persistenta data.
- Docker Compose binder samman Nginx/frontend, backend och databas.
- PostgreSQL exponeras normalt inte utanför det interna Docker-nätverket.

### Kodprincip
Den kompletta referensimplementationen ska ligga under `code/taskboard/`. Kod som visas i boken ska komma från eller hållas konsekvent med denna implementation. Kodexempel ska vara körbara eller tydligt markerade som förenklade utdrag.

## Kvalitetskriterier
- Arkitekturen ska vara konsekvent genom hela boken.
- Referensimplementation och kodexempel får inte glida isär.
- Alla versionsberoende tekniska påståenden ska verifieras nära skriv- eller publiceringstillfället.
- Officiell dokumentation ska prioriteras för React/Vite/PWA, Quarkus, PostgreSQL, Flyway, Nginx och Docker.
- Skillnaden mellan utvecklingsmiljö och produktionslik körmiljö ska vara tydlig.
- Läsaren ska efter boken kunna förstå och reproducera helheten utan att boken blir en nybörjarkurs i de ingående programmeringsspråken.
