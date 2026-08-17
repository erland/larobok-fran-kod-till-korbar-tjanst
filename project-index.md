# Projektindex

## Projekt
- Titel: Från kod till körbar tjänst
- book_kind: factbook
- book_type: subject_overview
- Project-id: bda7fd5f-8515-4a5a-b548-a42496aa66aa
- Revision: 35
- Senaste verifierade zip: `fran-kod-till-korbar-tjanst-r35.zip`

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
- Releasekedja: `taskboard-v<SemVer>` bygger och smoke-testar samma web-/backend-images före GHCR-push och producerar digestlåst `docker-compose.release.yml` + `release.env`, `release-manifest.json` och SHA-256-checksummor.

## Faktakontroll
- Policy: `docs/kallpolicy.md`
- Register: `docs/faktakontroll.md`
- Versionsval för referensimplementationen: fastställda och primärkällekontrollerade 2026-08-16.
- Öppna punkter: Steg C och D är implementerade: npm-lockfil/`npm ci`, SHA-pinnade TaskBoard-Actions, verifierad release-imagekedja, GHCR-publicering, registry-digests och maskinläsbart release-manifest finns i referensimplementationen. Synliga källhänvisningar använder kort parentetisk form med fullständig post i källförteckningen.

## Export
- EPUB: ej skapad
- PDF: ej skapad

## Synkkontroll
- `book.yaml`, bokspecifikation, canon, projektstatus, projektindex och referensimplementation beskriver samma aktuella bokprofil och arkitektur.
