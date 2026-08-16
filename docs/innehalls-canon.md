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
  - Exakta patchversioner är tidskänsliga och ska inte beskrivas som långsiktiga arkitekturkrav.
  - PWA-tooling är fastställd till vite-plugin-pwa för referensimplementationen.
  - Exakt teststack är ännu inte fastställd.
- Tidskänsliga delar: installationskommandon, extension-/plugin-namn, konfigurationsnycklar, image-taggar, Compose-beteenden och ramverksrekommendationer.

## Versions- och faktaval
- Verktyg/ramverk/versioner: referensimplementationen initierades 2026-08-16 med Java 21, Quarkus 3.33.3.1 LTS, React 19.2.7, Vite 8.2.1, TypeScript 6.0.3, vite-plugin-pwa 1.3.0, Node 24 LTS, PostgreSQL 18.4 och Nginx 1.30.4 stable. Exakta patchversioner ska omverifieras före publicering.
- Antaganden: läsaren behärskar TypeScript, React, Java och JPA på utvecklarnivå.
- Delar som kräver färsk verifiering: PWA/Vite, Quarkus, PostgreSQL, Flyway, Nginx, Docker och testverktyg.
