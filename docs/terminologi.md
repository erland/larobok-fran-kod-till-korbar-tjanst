# Terminologi

| Term | Definition | Första användning | Kommentar |
|---|---|---|---|
| PWA | Progressive Web App; webbapplikation med valda installerbara/offline-relaterade webbfunktioner. | Kapitel 1 | Fördjupas i kapitel 4. |
| TaskBoard | Genomgående referenstjänst för arbetsuppgifter. | Kapitel 1 | Caset ska hållas avsiktligt enkelt. |
| frontend | React/TypeScript-klienten. | Kapitel 1 | Byggs med Vite, serveras av Nginx i körmiljö. |
| backend | Quarkus-baserat REST-API och applikationslogik. | Kapitel 1 | Java/JPA. |
| reverse proxy | Server som tar emot extern trafik och vidarebefordrar vald trafik till intern tjänst. | Kapitel 2 | Nginx proxar `/api` till Quarkus. |
| migration | Versionshanterad förändring av databasschemat. | Kapitel 9 | Flyway är kanonisk migrationsmotor. |
| körmiljö | Den sammansatta miljö där tjänstens images körs. | Kapitel 1 | Skiljs tydligt från utvecklingsmiljö. |
| referensimplementation | Komplett körbar kod som bokens exempel baseras på. | Kapitel 1 | Ligger under `code/taskboard/`. |
