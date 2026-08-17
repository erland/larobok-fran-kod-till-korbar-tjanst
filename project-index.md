# Projektindex

## Projekt
- Titel: Från kod till körbar tjänst
- book_kind: factbook
- book_type: subject_overview
- Project-id: bda7fd5f-8515-4a5a-b548-a42496aa66aa
- Revision: 33
- Senaste verifierade zip: `fran-kod-till-korbar-tjanst-r33.zip`

## Kapitel
- Inledning: helhetsreviderad
- Planerade numrerade kapitel: 17
- Skapade och helhetsreviderade kapitel med brödtext: kapitel 1–17
- Källförteckning: samlad och uppdaterad; kapitel 17 är en syntes av tidigare verifierat material och den körbara referensimplementationen.

## Referensimplementation
- Case: TaskBoard
- Plats: `code/taskboard/`
- Status: komplett referenskedja React/PWA → Nginx → Quarkus/JPA/Flyway → PostgreSQL, verifierad end-to-end i GitHub Actions.
- Docker Compose: finns med persistent databas och health-baserad startordning.
- Frontendtestning: `App.test.tsx` med Vitest, React Testing Library, user-event och jsdom verifierar initial laddning, create, statusupdate och HTTP-fel; `npm run test` kör sviten i CI.
- Backendtestning: `TaskResourceTest` med `@QuarkusTest` och Rest Assured mot PostgreSQL 18.4 via Dev Services är implementerad; `mvn verify` kör sviten i CI.
- Full runtime-verifiering: genomförd i GitHub Actions med image-build, Compose-start och smoke test genom Nginx → Quarkus → PostgreSQL.

## Faktakontroll
- Policy: `docs/kallpolicy.md`
- Register: `docs/faktakontroll.md`
- Versionsval för referensimplementationen: fastställda och primärkällekontrollerade 2026-08-16.
- Öppna punkter: Steg C för frontendberoenden är slutfört: npm-genererad `package-lock.json` är incheckad och både Workflow 04 och frontend-Dockerfile använder `npm ci`. Digest-policyn är fastställd på manusnivå. Synliga källhänvisningar använder kort parentetisk form med fullständig post i källförteckningen.

## Export
- EPUB: ej skapad
- PDF: ej skapad

## Synkkontroll
- `book.yaml`, bokspecifikation, canon, projektstatus, projektindex och referensimplementation beskriver samma aktuella bokprofil och arkitektur.
