# TaskBoard – referensimplementation

Detta är den körbara referensimplementation som används genom hela boken.

## Arkitektur

- `frontend/`: React + TypeScript + Vite + PWA. I produktionsimagen serveras den byggda applikationen av Nginx.
- `backend/`: Java 21 + Quarkus + Jakarta Persistence/Hibernate ORM + Flyway.
- `db`: PostgreSQL 18 i Docker Compose.
- Nginx är tjänstens yttre entry point och proxar `/api/` till Quarkus.

## Starta hela tjänsten

```bash
cp .env.example .env
docker compose up --build
```

Öppna därefter `http://localhost:8080`.

## Lokal utveckling

Backend kan köras i Quarkus dev mode. Med Docker tillgängligt startar Quarkus Dev Services automatiskt en PostgreSQL-instans eftersom JDBC PostgreSQL-extensionen finns och ingen explicit dev-datasource är konfigurerad.

```bash
cd backend
./mvnw quarkus:dev
```

Maven Wrapper läggs inte in i denna första referensrevision; använd installerad Maven om wrapper saknas:

```bash
mvn quarkus:dev
```

Frontend körs separat med Vite och proxar `/api` till Quarkus på port 8080:

```bash
cd frontend
npm ci
npm run dev
```

## Databas och migrationer

Flyway-migrationerna ligger i `backend/src/main/resources/db/migration/`. Hibernate ORM är satt till `validate`: Flyway äger schemat och JPA-modellen verifieras mot det.

## Versionsval

Se `STACK-VERSIONS.md` för de versioner som valdes när referensimplementationen initierades och varför de valdes.
## Automatisk verifiering i GitHub Actions

Workflowen `.github/workflows/04-test-reference-implementation.yml` verifierar referensimplementationen vid ändringar under `code/taskboard/` och kan även köras manuellt. Den:

1. kör den statiska referensvalideringen,
2. kör frontendtesterna och bygger React/TypeScript-frontenden,
3. kompilerar och testar Quarkus-backenden med Maven,
4. validerar och bygger Docker Compose-konfigurationen,
5. startar hela tjänsten och gör ett smoke test genom Nginx → Quarkus → PostgreSQL.

Smoke testet skapar en uppgift via REST-API:t och läser tillbaka den för att kontrollera att hela kedjan fungerar.

## Releasa referensimplementationen

Workflowen `.github/workflows/05-release-reference-implementation.yml` skapar en separat TaskBoard-release när en tagg `taskboard-v<SemVer>` pushas. Den bygger web- och backend-images en gång, kör frontend-/backendtester och smoke-testar exakt de byggda images innan de publiceras till GitHub Container Registry. Därefter skapas ett releasepaket med:

- `docker-compose.release.yml` utan lokala build-steg,
- `release.env` med exakta image-digests för web, backend och PostgreSQL,
- `release-manifest.json` med Git commit, Actions-run, verktygsversioner och checksummor,
- `SHA256SUMS.txt`,
- installationsinstruktionen `README.md`.

Releasepaketet publiceras i en separat GitHub Release med samma `taskboard-v<SemVer>`-tagg. Bokens `v*`-taggar för EPUB/PDF påverkas inte.

