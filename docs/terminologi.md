# Terminologi

| Term | Definition | Första användning | Kommentar |
|---|---|---|---|
| PWA | Progressive Web App; webbapplikation med valda installerbara/offline-relaterade webbfunktioner. | Kapitel 1 | Fördjupas i kapitel 4. |
| TaskBoard | Genomgående referenstjänst för arbetsuppgifter. | Kapitel 1 | Caset ska hållas avsiktligt enkelt. |
| frontend | React/TypeScript-klienten. | Kapitel 1 | Byggs med Vite, serveras av Nginx i körmiljö. |
| backend | Quarkus-baserat REST-API och applikationslogik. | Kapitel 1 | Java + JPA. |
| reverse proxy | Server som tar emot extern trafik och vidarebefordrar vald trafik till intern tjänst. | Kapitel 2 | Nginx proxar `/api` till Quarkus. |
| same-origin | Webbläsarprincip där frontend och API använder samma origin sett från klienten. | Kapitel 2 | TaskBoard använder relativa `/api`-URL:er. |
| request / response | HTTP-begäran respektive HTTP-svar. | Kapitel 2 | Engelska termer används när de syftar på HTTP-/kodmodeller; i löptext används även *anrop* och *svar*. |
| persistens | Beständig lagring och det applikationslager som ansvarar för den. | Kapitel 1 | Svenska *persistens* används i löptext; `jakarta.persistence` och `persistence.xml` behåller sina kodnamn. |
| migration | Versionshanterad förändring av databasschemat. | Kapitel 9 | Flyway är kanonisk migrationsmotor. |
| image | Docker-image som paketerar ett filsystem och metadata för containerkörning. | Kapitel 1 | *Image* behålls som Docker-term; plural *images*. |
| container | Körande eller stoppad instans skapad från en image. | Kapitel 1 | Ska inte blandas ihop med imagen eller persistent data. |
| healthcheck | Maskinell kontroll som ger en begränsad hälsosignal för en service/container. | Kapitel 1 | Stavas konsekvent *healthcheck* när Docker/Compose-funktionen avses. |
| readiness | Signal om att en komponent är redo att ta emot avsedd trafik. | Kapitel 1 | Skiljs från att processen bara har startat. |
| runtime | Körningsfas eller körningsmiljö. | Kapitel 1 | Engelska termen används främst i sammansättningar som `runtime-image`; annars föredras *körmiljö* eller *vid start*. |
| artefakt | Byggt eller paketerat resultat som kan identifieras och överlämnas. | Kapitel 1 | Svenska *artefakt* används i löptext. |
| körmiljö | Den sammansatta miljö där tjänstens images körs. | Kapitel 1 | Skiljs tydligt från utvecklingsmiljö. |
| referensimplementation | Komplett körbar kod som bokens exempel baseras på. | Kapitel 1 | Ligger under `code/taskboard/`. |
