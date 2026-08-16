# Källpolicy

## Syfte
Boken behandlar en teknikstack som förändras kontinuerligt. Källpolicyn ska säkerställa att kod, konfiguration, CLI-kommandon och tekniska rekommendationer är korrekta nära skriv- och publiceringstillfället.

## Grundkrav
- Primärkällor prioriteras när det är praktiskt och relevant.
- Aktuella påståenden ska verifieras nära skriv-/publiceringstillfället.
- Versionsspecifika beteenden får inte beskrivas som tidlösa egenskaper.
- Om trovärdiga källor skiljer sig ska skillnaden beskrivas sakligt.
- Osäkerhet får inte skrivas om till säker fakta.
- Kod och konfiguration ska verifieras mot den referensimplementation som följer bokprojektet.

## Projektets val
- Kravnivå: hög
- Synliga referenser i boktext: ja
- Källförteckning i slutet: ja
- Referensstil: korta källhänvisningar i text eller noter kopplade till en samlad källförteckning; exakt presentationsformat fastställs före manusproduktion.
- Maximal ålder på tidskänsliga källor: ingen fast årgräns; aktuella versioner och rekommendationer verifieras vid varje kapitelrevision och inför publicering.
- Särskilt betrodda källtyper/domäner: officiell dokumentation och standarder för React, TypeScript, Vite/PWA, Quarkus/Jakarta, PostgreSQL, Flyway, Nginx och Docker.
- Källtyper som bör undvikas: anonyma tutorials, SEO-sammanställningar, äldre blogginlägg med versionsspecifika instruktioner och sekundärkällor när officiell dokumentation finns.

## Tekniska verifieringsprinciper
- När ett exakt kommando eller konfigurationsfält visas ska det kontrolleras mot aktuell officiell dokumentation.
- När referensimplementationen introducerar ett versionsval ska versionen dokumenteras i canon och faktakontroll.
- Docker-images ska senare pin-nas på en nivå som stödjer reproducerbarhet; strategin fastställs när referensimplementationen skapas.
- Boken ska undvika exakta versionsnummer i löptext när de inte behövs för förståelsen.

## Anteckning
Källarbetsmaterial hör hemma i `docs/faktakontroll.md`. Den publicerade källförteckningen ligger i `chapters/kallforteckning.md`.
