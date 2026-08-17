# 1. Från kod till körbar tjänst

Två kodbaser kan vara fullt fungerande och ändå inte utgöra en levererbar tjänst. Frontenden kanske körs med en utvecklingsserver, backenden från IDE:n och databasen i en lokal container som bara utvecklaren känner till. API-anropen fungerar eftersom rätt portar råkar vara öppna och rätt miljövariabler redan finns på den egna datorn.

Det är ett användbart utvecklingsläge, men det är inte samma sak som att ha en tjänst som kan överlämnas.

I den här boken betyder **körbar tjänst** att alla nödvändiga delar kan byggas, konfigureras, startas och verifieras som en sammanhängande enhet utan att mottagaren behöver återskapa utvecklarens arbetsstation. För TaskBoard innebär det en frontend som går att hämta i webbläsaren, ett REST-API som frontenden kan anropa, ett persistent datalager och en definierad väg från externa HTTP-anrop till interna komponenter.

Det är slutmålet vi börjar med. Först därefter går vi ned i detaljerna.

## TaskBoard som referenstjänst

TaskBoard är avsiktligt liten. En uppgift innehåller följande grunddata:

- ett unikt id,
- titel och valfri beskrivning,
- status `OPEN`, `IN_PROGRESS` eller `DONE`,
- prioritet `LOW`, `NORMAL` eller `HIGH`,
- valfritt förfallodatum,
- tidpunkter för när posten skapades och senast uppdaterades.

Användaren kan skapa, visa, uppdatera och ta bort uppgifter. API:t kan dessutom lista och filtrera uppgifter efter status och prioritet. Frontenden erbjuder en mindre del av den funktionaliteten direkt i användargränssnittet: den kan skapa uppgifter, visa listan, ändra status och ta bort poster.

Domänen är tillräckligt stor för att ge oss riktiga HTTP-anrop, validering, databastransaktioner, migrationer och persistens, men tillräckligt liten för att arkitekturfrågorna ska stå i centrum.

Referensimplementationen finns under `code/taskboard/`. Den katalogen är bokens tekniska facit. När ett senare kapitel visar ett konkret konfigurationsfält eller ett kodutdrag ska det gå att koppla tillbaka till den körbara lösningen.

## Vad består tjänsten av?

I den färdiga körmiljön består TaskBoard av tre runtime-delar:

1. **web** — Nginx serverar den byggda React/PWA-frontenden och tar emot externa HTTP-anrop.
2. **backend** — Quarkus exponerar REST-API:t och innehåller applikations- och persistenslogik.
3. **db** — PostgreSQL lagrar TaskBoards persistenta data.

Docker Compose startar och kopplar samman dessa delar. Den förenklade kedjan är:

```text
Webbläsare
    |
    v
Nginx
    |
  /api
    v
Quarkus
    |
    v
PostgreSQL
```

Det här diagrammet är medvetet enkelt. Kapitel 2 går djupare in i gränserna, nätverket och trafikflödet. Här räcker det att konstatera att varje del har ett eget huvudansvar och att tjänsten bara fungerar om ansvaren kopplas ihop på ett förutsägbart sätt.

### Frontenden är inte sin utvecklingsserver

React- och TypeScript-koden ligger i `code/taskboard/frontend/`. Under utveckling körs den med Vite. Det ger snabb omladdning, utvecklingsfunktioner och en proxy som kan vidarebefordra `/api` till en lokalt körande Quarkus-instans.

Men Vite är inte TaskBoards produktionsserver. När frontend-imagen byggs kompileras applikationen till statiska filer. I runtime-imagen är det Nginx som serverar dessa filer.

Skillnaden är viktig eftersom utvecklingsmiljön annars lätt blir en dold del av produktionsarkitekturen. En port som bara existerar när `npm run dev` körs ska inte vara ett krav för den färdiga tjänsten.

### Backend är ett API, inte en publik webbplats

Backenden ligger i `code/taskboard/backend/` och körs på Quarkus. Den exponerar resurser under `/api/tasks` för listning, läsning, skapande, uppdatering och borttagning.

Quarkus-processen är däremot inte tjänstens avsedda publika ingång i Compose-miljön. Webbläsaren går via Nginx. Nginx serverar frontend och vidarebefordrar API-trafiken till backendcontainern.

Det ger ett enkelt externt gränssnitt: klienten behöver förhålla sig till en och samma HTTP-origin och kan anropa relativa adresser som `/api/tasks`. Hur reverse proxy-konfigurationen fungerar och vilka säkerhetsmässiga konsekvenser den får behandlas senare.

### Databasen är intern persistence

PostgreSQL lagrar TaskBoards data. I Compose-modellen publiceras ingen databasport till värddatorn. Backenden når databasen på det interna Compose-nätverket med servicenamnet `db`.

Det är en viktig arkitekturgräns: en webbläsare ska inte känna till databasens adress, credentials eller schema. Frontenden pratar HTTP med API:t. Backenden äger åtkomsten till persistence.

Databasschemat hanteras med Flyway. Den första migrationen skapar TaskBoards tabell och index. Hibernate ORM är konfigurerat för att validera att JPA-modellen är förenlig med det schema som migrationerna har etablerat. På så sätt skiljs två ansvar åt: Flyway förändrar schemat, medan ORM-lagret använder och kontrollerar det.

## Från fungerande delar till fungerande helhet

En levererbar tjänst behöver mer än rätt ramverk. För TaskBoard måste åtminstone följande frågor ha konkreta svar.

### Hur byggs varje del?

Frontend och backend har separata byggkedjor. Frontenden använder Node-baserade verktyg för att typkontrollera och bygga webbapplikationen. Backenden byggs med Maven och Quarkus.

När Docker-images skapas används multi-stage builds. Byggverktygen behövs i build-stegen men inte nödvändigtvis i de färdiga runtime-images. Frontendens runtime-image behöver exempelvis Nginx och de färdigbyggda statiska filerna, inte hela Node-utvecklingsmiljön.

Det här är en första aspekt av reproducerbarhet: byggprocessen uttrycks som kod och konfiguration i projektet i stället för att vara en serie manuella steg som bara en utvecklare känner till.

### Hur konfigureras miljön?

Databasnamn, användare, lösenord och publicerad HTTP-port är exempel på värden som kan skilja sig mellan körmiljöer. De ska inte kräva ändringar i applikationskoden.

TaskBoards Compose-fil tillför databasanslutningen till Quarkus genom miljövariabler. En `.env.example` visar vilka värden som kan sättas utan att verkliga credentials behöver checkas in i projektet.

Det är en enkel modell, men principen är större än TaskBoard: samma byggda artifact bör så långt det är rimligt kunna användas i flera miljöer med konfiguration som tillförs vid start.

### Hur vet vi att komponenterna är redo?

En startad process är inte alltid en användbar tjänst. PostgreSQL behöver initiera databasen innan backend kan ansluta. Quarkus behöver starta, köra Flyway-migrationer och bli redo innan Nginx-baserade end-to-end-kontroller kan förvänta sig ett fungerande API.

TaskBoards Compose-konfiguration använder healthchecks och beroenden för att göra uppstarten mer deterministisk. Databasen kontrolleras med `pg_isready`. Backend använder Quarkus readiness-endpoint. Frontend-imagen har en lokal Nginx-healthcheck mot `/healthz`.

Healthchecks ersätter inte all driftövervakning, men de ger Compose en konkret signal om när en komponent kan betraktas som frisk i just den här startkedjan.

### Vad ska överleva en omstart?

Containrar är utbytbara. TaskBoards PostgreSQL-data ska däremot inte försvinna bara för att databascontainern ersätts.

Därför använder Compose en namngiven Docker-volume för PostgreSQLs datakatalog. Applikations- och webbcontainrarna behöver ingen motsvarande persistent lokal state i referensarkitekturen; de kan byggas och ersättas från sina images.

Detta är en central skillnad mellan **compute** och **persistent data**. En driftmodell måste veta vilken del som får försvinna och återskapas och vilken del som måste bevaras, säkerhetskopieras och kunna återställas.

## Utvecklingsmiljö och körmiljö är två olika systembilder

En vanlig källa till onödig komplexitet är att försöka göra utvecklingsmiljön och den färdiga körmiljön identiska. De behöver vara **konsekventa**, men de har olika syften.

I lokal frontendutveckling är snabb återkoppling viktig. Därför används Vite som utvecklingsserver. Den proxar API-anrop till Quarkus, vilket gör att frontendkoden kan använda samma relativa `/api`-adresser som i den färdiga lösningen.

I backendutveckling kan Quarkus köras i dev mode. Med Docker tillgängligt kan Quarkus Dev Services tillhandahålla en PostgreSQL-instans utan att utvecklaren behöver starta den fullständiga Compose-miljön för varje kodändring.

Den produktionslika körmiljön har ett annat mål. Där ska inga utvecklingsservrar behövas. Frontenden är färdigbyggd. Nginx är publik ingång. Quarkus kör sin runtime-artifact. PostgreSQL använder persistent lagring. Compose beskriver hur delarna kopplas samman.

Skillnaden kan sammanfattas så här:

| Område | Utvecklingsmiljö | Produktionslik Compose-miljö |
|---|---|---|
| Frontendserver | Vite | Nginx |
| Frontendkod | källkod med snabb utvecklingsloop | byggda statiska filer |
| API-väg | Vite proxy → Quarkus | Nginx `/api` → Quarkus |
| Backend | Quarkus dev mode eller vanlig lokal körning | Quarkus runtime-container |
| Databas | Dev Services/lokal PostgreSQL | PostgreSQL-container med volume |
| Huvudmål | snabb utveckling och felsökning | reproducerbar körning och överlämning |

Det viktiga är att miljöerna delar kontrakt. Frontenden ska exempelvis inte behöva en helt annan API-strategi bara för att den byggs för runtime. Databasschemat ska inte skapas på ett sätt i utveckling och på ett annat i leveransen. Skillnaderna ska vara medvetna, inte historiska olyckor.

## Referensimplementationen verifieras som en helhet

Det går att ha en grön frontend-build, en grön backend-build och ändå en trasig tjänst. Integrationsfel uppstår ofta i skarvarna: fel port, fel miljövariabel, fel enumvärde, en volume på fel sökväg, en healthcheck som träffar fel adress eller en Docker-build som inte producerar den katalog som runtime-steget förväntar sig.

TaskBoards CI-workflow är därför byggt för att gå längre än komponentkompilering.

I den verifierade kedjan gör GitHub Actions i huvudsak följande:

1. validerar referensprojektets statiska kontrakt,
2. bygger React/TypeScript-frontenden,
3. kör Maven-verifiering av Quarkus-backenden,
4. validerar Docker Compose-konfigurationen,
5. bygger Docker-images,
6. startar `db`, `backend` och `web` och väntar på deras hälsosignaler,
7. gör ett smoke test via den publicerade Nginx-porten,
8. skapar en uppgift via `/api/tasks`, hämtar den igen och verifierar centrala fält.

Den sista punkten är viktig. Testet går genom samma yttre ingång som en klient använder. För att det ska lyckas måste Nginx-konfigurationen fungera, Quarkus kunna hantera requesten, Flyway ha etablerat rätt schema och PostgreSQL kunna lagra och returnera data.

Det gör inte smoke-testet till en fullständig teststrategi. Det bevisar exempelvis inte att alla felvägar, UI-tillstånd eller domänregler fungerar. Men det verifierar en kritisk egenskap: **den levererade systemformen går att starta och dess viktigaste requestkedja fungerar**.

Kapitel 12 återkommer till hur detta kompletteras med tester på lägre och högre nivåer.

## Vad betyder reproducerbar leverans?

Ordet *reproducerbar* används ofta slarvigt. I den här boken betyder det inte att varje byggning nödvändigtvis producerar byte-identiska filer. Det betyder i första hand att den information som krävs för att bygga och köra tjänsten finns uttryckt och versionshanterad på ett sådant sätt att en annan miljö kan upprepa processen med förutsägbart resultat.

För TaskBoard innebär det bland annat att följande finns i projektet:

- frontendens och backendens byggdefinitioner,
- Dockerfiles för de två egna images,
- en Compose-fil som beskriver tjänster, beroenden och persistent lagring,
- databasens Flyway-migrationer,
- exempel på extern konfiguration,
- dokumenterade teknikversioner,
- automatiserad verifiering av den sammansatta tjänsten.

Senare kapitel skärper detta perspektiv med versionssättning, image-taggar eller digests, releaseartefakter, installationsinstruktioner och uppgraderingsflöden. Men redan här går det att se principen: leveransen består inte bara av kompilerad kod. Den består också av kunskapen om **hur koden blir ett körande system**, uttryckt på ett sätt som går att versionera och testa.

## Vad den här arkitekturen medvetet inte löser

Att TaskBoard går att bygga och starta innebär inte att alla produktionsfrågor är lösta.

Referensimplementationen har exempelvis ingen fullständig autentisering eller auktorisering. TLS-terminering är inte huvudproblemet i den lokala Compose-modellen. Observability är begränsad jämfört med vad en större produktionsmiljö kan kräva. PostgreSQL-backup och restore måste behandlas som egna driftprocesser. Skalning över flera värdar, rolling deployments och plattformsorkestrering ligger utanför huvudlösningen.

Dessa luckor är avsiktliga. En bra referensarkitektur behöver visa var nya förmågor ska kopplas in utan att låtsas att en liten demonstrationsmiljö redan löser allt.

Boken kommer därför återkommande att skilja mellan tre saker:

- det som krävs för att TaskBoard ska fungera,
- det som krävs för att TaskBoard ska vara rimligt driftbar i en mindre egen miljö,
- det som skulle behöva läggas till när kravbilden blir större.

## Centrala fakta

- TaskBoard är bokens genomgående, körbara referensimplementation.
- Den färdiga tjänsten består av Nginx/frontend, Quarkus-backend och PostgreSQL.
- Nginx är den yttre HTTP-ingången och vidarebefordrar `/api` till backend.
- Frontenden byggs med Vite men serveras inte av Vite i den produktionslika körmiljön.
- Quarkus äger REST-API och applikationslogik; PostgreSQL är internt persistent datalager.
- Flyway versionshanterar databasschemat och Hibernate ORM validerar modellen mot det.
- Docker Compose beskriver hur runtime-delarna startas, konfigureras, hälsokontrolleras och kopplas samman.
- Persistent databasdata hålls utanför den utbytbara databascontainerns livscykel genom en Docker-volume.
- Utvecklingsmiljö och körmiljö har olika syften men ska dela samma centrala kontrakt.
- CI-verifieringen bygger och startar hela referensimplementationen och smoke-testar kedjan från Nginx till PostgreSQL.

## Nästa steg

Vi har nu definierat vad slutmålet är: inte bara fungerande frontend- och backendkod, utan en sammanhängande tjänst med en tydlig yttre ingång, intern persistens, reproducerbar byggprocess och verifierbar startkedja.

I nästa kapitel zoomar vi in på arkitekturen. Där blir gränserna mellan webbläsare, Nginx, Quarkus och PostgreSQL mer precisa, och vi följer hur trafik och ansvar förflyttas genom systemet.
