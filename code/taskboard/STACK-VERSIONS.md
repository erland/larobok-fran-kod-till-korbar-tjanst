# Versionsval för referensimplementationen

Fastställda 2026-08-16 mot respektive projekts officiella dokumentation/releaser.

| Del | Val | Princip |
|---|---|---|
| Java | 21 | LTS och starkt rekommenderad av Quarkus för moderna applikationer. |
| Quarkus | 3.33.3.1 | Senaste patchen i Quarkus 3.33 LTS vid kontrolltillfället. Quarkus rekommenderar senaste LTS för produktion. |
| React | 19.2.7 | Senaste React 19.2-patchen vid kontrolltillfället. |
| Vite | 8.2.1 | Senaste stabila Vite-releasen vid kontrolltillfället. |
| TypeScript | 6.0.3 | Senaste stabila TypeScript 6.0-patchen vid kontrolltillfället. |
| @vitejs/plugin-react | 6.0.5 | Aktuell stabil React-plugin för Vite. |
| vite-plugin-pwa | 1.3.0 | Aktuell stabil release. |
| Node.js | 24.x LTS | Frontendens build-miljö använder Node 24 LTS. |
| PostgreSQL | 18.4 | Senaste PostgreSQL 18-patchen vid kontrolltillfället. |
| Nginx | 1.30.4 stable | Aktuell stabil Nginx-release vid kontrolltillfället. |

Dockerfiler använder i vissa fall en versionsserie, till exempel `node:24-alpine`, för att få säkerhets- och patchuppdateringar inom vald LTS-serie. Själva boktexten ska undvika att göra exakta patchversioner till konceptuella krav.
