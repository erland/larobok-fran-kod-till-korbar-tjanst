# Faktakontroll

| ID | Kapitel | Påstående/faktaområde | Status | Källa/verifiering | Kontrollerad | Kommentar |
|---|---|---|---|---|---|---|
| F001 | 4 | Aktuell rekommenderad PWA-setup för React/Vite | Ej kontrollerad | Officiell webb-/verktygsdokumentation | | Verifieras vid kapitelarbete |
| F002 | 6 | Aktuell Quarkus-version, extensions och REST-konfiguration | Ej kontrollerad | Quarkus officiell dokumentation | | Verifieras vid kapitelarbete |
| F003 | 8 | PostgreSQL-version/image och relevant containerkonfiguration | Ej kontrollerad | PostgreSQL + Docker Official Image | | Verifieras vid kapitelarbete |
| F004 | 9 | Flyway-konventioner och Quarkus-integrering | Ej kontrollerad | Flyway + Quarkus officiell dokumentation | | Verifieras vid kapitelarbete |
| F005 | 11 | Reverse proxy, headers, same-origin och CORS-konfiguration | Ej kontrollerad | Nginx + Quarkus officiell dokumentation | | Verifieras vid kapitelarbete |
| F006 | 12 | Aktuell testsetup och containerbaserad databastestning | Ej kontrollerad | Officiell dokumentation för valda testverktyg | | Fastställ verktyg när referenskoden skapas |
| F007 | 13 | Docker multi-stage builds och rekommenderad Quarkus-image | Ej kontrollerad | Docker + Quarkus officiell dokumentation | | Verifieras vid kapitelarbete |
| F008 | 14 | Docker Compose health/dependency/networking semantics | Ej kontrollerad | Docker Compose-specifikation/dokumentation | | Verifieras vid kapitelarbete |
| F009 | 15 | PostgreSQL backup/restore och Quarkus health | Ej kontrollerad | PostgreSQL + Quarkus officiell dokumentation | | Verifieras vid kapitelarbete |
| F010 | 16 | Image tag/digest och reproducerbar leverans | Ej kontrollerad | Docker officiell dokumentation | | Verifieras vid kapitelarbete |

## Öppna verifieringspunkter
- Fastställ aktuella, kompatibla versioner för referensimplementationen när kodbasen initieras.
- Fastställ PWA-tooling för Vite/React.
- Fastställ testverktyg och strategi för PostgreSQL-integrationstester.
- Fastställ format för synliga källhänvisningar i kapiteltexten.

## Publiceringskontroll
- [ ] Alla högprioriterade påståenden är verifierade.
- [ ] Alla exakta installationskommandon är kontrollerade mot aktuell officiell dokumentation.
- [ ] Referensimplementationen bygger och testerna går igenom.
- [ ] Tidskänsliga uppgifter har kontrollerats på nytt.
- [ ] Källhänvisningar och källförteckning är konsekventa.
