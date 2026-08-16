# Faktakontroll

| ID | Kapitel | Påstående/faktaområde | Status | Källa/verifiering | Kontrollerad | Kommentar |
|---|---|---|---|---|---|---|
| F011 | 1 | Referensimplementationens kompletta requestkedja och runtime-form | Kontrollerad | GitHub Actions `04-test-reference-implementation.yml`: build, Compose-start och smoke test | 2026-08-16 | Verifierad kedja Nginx → Quarkus → PostgreSQL; smoke test skapar och läser tillbaka en uppgift. |
| F012 | 2 | Compose-standardnätverk, service discovery, reverse proxy, Quarkus HTTP-bindning och health-baserad startordning | Kontrollerad | Docker Docs (Networking in Compose; Services), NGINX proxy module, Quarkus HTTP/config-dokumentation samt verifierad TaskBoard-runtime | 2026-08-16 | Kapitlet skiljer uttryckligen på ej publicerad databasport och faktisk nätverkssegmentering. |
| F013 | 3 | Vite dev proxy, Quarkus database Dev Services och Mavens standardkataloglayout | Kontrollerad | Vite Server Options, Quarkus Dev Services for Databases och Apache Maven Standard Directory Layout samt faktisk TaskBoard-konfiguration | 2026-08-16 | Kapitlet skiljer på snabb lokal utveckling, produktionslik Compose-körning och CI-verifiering; avsaknad av npm-lockfil dokumenteras uttryckligen. |
| F001 | 4 | PWA-installation, manifest, service worker, precache, autoUpdate, HTTPS och aktuell TaskBoard-konfiguration | Kontrollerad | MDN PWA/manifest-dokumentation, Vite PWA Getting Started/Automatic reload/Service Worker Precache samt faktisk `vite.config.ts` och `nginx.conf` | 2026-08-16 | TaskBoard använder manifest + genererad service worker med `autoUpdate`; statiska resurser precachas men `/api` har ingen runtime-cache. SVG-ikon är referensprojektets miniminivå; robust Chromium-installation bör kompletteras med 192/512-pixelsikoner. |
| F014 | 5 | React state/effects, TypeScript transporttyper och Fetch-felhantering i TaskBoard-frontenden | Kontrollerad | React officiell dokumentation (`useState`, `useEffect`), TypeScript Handbook (`Everyday Types`, `Object Types`), MDN Fetch API samt faktisk `App.tsx` och `api.ts` | 2026-08-16 | Kapitlet skiljer compile-time-typer från runtime-validering, beskriver Strict Mode som utvecklingsbeteende och är troget att nuvarande referensfrontend saknar klientrouter. |
| F002 | 6 | Quarkus-version, Maven packaging, REST/Jackson, CDI, Bean Validation, konfigurationskällor, dev mode och transaktionsgräns | Kontrollerad | Quarkus officiella guider för REST JSON, Quarkus REST, CDI, Validation, Configuration, Maven Plugin, Dev Mode och Hibernate ORM samt faktisk TaskBoard-kod | 2026-08-16 | Kapitel 6 är grundat i Quarkus 3.33.3.1-referensimplementationen och skiljer uttryckligen dev mode från paketerad runtime samt HTTP-/servicelager från persistence-detaljerna i kapitel 7. |
| F015 | 7 | Jakarta Persistence/Hibernate ORM, injicerad `EntityManager`, managed entities/dirty checking, transaktionsgräns och `@Version` | Kontrollerad | Quarkus *Using Hibernate ORM and Jakarta Persistence*, Jakarta Persistence Specification 3.2 samt faktisk `TaskEntity`, `TaskRepository` och `TaskService` | 2026-08-16 | Kapitlet skiljer explicit JPA:s optimistiska låsning från ett klientburet HTTP-concurrency-kontrakt och låter Flyway fortsatt äga schemaevolutionen. |
| F003 | 8 | PostgreSQL 18.4, JDBC-/Compose-konfiguration, SQL-datatyper, constraints, index och PostgreSQL 18-volymmount | Kontrollerad | PostgreSQL 18 officiell dokumentation för constraints, UUID och index; Docker Official Image for PostgreSQL dokumentation/Dockerfile för PGDATA/VOLUME; faktisk `V1__create_task.sql`, Compose-konfiguration och genomförd runtime-verifiering | 2026-08-16 | Kapitlet skiljer mellan API/JPA-garantier och databasschemats egna constraints, beskriver befintliga index utan att påstå att de är universellt optimala och dokumenterar 18+-mounten `/var/lib/postgresql`. |
| F004 | 9 | Flyway-konventioner, schemahistorik/checksummor, Quarkus-integrering, baseline/repair och samspel med Hibernate schema-validering | Kontrollerad | Quarkus *Using Flyway* och *Using Hibernate ORM and Jakarta Persistence*; Redgate Flyway-dokumentation för versionerade migrationer, schema history, repair och baselines; faktisk `V1__create_task.sql` | 2026-08-16 | TaskBoard har endast V1 i faktisk kod. V2/V3 i kapitlet är uttryckligen hypotetiska evolutionssteg. `migrate-at-start` används; Hibernate validerar i stället för att äga schemaevolutionen. |
| F005 | 11 | Reverse proxy, headers, same-origin och CORS-konfiguration | Delvis kontrollerad | Nginx officiell versionsinformation; konfiguration statiskt granskad | 2026-08-16 | Nginx 1.30.4 stable vald. Same-origin via `/api`; detaljverifiering vid kapitelarbete. |
| F006 | 12 | Aktuell testsetup och containerbaserad databastestning | Ej kontrollerad | Officiell dokumentation för valda testverktyg | | Fastställs när testkapitlet/referenstesterna byggs ut. |
| F007 | 13 | Docker multi-stage builds och rekommenderade runtime-images | Kontrollerad för referenskod | Node/NGINX/Quarkus-releaser samt genomförd GitHub Actions-build | 2026-08-16 | Frontend- och backend-images byggda framgångsrikt i CI. Detaljrekommendationer om images omverifieras vid kapitelarbete. |
| F008 | 14 | Docker Compose health/dependency/networking semantics | Kontrollerad för vald modell | Docker Compose officiell dokumentation samt genomförd Compose-start i CI | 2026-08-16 | Databas och backend använder health-baserad startordning; hela stacken startar och smoke-testas i GitHub Actions. |
| F009 | 15 | PostgreSQL backup/restore och Quarkus health | Delvis kontrollerad | Quarkus Health finns i referenskod | 2026-08-16 | Backup/restore verifieras vid kapitelarbete. |
| F010 | 16 | Image tag/digest och reproducerbar leverans | Ej kontrollerad | Docker officiell dokumentation | | Fastställ digest-policy när leveranskapitlet skrivs. |

## Fastställda versionsval 2026-08-16
- Java 21.
- Quarkus 3.33.3.1, senaste kontrollerade patch i den rekommenderade 3.33 LTS-serien.
- React 19.2.7.
- Vite 8.2.1.
- TypeScript 6.0.3.
- `@vitejs/plugin-react` 6.0.5.
- `vite-plugin-pwa` 1.3.0.
- Node.js 24.x LTS för frontend-build.
- PostgreSQL 18.4.
- Nginx 1.30.4 stable.

Detaljer finns även i `code/taskboard/STACK-VERSIONS.md`.

## Öppna verifieringspunkter
- Fastställ testverktyg och strategi för frontend samt PostgreSQL-integrationstester.
- Omverifiera tidskänsliga versioner och kommandon när respektive kapitel skrivs och före publicering.

## Publiceringskontroll
- [ ] Alla högprioriterade påståenden är verifierade.
- [ ] Alla exakta installationskommandon är kontrollerade mot aktuell officiell dokumentation.
- [x] Referensimplementationen bygger och den nuvarande end-to-end-verifieringen går igenom.
- [ ] Tidskänsliga uppgifter har kontrollerats på nytt.
- [ ] Källhänvisningar och källförteckning är konsekventa.
