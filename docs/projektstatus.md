# Projektstatus

## Bok
- Titel: Från kod till körbar tjänst
- Språk: svenska
- Författare: Erland Lindmark
- Version: 0.1
- book_kind: factbook
- book_type: subject_overview

## Nuvarande fas
Planering slutförd; projekt initierat. Inget numrerat kapitel är ännu skrivet.

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

## Faktakontroll
- Öppna verifieringspunkter: 10 initiala områden registrerade i `docs/faktakontroll.md`.
- Senast genomgången: 2026-08-16

## Öppna beslut
- Om omslagsbild ska tas fram och vilket visuellt uttryck den i så fall ska ha.
- Exakta kompatibla versioner för referensimplementationens teknikstack.
- Val av PWA-plugin/tooling för React/Vite.
- Val av teststack för frontend och PostgreSQL-baserade integrationstester.
- Exakt presentationsformat för synliga källhänvisningar.

## Nästa rekommenderade steg
- Initiera `code/taskboard/` som körbar referensimplementation och fastställ samtidigt aktuella, kompatibla teknikversioner mot officiell dokumentation.
- Därefter skriv `chapters/00-inledning.md` och kapitel 1 med referensimplementationens faktiska struktur som grund.
