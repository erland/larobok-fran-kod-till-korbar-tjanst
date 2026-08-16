# Faktakontroll

| ID | Kapitel | Påstående/faktaområde | Status | Källa/verifiering | Kontrollerad | Kommentar |
|---|---|---|---|---|---|---|
| F011 | 1 | Referensimplementationens kompletta requestkedja och runtime-form | Kontrollerad | GitHub Actions `04-test-reference-implementation.yml`: build, Compose-start och smoke test | 2026-08-16 | Verifierad kedja Nginx → Quarkus → PostgreSQL; smoke test skapar och läser tillbaka en uppgift. |
| F001 | 4 | Aktuell PWA-setup för React/Vite | Delvis kontrollerad | React/Vite/vite-plugin-pwa officiella releaser och dokumentation | 2026-08-16 | React 19.2.7, Vite 8.2.1 och vite-plugin-pwa 1.3.0 valda; omverifiera detaljer vid kapitelarbete. |
| F002 | 6 | Quarkus-version, extensions och REST-konfiguration | Kontrollerad för referenskod | Quarkus officiell release-/guide-dokumentation | 2026-08-16 | Quarkus 3.33.3.1 i 3.33 LTS-serien vald. REST/Jackson, Hibernate ORM, PostgreSQL JDBC, Flyway, Validator och Health används. |
| F003 | 8 | PostgreSQL-version/image och relevant containerkonfiguration | Kontrollerad för referenskod | PostgreSQL officiella release-/versionssidor samt genomförd runtime-verifiering | 2026-08-16 | PostgreSQL 18.4 vald; PostgreSQL 18-volymmount och containerstart verifierade i Compose-smoke test. |
| F004 | 9 | Flyway-konventioner och Quarkus-integrering | Kontrollerad för referenskod | Quarkus officiella Flyway-guide | 2026-08-16 | Migrationer i `db/migration`; `migrate-at-start`; Hibernate satt till schema-validering. |
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
- Fastställ format för synliga källhänvisningar i kapiteltexten.
- Omverifiera tidskänsliga versioner och kommandon när respektive kapitel skrivs och före publicering.

## Publiceringskontroll
- [ ] Alla högprioriterade påståenden är verifierade.
- [ ] Alla exakta installationskommandon är kontrollerade mot aktuell officiell dokumentation.
- [x] Referensimplementationen bygger och den nuvarande end-to-end-verifieringen går igenom.
- [ ] Tidskänsliga uppgifter har kontrollerats på nytt.
- [ ] Källhänvisningar och källförteckning är konsekventa.
