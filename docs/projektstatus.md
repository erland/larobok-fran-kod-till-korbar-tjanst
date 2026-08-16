# Projektstatus

## Bok
- Titel: Från kod till körbar tjänst
- Språk: svenska
- Författare: Erland Lindmark
- Version: 0.1
- book_kind: factbook
- book_type: subject_overview

## Nuvarande fas
Planering slutförd. TaskBoard-referensimplementationen är byggd och end-to-end-verifierad i GitHub Actions. Inledningen samt kapitel 1–4 är skrivna som första manusversion.

## Kapitelstatus
| Kapitel | Titel | Status | Kommentar |
|---|---|---|---|
| 0 | Inledning | Skriven | Första manusversion, grundad i verifierad referensimplementation |
| 1 | Från kod till körbar tjänst | Skriven | Första manusversion, grundad i verifierad referensimplementation |
| 2 | Tjänstens arkitektur | Skriven | Första manusversion, grundad i verifierad runtime-arkitektur |
| 3 | Projektstruktur och utvecklingsmiljö | Skriven | Första manusversion, grundad i faktisk repo- och utvecklingsstruktur |
| 4 | PWA som frontendarkitektur | Skriven | Första manusversion, grundad i faktisk vite-plugin-pwa- och Nginx-konfiguration |
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
- Val av mer detaljerad frontend-teststack och eventuell separat testcontainerstrategi för kapitel 12; grundläggande end-to-end smoke test finns nu i GitHub Actions.
- Om Docker-images i slutlig publiceringspipeline ska låsas med digest utöver versions-taggar.

## Nästa rekommenderade steg
- Skriv kapitel 5 om frontend med React och TypeScript med den faktiska `App.tsx`- och `api.ts`-implementationen som grund.
- Vid nästa manuspass kontrolleras övergången mellan kapitel 4 och 5 så att PWA-leveransmodellen och React-applikationens interna struktur hålls isär.
