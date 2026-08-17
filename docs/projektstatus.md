# Projektstatus

## Bok
- Titel: Från kod till körbar tjänst
- Språk: svenska
- Författare: Erland Lindmark
- Version: 0.1
- book_kind: factbook
- book_type: subject_overview

## Nuvarande fas
Planering slutförd. TaskBoard-referensimplementationen är byggd och end-to-end-verifierad i GitHub Actions. Inledningen samt kapitel 1–17 är skrivna och helhetsreviderade som ett sammanhållet första fullständigt manus. Revisionen har stramat upp progression, terminologi, interna hänvisningar, överlapp och kapitelgränser samt kontrollerat manuset mot den körbara referensimplementationen.

## Kapitelstatus
| Kapitel | Titel | Status | Kommentar |
|---|---|---|---|
| 0 | Inledning | Helhetsreviderad | Grundad i verifierad referensimplementation |
| 1 | Från kod till körbar tjänst | Helhetsreviderad | Grundad i verifierad referensimplementation |
| 2 | Tjänstens arkitektur | Helhetsreviderad | Grundad i verifierad runtime-arkitektur |
| 3 | Projektstruktur och utvecklingsmiljö | Helhetsreviderad | Grundad i faktisk repo- och utvecklingsstruktur |
| 4 | PWA som frontendarkitektur | Helhetsreviderad | Grundad i faktisk vite-plugin-pwa- och Nginx-konfiguration |
| 5 | Frontend med React och TypeScript | Helhetsreviderad | Grundad i faktisk `App.tsx`- och `api.ts`-implementation |
| 6 | Backend med Quarkus | Helhetsreviderad | Grundad i faktisk REST-resurs, DTO-, CDI-, validerings- och tjänstelagerimplementation |
| 7 | Persistens med JPA | Helhetsreviderad | Grundad i faktisk `TaskEntity`, `TaskRepository`, `EntityManager`- och transaktionsimplementation |
| 8 | PostgreSQL som databas | Helhetsreviderad | Grundad i faktisk Compose-konfiguration, `task_item`-schema, PostgreSQL 18.4 och verifierad volymmount |
| 9 | Databasschemat som kod med Flyway | Helhetsreviderad | Grundad i faktisk `V1__create_task.sql`, `migrate-at-start` och Hibernate schema-validering |
| 10 | Från frontend till databas och tillbaka | Helhetsreviderad | Grundad i den faktiska request/response-kedjan och verifierat end-to-end-test |
| 11 | Konfiguration och säkerhet | Helhetsreviderad | Grundad i faktisk Compose-, Nginx- och Quarkus-konfiguration samt explicit säkerhetsavgränsning |
| 12 | Testning av den kompletta tjänsten | Helhetsreviderad | Grundad i faktisk CI-workflow, Vitest/React Testing Library, Quarkus-integrationstest och full-stack-smoke-test |
| 13 | Frontend, reverse proxy och backend som Docker-images | Helhetsreviderad | Grundad i faktiska multi-stage Dockerfiles, Nginx-konfiguration, Quarkus fast-jar och verifierad image-start i CI |
| 14 | Den kompletta tjänsten med Docker Compose | Helhetsreviderad | Grundad i faktisk Compose-konfiguration, health-baserad startordning och verifierad CI-start |
| 15 | Från lokal körning till driftbar tjänst | Helhetsreviderad | Grundad i faktisk Compose-/PostgreSQL-/Quarkus-konfiguration och verifierad drift-/backupdokumentation |
| 16 | En reproducerbar leverans | Helhetsreviderad | Grundad i faktisk Git/CI/Docker/npm/Maven-leveranskedja och verifierad reproducerbarhetspolicy |
| 17 | Arkitekturen i backspegeln | Helhetsreviderad | Syntes av den verifierade referensarkitekturen, dess avvägningar och naturliga utvecklingsvägar |
| – | Källförteckning | Uppdaterad | Samlad primärkällförteckning för de faktakontrollerade kapitlen |

## Referensimplementation
- Plats: `code/taskboard/`
- Status: komplett körbar kedja, end-to-end-verifierad i GitHub Actions.
- Frontend: React 19.2.7, TypeScript 6.0.3, Vite 8.2.1 och vite-plugin-pwa 1.3.0.
- Runtime frontend: Nginx 1.30.4 stable, som serverar PWA:n och proxar `/api`.
- Backend: Java 21 och Quarkus 3.33.3.1 LTS med REST/Jackson, Hibernate ORM/JPA, PostgreSQL JDBC, Flyway, Bean Validation och SmallRye Health.
- Databas: PostgreSQL 18.4.
- Leverans: Docker Compose med persistent PostgreSQL-volume och health-baserad startordning.
- Lokal utveckling: Vite-proxy till Quarkus; Quarkus Dev Services kan tillhandahålla PostgreSQL.
- GitHub Actions: `04-test-reference-implementation.yml` installerar frontendberoenden, kör Vitest-komponenttesterna, bygger frontenden, kör backendens `@QuarkusTest`/Rest Assured-test mot PostgreSQL Dev Services via `mvn verify`, bygger Docker-images och verifierar hela requestkedjan med ett runtime smoke test.
- Full runtime-verifiering: GitHub Actions bygger images, startar Compose-stacken och smoke-testar Nginx → Quarkus → PostgreSQL. Denna workflow är projektets kanoniska end-to-end-verifiering.

## Faktakontroll
- Initiala versionsval och huvudkonfiguration för referensimplementationen verifierade 2026-08-16 mot officiella primärkällor.
- Detaljer som hör till senare kapitel ska fortfarande omverifieras nära skriv-/publiceringstillfället.

## Öppna beslut
- Om omslagsbild ska tas fram och vilket visuellt uttryck den i så fall ska ha.
- Den rekommenderade frontend- och backendteststacken är nu implementerad i referensimplementationen.
- `package-lock.json` är nu genererad av npm i GitHub Actions, incheckad i referensimplementationen och används av både CI och frontend-Dockerfile via `npm ci`.

## Nästa rekommenderade steg
- Steg C är slutfört för frontendberoenden: npm-genererad `package-lock.json` är incheckad och både CI och frontend-Dockerfile använder `npm ci`. Starkare image-/Actions-pinning och release-manifest hör till nästa leveranshärdning.
- Genomför därefter en slutputs med fokus på språk, kodexempel, källhänvisningar och exportberedskap.
- Digest-policyn är fastställd på manusnivå: releasekritiska image-referenser bör registrera verifierade digests; en eventuell implementation i referenskoden görs separat och testas i CI.
