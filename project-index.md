# Projektindex

## Projekt
- Titel: Från kod till körbar tjänst
- book_kind: factbook
- book_type: subject_overview
- Project-id: bda7fd5f-8515-4a5a-b548-a42496aa66aa
- Revision: 27
- Senaste verifierade zip: `fran-kod-till-korbar-tjanst-r27.zip`

## Kapitel
- Inledning: skriven, första manusversion
- Planerade numrerade kapitel: 17
- Skapade kapitel med brödtext: kapitel 1–16
- Källförteckning: kompletterad med primärkällor genom kapitel 16; flera kapitel bygger dessutom direkt på verifierad referenskod och end-to-end/Compose-start.

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
- Öppna punkter: eventuell implementation av rekommenderad utökad teststack samt den starkare leveransmodellen från kapitel 16. Digest-policyn är fastställd på manusnivå. Synliga källhänvisningar använder kort parentetisk form med fullständig post i källförteckningen.

## Export
- EPUB: ej skapad
- PDF: ej skapad

## Synkkontroll
- `book.yaml`, bokspecifikation, canon, projektstatus, projektindex och referensimplementation beskriver samma aktuella bokprofil och arkitektur.
