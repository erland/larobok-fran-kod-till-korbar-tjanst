# Projektstatus

## Bok
- Titel: Från kod till körbar tjänst
- Språk: svenska
- Författare: Erland Lindmark
- Version: 0.1
- book_kind: factbook
- book_type: subject_overview

## Nuvarande fas
Planering slutförd. Körbar TaskBoard-referensimplementation initierad. Inget numrerat kapitel är ännu skrivet.

## Kapitelstatus
| Kapitel | Titel | Status | Kommentar |
|---|---|---|---|
| 0 | Inledning | Planerad | Stomme skapad |
| 1 | Från kod till körbar tjänst | Planerad | Stomme skapad |
| 2 | Tjänstens arkitektur | Planerad | Stomme skapad |
| 3 | Projektstruktur och utvecklingsmiljö | Planerad | Stomme skapad |
| 4 | PWA som frontendarkitektur | Planerad | Stomme skapad |
| 5 | Frontend med React och TypeScript | Planerad | Stomme skapad |
| 6 | Backend med Quarkus | Planerad | Stomme skapad |
| 7 | Persistens med JPA | Planerad | Stomme skapad |
| 8 | PostgreSQL som databas | Planerad | Stomme skapad |
| 9 | Databasschemat som kod med Flyway | Planerad | Stomme skapad |
| 10 | Från frontend till databas och tillbaka | Planerad | Stomme skapad |
| 11 | Konfiguration och säkerhet | Planerad | Stomme skapad |
| 12 | Testning av den kompletta tjänsten | Planerad | Stomme skapad |
| 13 | Frontend, reverse proxy och backend som Docker-images | Planerad | Stomme skapad |
| 14 | Den kompletta tjänsten med Docker Compose | Planerad | Stomme skapad |
| 15 | Från lokal körning till driftbar tjänst | Planerad | Stomme skapad |
| 16 | En reproducerbar leverans | Planerad | Stomme skapad |
| 17 | Arkitekturen i backspegeln | Planerad | Stomme skapad |
| – | Källförteckning | Planerad | Exporterad efter kapitel 17 |

## Referensimplementation
- Plats: `code/taskboard/`
- Status: initierad som komplett körbar kedja.
- Frontend: React 19.2.7, TypeScript 6.0.3, Vite 8.2.1 och vite-plugin-pwa 1.3.0.
- Runtime frontend: Nginx 1.30.4 stable, som serverar PWA:n och proxar `/api`.
- Backend: Java 21 och Quarkus 3.33.3.1 LTS med REST/Jackson, Hibernate ORM/JPA, PostgreSQL JDBC, Flyway, Bean Validation och SmallRye Health.
- Databas: PostgreSQL 18.4.
- Leverans: Docker Compose med persistent PostgreSQL-volume och health-baserad startordning.
- Lokal utveckling: Vite-proxy till Quarkus; Quarkus Dev Services kan tillhandahålla PostgreSQL.
- Känd verifieringsbegränsning: projektmiljön där revisionen skapades saknade Docker och nätåtkomst för npm/Maven, så full container-build och runtime smoke test återstår.

## Faktakontroll
- Initiala versionsval och huvudkonfiguration för referensimplementationen verifierade 2026-08-16 mot officiella primärkällor.
- Detaljer som hör till senare kapitel ska fortfarande omverifieras nära skriv-/publiceringstillfället.

## Öppna beslut
- Om omslagsbild ska tas fram och vilket visuellt uttryck den i så fall ska ha.
- Val av teststack för frontend och exakt strategi för PostgreSQL-baserade integrationstester i kapitel 12.
- Exakt presentationsformat för synliga källhänvisningar.
- Om Docker-images i slutlig publiceringspipeline ska låsas med digest utöver versions-taggar.

## Nästa rekommenderade steg
- Skriv `chapters/00-inledning.md` och kapitel 1 med den faktiska TaskBoard-referensimplementationen som grund.
- Därefter kan kapitel 2–3 etablera arkitekturbilden och projektstrukturen innan teknikdelarna skrivs.
