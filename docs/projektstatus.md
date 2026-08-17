# Projektstatus

## Bok
- Titel: Från kod till körbar tjänst
- Språk: svenska
- Författare: Erland Lindmark
- Version: 0.1
- book_kind: factbook
- book_type: subject_overview

## Nuvarande fas
Planering slutförd. TaskBoard-referensimplementationen är byggd och end-to-end-verifierad i GitHub Actions. Inledningen samt kapitel 1–17 är skrivna som första manusversion. Hela det planerade numrerade grundmanuset är därmed skrivet.

## Kapitelstatus
| Kapitel | Titel | Status | Kommentar |
|---|---|---|---|
| 0 | Inledning | Skriven | Första manusversion, grundad i verifierad referensimplementation |
| 1 | Från kod till körbar tjänst | Skriven | Första manusversion, grundad i verifierad referensimplementation |
| 2 | Tjänstens arkitektur | Skriven | Första manusversion, grundad i verifierad runtime-arkitektur |
| 3 | Projektstruktur och utvecklingsmiljö | Skriven | Första manusversion, grundad i faktisk repo- och utvecklingsstruktur |
| 4 | PWA som frontendarkitektur | Skriven | Första manusversion, grundad i faktisk vite-plugin-pwa- och Nginx-konfiguration |
| 5 | Frontend med React och TypeScript | Skriven | Första manusversion, grundad i faktisk `App.tsx`- och `api.ts`-implementation |
| 6 | Backend med Quarkus | Skriven | Första manusversion, grundad i faktisk REST-resurs, DTO-, CDI-, validerings- och tjänstelagerimplementation |
| 7 | Persistens med JPA | Skriven | Första manusversion, grundad i faktisk `TaskEntity`, `TaskRepository`, `EntityManager`- och transaktionsimplementation |
| 8 | PostgreSQL som databas | Skriven | Första manusversion, grundad i faktisk Compose-konfiguration, `task_item`-schema, PostgreSQL 18.4 och verifierad volymmount |
| 9 | Databasschemat som kod med Flyway | Skriven | Första manusversion, grundad i faktisk `V1__create_task.sql`, `migrate-at-start` och Hibernate schema-validering |
| 10 | Från frontend till databas och tillbaka | Skriven | Första manusversion, grundad i den faktiska request/response-kedjan och verifierat end-to-end-test |
| 11 | Konfiguration och säkerhet | Skriven | Första manusversion, grundad i faktisk Compose-, Nginx- och Quarkus-konfiguration samt explicit säkerhetsavgränsning |
| 12 | Testning av den kompletta tjänsten | Skriven | Första manusversion, grundad i faktisk CI-workflow och smoke-test samt verifierad Quarkus-/frontend-teststrategi |
| 13 | Frontend, reverse proxy och backend som Docker-images | Skriven | Första manusversion, grundad i faktiska multi-stage Dockerfiles, Nginx-konfiguration, Quarkus fast-jar och verifierad image-start i CI |
| 14 | Den kompletta tjänsten med Docker Compose | Skriven | Första manusversion, grundad i faktisk Compose-konfiguration, health-baserad startordning och verifierad CI-start |
| 15 | Från lokal körning till driftbar tjänst | Skriven | Första manusversion, grundad i faktisk Compose-/PostgreSQL-/Quarkus-konfiguration och verifierad drift-/backupdokumentation |
| 16 | En reproducerbar leverans | Skriven | Första manusversion, grundad i faktisk Git/CI/Docker/npm/Maven-leveranskedja och verifierad reproducerbarhetspolicy |
| 17 | Arkitekturen i backspegeln | Skriven | Första manusversion, syntes av den verifierade referensarkitekturen, dess trade-offs och naturliga utvecklingsvägar |
| – | Källförteckning | Planerad | Exporterad efter kapitel 17 |

## Referensimplementation
- Plats: `code/taskboard/`
- Status: komplett körbar kedja, end-to-end-verifierad i GitHub Actions.
- Frontend: React 19.2.7, TypeScript 6.0.3, Vite 8.2.1 och vite-plugin-pwa 1.3.0.
- Runtime frontend: Nginx 1.30.4 stable, som serverar PWA:n och proxar `/api`.
- Backend: Java 21 och Quarkus 3.33.3.1 LTS med REST/Jackson, Hibernate ORM/JPA, PostgreSQL JDBC, Flyway, Bean Validation och SmallRye Health.
- Databas: PostgreSQL 18.4.
- Leverans: Docker Compose med persistent PostgreSQL-volume och health-baserad startordning.
- Lokal utveckling: Vite-proxy till Quarkus; Quarkus Dev Services kan tillhandahålla PostgreSQL.
- GitHub Actions: `04-test-reference-implementation.yml` bygger frontend/backend, kör Maven-testfasen, bygger Docker-images och verifierar hela requestkedjan med ett runtime smoke test.
- Full runtime-verifiering: GitHub Actions bygger images, startar Compose-stacken och smoke-testar Nginx → Quarkus → PostgreSQL. Denna workflow är projektets kanoniska end-to-end-verifiering.

## Faktakontroll
- Initiala versionsval och huvudkonfiguration för referensimplementationen verifierade 2026-08-16 mot officiella primärkällor.
- Detaljer som hör till senare kapitel ska fortfarande omverifieras nära skriv-/publiceringstillfället.

## Öppna beslut
- Om omslagsbild ska tas fram och vilket visuellt uttryck den i så fall ska ha.
- Om den rekommenderade utökade teststacken (Quarkus API/integrationstester med PostgreSQL Dev Services samt Vitest + React Testing Library) ska implementeras i referenskoden eller enbart fungera som nästa utvecklingssteg.

## Nästa rekommenderade steg
- Genomför en helhetsrevision av kapitel 0–17: disposition, överlapp, terminologi, kodexempel, faktakontroll och källhänvisningar.
- Ta därefter ställning till om den rekommenderade teststacken och den starkare leveransmodellen ska implementeras i referenskoden före slutrevision/export.
- Digest-policyn är fastställd på manusnivå: releasekritiska image-referenser bör registrera verifierade digests; en eventuell implementation i referenskoden görs separat och testas i CI.
