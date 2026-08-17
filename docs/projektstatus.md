# Projektstatus

## Bok
- Titel: Från kod till körbar tjänst
- Språk: svenska
- Författare: Erland Lindmark
- Version: 0.1
- book_kind: factbook
- book_type: subject_overview

## Nuvarande fas
Planering, grundmanus, teknisk helhetsrevision, slutsynk och publiceringsslutputs är slutförda. TaskBoard-referensimplementationen är byggd, testad och end-to-end-verifierad i GitHub Actions, och den separata releasekedjan är runtime-verifierad genom GHCR-publicering, digestinsamling, deploymentbundle och GitHub Release. Inledningen samt kapitel 1–17 är synkroniserade mot denna verifierade implementation. Publiceringspasset har dessutom kontrollerat kvarvarande tidsmarkörer, källhänvisningar, metadata, terminologi och exportberedskap utan att ändra referensimplementationens funktionalitet.

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
- GitHub Actions: `04-test-reference-implementation.yml` använder SHA-pinnade externa Actions, installerar frontendberoenden med `npm ci`, kör Vitest-komponenttesterna, bygger frontenden, kör backendens `@QuarkusTest`/Rest Assured-test mot PostgreSQL Dev Services via `mvn verify`, bygger Docker-images och verifierar hela requestkedjan med ett runtime smoke test.
- Full runtime-verifiering: GitHub Actions bygger images, startar Compose-stacken och smoke-testar Nginx → Quarkus → PostgreSQL. Denna workflow är projektets kanoniska end-to-end-verifiering.
- TaskBoard-release: `05-release-reference-implementation.yml` triggas av `taskboard-v<SemVer>`, bygger images en gång, smoke-testar dem med `--no-build`, publicerar exakt de verifierade web-/backend-images till GHCR och skapar ett deploymentpaket med image-digests, `release-manifest.json` och SHA-256-checksummor. Kedjan är runtime-verifierad i GitHub Actions, inklusive GHCR-push och skapad GitHub Release.

## Faktakontroll
- Initiala versionsval och huvudkonfiguration för referensimplementationen verifierade 2026-08-16 mot officiella primärkällor.
- Detaljer som hör till senare kapitel ska fortfarande omverifieras nära skriv-/publiceringstillfället.

## Öppna beslut
- Om omslagsbild ska tas fram och vilket visuellt uttryck den i så fall ska ha.
- Ytterligare supply-chain-härdning som attestering/SBOM och explicit Maven-reproducerbarhetskontroll är valfria nästa nivåer, inte krav för bokens referensmål.

## Nästa rekommenderade steg
- Kör projektets EPUB/PDF-preview och gör en slutlig visuell kontroll av sidbrytningar, kodblock, tabeller, titelblad och innehållsförteckning.
- Ta fram omslag om boken ska publiceras med omslagsbild.
- Produktionsfunktioner som autentisering, TLS/trusted proxy, secrets-hantering, backup/restore och observability ska endast införas om TaskBoard ska gå från pedagogisk referens till verklig tjänst.
