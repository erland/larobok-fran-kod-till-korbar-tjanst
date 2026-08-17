# Publiceringsslutputs – revision 39

## Omfattning

Slutpasset utgår från den runtime-verifierade TaskBoard-referensimplementationen i revision 37 och manus-/faktasynkningen i revision 38. Målet är publiceringsberedskap utan ny funktionalitet i referenskoden.

## Redaktionellt och faktamässigt genomfört

- granskat bokkapitlen efter kvarvarande formuleringar som felaktigt beskriver implementerade delar som framtida eller saknade,
- synkroniserat de korta CI-sammanfattningarna i kapitel 1 och 3 med den faktiska kedjan: `npm ci` + Vitest, Maven `verify` + Quarkus/PostgreSQL Dev Services, Compose-build och full-stack-smoke-test,
- korrigerat releasebeskrivningen i kapitel 16: web- och backend-images byggs direkt med sina versionsmärkta GHCR-referenser, smoke-testas utan rebuild och pushas därefter utan mellanliggande omtaggning,
- uppdaterat innehålls-canon med den fastställda teststacken,
- kompletterat källförteckningen med den Vitest-sida som citeras i kapitel 12 och rensat dubblerade Docker-källor,
- uppdaterat bokmetadata till aktuell publiceringsrevision,
- gjort mindre terminologisk språkputs i leveranskapitlet.

## Exportpreflight

Den kanoniska EPUB/PDF-exporten kördes under slutpasset. Tre exportproblem upptäcktes och åtgärdades:

1. PDF-templaten saknade Pandocs genererade `highlighting-macros`, vilket gav `Environment Shaded undefined` vid syntaxmarkerade kodblock. Templaten inkluderar nu makrona när de finns.
2. H2/H3 fick oönskade `0.x`-nummer eftersom H1-kapitlen skapas av Lua-filtret i stället för LaTeX chapter-counter. PDF-templaten använder nu `secnumdepth=-1`; kapitelnumret kommer från manusets H1 medan underrubriker visas utan artificiell LaTeX-numrering.
3. Unicode-tecken i katalogträd och symbolen `≠` saknades i den valda monospacefonten. Presentationsexemplen använder nu portabla ASCII-varianter (`|--`, `` `-- ``, `|`, `!=`).

Efter korrigeringarna byggdes både EPUB och PDF utan Pandoc/LaTeX-varningar om saknade glypher. Titelblad, innehållsförteckning, brödtext, underrubriker och kodexempel kontrollerades visuellt på representativa PDF-sidor.

## Faktaverifiering nära publicering

Följande tidskänsliga principer omverifierades mot officiella primärkällor 2026-08-17:

- `npm ci` kräver en befintlig lockfil och avbryter om `package.json` och lockfilen inte stämmer överens,
- GitHub rekommenderar fullständig commit-SHA för immutable pinning av Actions,
- Docker Compose kan vänta på `service_healthy` för beroenden med healthcheck,
- Quarkus Dev Services kan starta PostgreSQL automatiskt i testläge när relevant extension finns och extern JDBC-URL inte är konfigurerad.

## Kvar före faktisk publicering

Det redaktionella och tekniska manuset samt exportkedjan är publiceringsberedda. Kvar är i första hand beslut om omslag och eventuell kanalmetadata som publisher/identifier.
