# 14. Den kompletta tjänsten med Docker Compose

I föregående kapitel byggde vi två applikationsspecifika Docker-images: en webbimage som innehåller den byggda PWA:n och Nginx, och en backendimage som innehåller Quarkus-applikationen och Java-runtime. PostgreSQL kommer från en färdig databasimage.

Men tre images är fortfarande inte en tjänst.

En mottagare behöver veta vilka containrar som ska startas, hur de hittar varandra, vilka värden som ska konfigureras, vilken port som ska vara publik, vilken data som måste överleva en omstart och i vilken ordning delarna blir redo. Det är den sammanhållande rollen som Docker Compose får i TaskBoard.

Referensimplementationens `docker-compose.yml` är medvetet liten. Den beskriver tre services:

```text
web
 |
 v
backend
 |
 v
db
```

och en persistent volume:

```text
taskboard-postgres
```

Det räcker för att göra samma arkitektur som vi tidigare beskrivit till en startbar enhet.

## Compose beskriver en körning, inte en ny image

Dockerfile och Compose-fil svarar på olika frågor.

En Dockerfile svarar i första hand på:

> Hur byggs en image som kan köra den här delen av systemet?

Compose svarar på:

> Vilka services ingår i installationen, hur konfigureras de och hur kopplas de ihop när de körs?

TaskBoards Compose-fil börjar därför med tre tjänstdefinitioner:

```yaml
services:
  db:
    ...

  backend:
    ...

  web:
    ...
```

`db` använder en färdig image. `backend` och `web` byggs från projektets egna Dockerfiles.

```yaml
db:
  image: postgres:18.4-alpine
```

respektive:

```yaml
backend:
  build:
    context: ./backend
```

och:

```yaml
web:
  build:
    context: ./frontend
```

Det gör Compose-filen till installationsbeskrivningen för hela referenstjänsten, samtidigt som bygginstruktionerna fortfarande ligger nära respektive applikationsdel.

## Tre services med olika ansvar

Compose-modellen blir enklare när varje service har ett tydligt ansvar.

### `db`

Databasservicen ansvarar för PostgreSQL-processen och den persistenta datan. Den känner inte till React och behöver inte veta att Nginx finns.

### `backend`

Backendservicen kör Quarkus, äger API:t och ansluter till PostgreSQL. Den behöver databasens adress och credentials men behöver inte känna till värdens publicerade webbport.

### `web`

Webbservicen är installationens publika HTTP-ingång. Den serverar frontendfilerna och proxar `/api` vidare till backend.

Det ger samma ansvarskedja som i kapitel 2, men nu uttryckt som körbar konfiguration:

```text
web:80
  |
  | proxy_pass http://backend:8080
  v
backend:8080
  |
  | jdbc:postgresql://db:5432/...
  v
db:5432
```

Hostmaskinen behöver inte känna till backendens eller databasens container-IP-adresser. Compose-nätverket och intern DNS sköter service discovery.

## Standardnätverket räcker för den här referensen

TaskBoards Compose-fil innehåller ingen explicit `networks:`-sektion. Det betyder inte att containrarna saknar nätverk.

Compose skapar normalt ett projektspecifikt standardnätverk och ansluter services till det. På samma nätverk kan en service nå en annan via servicens namn. Därför fungerar adressen:

```text
backend:8080
```

från `web`, och:

```text
db:5432
```

från `backend`.

Docker rekommenderar att services adresseras med servicename snarare än med container-IP, eftersom IP-adresser kan ändras när containrar återskapas. (Docker Docs, *Networking in Compose*.)

Det är därför backendens JDBC-URL är:

```yaml
QUARKUS_DATASOURCE_JDBC_URL: jdbc:postgresql://db:5432/${POSTGRES_DB:-taskboard}
```

Den innehåller inte `localhost` och ingen hårdkodad IP-adress.

En viktig avgränsning är dock att standardnätverket inte är samma sak som strikt nätverkssegmentering. Alla tre TaskBoard-services ligger i samma Compose-standardnät. Databasen är inte publicerad till värden, men andra services på samma nätverk kan i princip nå dess interna port.

För en liten referensimplementation är det en rimlig kompromiss. En hårdare produktionsdesign kan använda separata frontend- och backendnätverk så att webcontainern inte alls delar nätverk med databasen.

## Bara webbservicen publiceras till värden

Den enda `ports:`-sektionen finns på `web`:

```yaml
ports:
  - "${TASKBOARD_PORT:-8080}:80"
```

Det betyder att containerport 80 mappas till en port på värdmaskinen. Om `TASKBOARD_PORT` inte sätts används 8080.

En lokal start kan därför öppnas på:

```text
http://localhost:8080
```

Om en annan värdport behövs kan den anges utan att imagen byggs om:

```bash
TASKBOARD_PORT=18080 docker compose up
```

Backend har ingen `ports:`-sektion och databasen har ingen `ports:`-sektion. De är därmed inte publicerade direkt på värdens nätverksinterface av den här Compose-filen.

Detta är en central del av tjänstens yttre gräns:

```text
värd / klient
     |
     | publicerad port
     v
    web
     |
     | internt Compose-nät
     v
 backend
     |
     | internt Compose-nät
     v
    db
```

I kapitel 11 såg vi varför detta är en bra grundegenskap, även om det inte ersätter autentisering, TLS eller övrig härdning.

## Miljövariabler binder ihop deployment och applikation

Databasservicen definierar tre centrala värden:

```yaml
environment:
  POSTGRES_DB: ${POSTGRES_DB:-taskboard}
  POSTGRES_USER: ${POSTGRES_USER:-taskboard}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-taskboard-change-me}
```

Samma Compose-variabler används när backendens Quarkus-konfiguration skapas:

```yaml
environment:
  QUARKUS_DATASOURCE_JDBC_URL: jdbc:postgresql://db:5432/${POSTGRES_DB:-taskboard}
  QUARKUS_DATASOURCE_USERNAME: ${POSTGRES_USER:-taskboard}
  QUARKUS_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD:-taskboard-change-me}
```

Det är ett enkelt men viktigt mönster: deploymenten har en gemensam källa för databasnamn och credentials, medan varje container får värden i den form dess egen runtime förstår.

PostgreSQL känner till `POSTGRES_USER`.

Quarkus känner till `QUARKUS_DATASOURCE_USERNAME`.

Compose knyter ihop dem.

Det gör också att applikationsimagen inte behöver byggas om bara för att ett installationsspecifikt användarnamn eller lösenord ändras.

Som vi konstaterade i kapitel 11 är standardlösenordet bara lämpligt som utvecklingsfallback. En verklig deployment ska sätta ett starkt värde och helst använda en mer ändamålsenlig secret-hantering.

## Databasdata måste leva längre än containern

PostgreSQL-servicen monterar en named volume:

```yaml
volumes:
  - taskboard-postgres:/var/lib/postgresql
```

och längst ned i filen deklareras:

```yaml
volumes:
  taskboard-postgres:
```

Det skiljer datans livscykel från containerinstansens livscykel.

En container kan återskapas när imagen uppdateras eller konfigurationen ändras. Om databasen bara lagrade data i containerns skrivbara lager skulle den kopplingen vara farlig. En named volume ligger utanför den enskilda containerns lager och kan återmonteras när en ny databascontainer skapas.

Det innebär inte att en volume är en backup. En volume skyddar framför allt data från att försvinna bara för att containern ersätts. Backup, restore och katastrofåterställning är separata driftfrågor som vi återkommer till i kapitel 15.

TaskBoard använder `/var/lib/postgresql` eftersom PostgreSQL 18-versionen av den officiella Docker-imagen använder den nya 18+-layout som vi redan behandlade i kapitel 8.

## Startordning är inte samma sak som readiness

En vanlig missuppfattning är att följande automatiskt löser alla startberoenden:

```yaml
depends_on:
  - db
```

Det uttrycker en dependency, men en startad databascontainer kan fortfarande vara mitt i sin initiering när backend försöker ansluta.

Docker Compose skiljer därför mellan att en dependency har startats och att den har blivit `healthy`. Med den långa `depends_on`-formen kan en service ange:

```yaml
condition: service_healthy
```

Compose väntar då på dependency-servicens healthcheck innan den beroende servicen startas. (Docker Docs, *Control startup and shutdown order in Compose*.)

TaskBoard använder precis detta i två steg.

## Databasen får bevisa att den är redo

PostgreSQL-servicen har:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-taskboard} -d ${POSTGRES_DB:-taskboard}"]
  interval: 5s
  timeout: 3s
  retries: 10
  start_period: 5s
```

`pg_isready` testar om PostgreSQL accepterar anslutningar för den valda databasmiljön.

Backend deklarerar sedan:

```yaml
depends_on:
  db:
    condition: service_healthy
```

Det skapar denna sekvens:

```text
starta db
   |
   v
vänta på db healthcheck
   |
   v
starta backend
```

Det är bättre än en godtycklig `sleep 10`, eftersom readiness mäts utifrån ett faktiskt tillstånd i databasen i stället för en uppskattad väntetid.

## Backend får i sin tur bevisa sin readiness

Backendservicen har en egen healthcheck:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget -q -O - http://localhost:8080/q/health/ready >/dev/null 2>&1 || exit 1"]
  interval: 5s
  timeout: 3s
  retries: 12
  start_period: 10s
```

Den använder Quarkus readiness-endpoint:

```text
/q/health/ready
```

`web` deklarerar därefter:

```yaml
depends_on:
  backend:
    condition: service_healthy
```

Hela startkedjan blir alltså:

```text
db startar
   |
   v
db blir healthy
   |
   v
backend startar
   |
   v
backend blir healthy
   |
   v
web startar
```

Det är en betydligt starkare modell än en ren startordning.

Samtidigt ska vi inte övertolka den. Healthchecken säger att processen uppfyller den readiness-signal vi har valt. Den bevisar inte att varje användarflöde i systemet fungerar. Därför avslutas CI-kedjan fortfarande med ett full-stack-smoke-test genom Nginx, API och databas.

## `docker compose up` bygger ihop delarna

I en katalog med TaskBoards Compose-fil kan hela stacken byggas och startas med:

```bash
docker compose up --build
```

På en hög nivå händer då följande:

```text
1. Compose läser tjänstdefinitionerna
2. frontend- och backend-images byggs
3. standardnätverk och volume skapas vid behov
4. db-containern startas
5. Compose väntar på db-health
6. backend-containern startas
7. Flyway migrerar databasschemat vid Quarkus-start
8. Hibernate validerar schemat
9. Compose väntar på backend-readiness
10. web-containern startas
11. värdporten binds till web:80
```

Punkt 7 och 8 utförs av applikationen, inte av Compose. Det är viktigt att hålla isär ansvaren.

Compose orkestrerar containrar och deras beroenden.

Quarkus/Flyway ansvarar för applikationens databasmigration.

PostgreSQL ansvarar för själva databasen.

Nginx ansvarar för den publika HTTP-ingången.

## `docker compose up --wait` passar automatiserad verifiering

Projektets GitHub Actions-workflow använder en något annorlunda start:

```bash
docker compose up -d --wait --wait-timeout 120
```

`-d` kör containrarna i bakgrunden. `--wait` gör kommandot användbart i automatisering genom att inte betrakta stackstarten som färdig förrän services är running/healthy enligt deras konfiguration, med en uttrycklig timeout i workflowen.

Det gör att nästa CI-steg kan utgå från en tydligare precondition:

```text
Compose-starten lyckades
          |
          v
kör smoke-testet
```

Om en service blir unhealthy faller startsteget och workflowen skriver ut containerstatus och loggar. Det är just den mekanismen som tidigare hjälpte oss att isolera ett fel till webbcontainerns healthcheck.

## Stänga ned är också en del av livscykeln

För en lokal utvecklingskörning kan stacken stoppas med:

```bash
docker compose down
```

Det tar bort containrarna och Compose-nätverket, men en named volume tas normalt inte bort bara av `down`.

I CI vill vi däremot inte lämna testdata efter körningen. Workflowen använder därför:

```bash
docker compose down -v --remove-orphans
```

`-v` tar bort de volumes som hör till Compose-projektet. Det är rimligt i en isolerad, tillfällig testmiljö men skulle vara ett farligt standardkommando för en installation vars PostgreSQL-volume innehåller värdefull produktionsdata.

Det är ett bra exempel på varför samma Compose-fil kan användas i flera miljöer medan livscykelkommandona fortfarande behöver väljas med omsorg.

## Compose ger portabilitet, inte full miljöidentitet

En Compose-fil minskar antalet manuella installationssteg kraftigt. En mottagare behöver inte separat konfigurera en Nginx-installation, en lokal Java-process och en PostgreSQL-instans för att prova hela TaskBoard.

Men Compose gör inte alla miljöer identiska.

Värdmaskinen bidrar fortfarande med exempelvis:

- container runtime och Compose-version,
- CPU-arkitektur,
- tillgängligt minne och lagring,
- nätverks- och brandväggsregler,
- DNS och eventuell extern TLS-terminering,
- backuphantering,
- övervakning och logginsamling.

Dessutom kan en image-tagg peka på ett annat image-innehåll vid en senare tidpunkt om den inte låses med digest.

Compose ger därför en **portabel tjänstedefinition**, men inte automatiskt en fullständigt reproducerbar eller produktionshärdad installation. Det är precis de två steg som kapitel 15 och 16 bygger vidare på.

## Vad Compose-filen gör — och inte gör

TaskBoards `docker-compose.yml` gör följande:

- definierar tre runtime-services,
- bygger frontend och backend,
- väljer PostgreSQL-image,
- ger services intern name-based discovery,
- publicerar bara webbservicen till värden,
- förmedlar databasens runtime-konfiguration,
- monterar persistent PostgreSQL-volume,
- väntar på databasens health innan backend startas,
- väntar på backendens health innan webben startas.

Den gör däremot inte följande:

- autentiserar användare,
- tillhandahåller TLS-certifikat,
- skapar databasbackup,
- skickar loggar till en central loggtjänst,
- konfigurerar extern övervakning,
- isolerar web och db i separata nätverk,
- låser alla images till immutable digests,
- definierar en strategi för uppgradering och rollback.

Det är inte ett misslyckande. Det är en sund gräns för en liten referensdeployment.

En teknisk installation blir lätt svår att förstå om varje produktionsfråga löses på en gång. TaskBoard visar i stället ett stegvis mönster:

```text
källkod
   |
   v
byggbara images
   |
   v
Compose-definierad tjänst
   |
   v
driftbar installation
   |
   v
reproducerbar leverans
```

## Från startbar till driftbar

Efter detta kapitel har TaskBoard en komplett, startbar tjänstedefinition. En mottagare kan bygga och starta alla tre delarna med Compose och behöver bara exponeras för webbporten.

Men en tjänst som kan startas är inte automatiskt en tjänst som är redo att förvaltas över tid.

När databasen innehåller viktig data uppstår frågor som:

- Hur tar vi backup och hur provar vi restore?
- Hur observerar vi att tjänsten mår bra efter start?
- Hur ser vi loggar när något går fel?
- Hur hanterar vi uppgraderingar utan att förlora data?
- Vad behöver flyttas från utvecklingsfallbacks till riktig driftkonfiguration?

Det är skillnaden mellan **körbar** och **driftbar**.

Nästa kapitel tar därför Compose-installationen vi nu har och granskar vad som krävs för att flytta den från lokal, verifierad körning till en tjänst som någon faktiskt kan drifta och underhålla.
