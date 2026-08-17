# Inledning

En webbapplikation är sällan färdig när frontendkoden fungerar och REST-anropen ger rätt svar på utvecklarens dator. Mellan fungerande kod och en tjänst som någon annan kan ta emot, starta, förstå och förvalta finns ett antal gränser som måste göras tydliga: hur frontend hittar backend, vem som äger databasschemat, hur konfiguration förs in i körmiljön, vilka komponenter som exponeras utåt, hur uppstart och hälsa kontrolleras och hur hela lösningen byggs på ett reproducerbart sätt.

Det är dessa gränser den här boken handlar om.

Bokens utgångspunkt är en liten men komplett referenstjänst som heter **TaskBoard**. Domänen är medvetet enkel: användaren kan skapa, visa, uppdatera och ta bort arbetsuppgifter. En uppgift har bland annat titel, beskrivning, status, prioritet och ett valfritt förfallodatum. Enkelheten är viktig. Syftet är inte att bygga ett avancerat ärendehanteringssystem, utan att kunna följa samma data och samma ansvar genom hela teknikstacken utan att domänlogiken skymmer arkitekturen.

TaskBoard består av en PWA-baserad frontend i React och TypeScript, en backend i Java på Quarkus och en PostgreSQL-databas. Frontenden byggs med Vite. I den färdiga körmiljön serveras dess statiska filer av Nginx, som också är tjänstens yttre HTTP-ingång och vidarebefordrar anrop under `/api` till Quarkus. Backenden använder JPA/Hibernate ORM för persistens och Flyway för versionshantering av databasschemat. Webbserver, backend och databas körs som separata containrar och binds samman med Docker Compose.

Det viktiga är inte att varje projekt måste använda exakt dessa produkter. Det viktiga är att ansvaren går att se och resonera om. En frontend måste byggas och serveras. Ett API måste ha en tydlig exponeringsyta. Persistens behöver både en objektmodell och ett kontrollerat databasschema. Miljöspecifik konfiguration måste kunna ändras utan att koden byggs om. Databasen behöver persistent lagring. Komponenter måste starta i en ordning som tar hänsyn till faktisk beredskap. Och någon måste kunna verifiera att hela kedjan fungerar efter att alla delar satts samman.

## Boken utgår från körbar kod

Referensimplementationen ligger under `code/taskboard/` i bokprojektet. Den är inte en samling fristående kodfragment som skrivits för att se bra ut i tryck, utan den kan byggas och startas som en sammanhängande tjänst. Kodutdrag i boken ska därför hämtas från, eller hållas konsekventa med, den implementationen.

Det här valet påverkar hur boken är skriven. När vi exempelvis beskriver att Nginx proxar `/api` till Quarkus finns motsvarande konfiguration i referensprojektet. När vi beskriver att Flyway äger databasschemat finns en riktig migration i backendprojektet och Hibernate är konfigurerat för att validera modellen mot schemat. När vi beskriver en containeriserad leverans finns Dockerfiles och en Compose-fil som faktiskt används för att starta lösningen.

Referensimplementationen verifieras dessutom automatiskt i GitHub Actions. CI bygger de separata delarna, skapar Docker-images, startar Compose-miljön och provar ett riktigt API-flöde genom den publika Nginx-ingången. Därmed kontrolleras inte bara att projekten går att bygga var för sig, utan att den sammansatta kedjan Nginx → Quarkus → PostgreSQL fungerar i praktiken. De exakta testnivåerna och vad smoke-testet bevisar behandlas senare i boken.

Det betyder inte att referensimplementationen är en färdig generell plattform. Den saknar medvetet delar som skulle behövas i många produktionssystem, exempelvis en fullständig identitetslösning, avancerad observability, horisontell skalning och plattformsorkestrering. Dessa avgränsningar gör det möjligt att fokusera på den grundläggande leveranskedjan utan att göra lösningen större än bokens syfte kräver.

## För vem boken är skriven

Boken vänder sig till dig som redan arbetar som utvecklare och kan läsa TypeScript, React, Java och JPA utan en introduktion till språkens eller ramverkens grunder. Fokus ligger därför inte på hur en React-komponent fungerar eller hur en Java-klass deklareras. I stället ligger tyngdpunkten på hur delarna kopplas samman och vilka konsekvenser arkitektur- och konfigurationsval får när tjänsten ska köras utanför utvecklingsmiljön.

Quarkus, PostgreSQL, Flyway, Nginx och Docker introduceras på den nivå som behövs för helheten. Målet är inte att ersätta respektive produkts fullständiga dokumentation, utan att ge en tillräckligt djup och sammanhängande förståelse för hur de används i den valda arkitekturen.

Du bör efter boken kunna titta på en liknande lösning och ställa frågor som:

- Vilken komponent är den publika ingången till tjänsten?
- Hur hittar frontend backend i utveckling respektive i körmiljön?
- Var finns kontraktet mellan API och klient?
- Vem ansvarar för att databasschemat har rätt version?
- Vilken data måste överleva när containrar ersätts?
- Vilken konfiguration ska ligga i image och vilken ska tillföras vid start?
- Hur ser vi skillnaden mellan att en process har startat och att tjänsten faktiskt är redo?
- Vilka artefakter behöver en mottagare för att kunna starta samma tjänst i sin egen miljö?

## En rekommenderad väg, inte en katalog över alternativ

För nästan varje del av stacken finns flera rimliga lösningar. Frontend kan serveras på andra sätt än med Nginx. API:t kan byggas med andra Java-ramverk. Databasen kan vara en annan relationsdatabas. Containerorkestreringen kan flyttas från Docker Compose till en större plattform.

Boken försöker inte jämföra alla dessa möjligheter. I stället följer den en rekommenderad huvudväg hela vägen från källkod till körbar tjänst. Alternativ tas upp när de förändrar en viktig avvägning, men huvudtexten prioriterar en konsekvent lösning som går att följa och reproducera.

Det gör också att teknikversioner måste behandlas med viss disciplin. Referensimplementationen är låst till dokumenterade versioner vid den revision som boken bygger på, men exakta patchversioner är inte arkitekturprinciper. Versionsberoende kommandon och konfigurationer behöver därför verifieras nära publiceringstillfället. De långlivade resonemangen i boken handlar i första hand om ansvar, gränser, dataflöden och leveransbarhet.

## Hur boken är upplagd

De första kapitlen etablerar helheten: vad vi menar med en körbar tjänst, hur TaskBoards arkitektur ser ut och hur projektet organiseras för utveckling och leverans.

Därefter behandlas frontenden, först som PWA-arkitektur och sedan som React/TypeScript-applikation. Backenden följer med Quarkus, JPA, PostgreSQL och Flyway. När delarna är etablerade följer vi anrop genom hela stacken och diskuterar konfiguration och säkerhetsgränser.

Den sista tredjedelen flyttar fokus från funktion till leverans. Vi testar den sammansatta tjänsten, bygger frontend och backend som Docker-images, binder samman dem med Docker Compose och diskuterar vad som krävs för att lösningen ska vara driftbar och reproducerbar över tid.

Du kan läsa boken från början till slut, men strukturen är också avsedd att fungera som referens. Den som redan förstår exempelvis React-delen kan gå direkt till Quarkus, Flyway eller containeriseringen och fortfarande känna igen samma TaskBoard och samma arkitektur.

Det genomgående målet är enkelt att formulera men kräver att många små beslut hänger ihop: **kod ska bli en tjänst som någon annan faktiskt kan starta**.
