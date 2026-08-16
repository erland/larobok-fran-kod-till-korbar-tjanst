# Referensimplementation

Bokens genomgående referensimplementation ska ligga i `code/taskboard/`.

Den planerade slutarkitekturen är:

- React + TypeScript + PWA-setup i frontend.
- Vite som utvecklingsserver/buildverktyg.
- Nginx i runtime-imagen för att servera frontendens statiska filer och reverse-proxa `/api` till backend.
- Java + Quarkus + JPA/Hibernate ORM i backend.
- Flyway för databasmigrationer.
- PostgreSQL som persistent databas.
- Docker Compose för att starta hela tjänsten.

Referensimplementationen är ännu inte initierad. Exakta ramverks- och image-versioner ska verifieras mot officiella källor i samband med initieringen.
