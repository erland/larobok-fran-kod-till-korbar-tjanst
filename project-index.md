# Projektindex

## Projekt
- Titel: Från kod till körbar tjänst
- book_kind: factbook
- book_type: subject_overview
- Project-id: bda7fd5f-8515-4a5a-b548-a42496aa66aa
- Revision: 11
- Senaste verifierade zip: `fran-kod-till-korbar-tjanst-r11.zip`

## Kapitel
- Inledning: skriven, första manusversion
- Planerade numrerade kapitel: 17
- Skapade kapitel med brödtext: kapitel 1
- Källförteckning: planerad

## Referensimplementation
- Case: TaskBoard
- Plats: `code/taskboard/`
- Status: komplett referenskedja React/PWA → Nginx → Quarkus/JPA/Flyway → PostgreSQL, verifierad end-to-end i GitHub Actions.
- Docker Compose: finns med persistent databas och health-baserad startordning.
- Full runtime-verifiering: genomförd i GitHub Actions med image-build, Compose-start och smoke test genom Nginx → Quarkus → PostgreSQL.

## Faktakontroll
- Policy: `docs/kallpolicy.md`
- Register: `docs/faktakontroll.md`
- Versionsval för referensimplementationen: fastställda och primärkällekontrollerade 2026-08-16.
- Öppna punkter: utökad teststack, digest-policy och presentationsformat för synliga källhänvisningar.

## Export
- EPUB: ej skapad
- PDF: ej skapad

## Synkkontroll
- `book.yaml`, bokspecifikation, canon, projektstatus, projektindex och referensimplementation beskriver samma aktuella bokprofil och arkitektur.
