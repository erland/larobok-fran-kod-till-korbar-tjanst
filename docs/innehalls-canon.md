# Innehålls-canon

## Gemensam profil
- Språk: svenska
- book_kind: factbook
- book_type: subject_overview
- Nivå/faktadjup: experienced
- Läsarprofil: erfaren utvecklare med TypeScript/React och Java/JPA som kända områden; Quarkus/PostgreSQL får praktisk introduktion.
- Ton: teknisk, saklig, förklarande och referensorienterad.

## Terminologi och fasta definitioner
| Begrepp | Första kapitel | Definition | Kommentar |
|---|---:|---|---|
| TaskBoard | 1 | Bokens genomgående referenstjänst för hantering av arbetsuppgifter. | Domänen hålls avsiktligt liten. |
| frontend | 1 | React/TypeScript-applikationen som byggs som PWA. | I produktion serveras dess statiska filer av Nginx. |
| backend | 1 | Quarkus-applikationen som exponerar REST-API och applikationslogik. | Java + JPA/Hibernate ORM. |
| reverse proxy | 2 | Nginx-funktion som vidarebefordrar `/api` till backend. | Nginx är yttre entry point. |
| referensimplementation | 1 | Den kompletta körbara TaskBoard-koden under `code/taskboard/`. | Bokens kodexempel ska hållas synkroniserade med den. |

## Återkommande exempel, case eller berättargrepp
- Namn: TaskBoard
- Syfte: ge samma konkreta kontext för frontend, API, persistence, migrationer, PWA, testning och Docker.
- Regler:
  - Caset får inte växa för att skapa artificiell domänkomplexitet.
  - Ny funktionalitet läggs bara till när den behövs för en teknisk poäng.
  - Kodexempel i boken ska hämtas från eller överensstämma med referensimplementationen.
  - En rekommenderad huvudlösning visas först; alternativ beskrivs där de förändrar viktiga trade-offs.

## Faktaboksspecifikt
- Fasta sakförhållanden som återkommer:
  - Nginx serverar byggd frontend och proxar `/api` till Quarkus i den färdiga Docker-miljön.
  - Vite används endast som utvecklingsserver i frontendutveckling.
  - Flyway ansvarar för versionshantering av databasschemat.
  - PostgreSQL är persistent datalager och ska normalt endast vara åtkomligt på det interna Docker-nätverket.
  - Docker Compose är bokens huvudsakliga drifts-/överföringsmodell.
- Kända osäkerheter/tolkningar:
  - Exakta ramverks- och image-versioner fastställs först när referensimplementationen skapas.
  - Exakt PWA-plugin/tooling är ännu inte fastställt.
  - Exakt teststack är ännu inte fastställd.
- Tidskänsliga delar: installationskommandon, extension-/plugin-namn, konfigurationsnycklar, image-taggar, Compose-beteenden och ramverksrekommendationer.

## Versions- och faktaval
- Verktyg/ramverk/versioner: fastställs och verifieras mot officiella källor när referensimplementationen initieras.
- Antaganden: läsaren behärskar TypeScript, React, Java och JPA på utvecklarnivå.
- Delar som kräver färsk verifiering: PWA/Vite, Quarkus, PostgreSQL, Flyway, Nginx, Docker och testverktyg.
