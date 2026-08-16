# Referensimplementation

Bokens genomgående referensimplementation finns nu i `code/taskboard/`.

Den består av:

- React + TypeScript + Vite + PWA i frontend.
- Nginx i frontendens runtime-image för statiska filer och reverse proxy av `/api`.
- Java 21 + Quarkus + JPA/Hibernate ORM i backend.
- Flyway för databasmigrationer.
- PostgreSQL som persistent databas.
- Docker Compose för att starta hela tjänsten.

Se `taskboard/README.md` för körning och `taskboard/STACK-VERSIONS.md` för fastställda versionsval.
