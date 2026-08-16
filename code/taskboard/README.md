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
npm install
npm run dev
```

## Databas och migrationer

Flyway-migrationerna ligger i `backend/src/main/resources/db/migration/`. Hibernate ORM är satt till `validate`: Flyway äger schemat och JPA-modellen verifieras mot det.

## Versionsval

Se `STACK-VERSIONS.md` för de versioner som valdes när referensimplementationen initierades och varför de valdes.
## Automatisk verifiering i GitHub Actions

Workflowen `.github/workflows/04-test-reference-implementation.yml` verifierar referensimplementationen vid ändringar under `code/taskboard/` och kan även köras manuellt. Den:

1. kör den statiska referensvalideringen,
2. bygger React/TypeScript-frontenden,
3. kompilerar och testar Quarkus-backenden med Maven,
4. validerar och bygger Docker Compose-konfigurationen,
5. startar hela tjänsten och gör ett smoke test genom Nginx → Quarkus → PostgreSQL.

Smoke testet skapar en uppgift via REST-API:t och läser tillbaka den för att kontrollera att hela kedjan fungerar.

