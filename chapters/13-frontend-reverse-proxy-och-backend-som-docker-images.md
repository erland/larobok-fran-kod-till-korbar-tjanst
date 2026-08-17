# 13. Frontend, reverse proxy och backend som Docker-images

När en applikation fungerar lokalt återstår fortfarande en avgörande fråga: **vad är egentligen den körbara artefakten?**

I utvecklingsmiljön består TaskBoard av källkod, Node.js, npm, Vite, Maven, en JDK, Quarkus dev mode och flera hjälpverktyg. Det är en bra miljö för att ändra kod. Det är däremot en dålig beskrivning av vad en mottagare ska behöva installera och förstå för att köra tjänsten.

Containeriseringen skapar en tydligare gräns. För TaskBoard byggs två egna images:

```text
frontend-källkod                     backend-källkod
       |                                     |
       v                                     v
 Node + npm + Vite                      Maven + JDK
       |                                     |
       v                                     v
 statiska filer                       Quarkus fast-jar
       |                                     |
       v                                     v
 Nginx runtime-image                  Java runtime-image
```

PostgreSQL behöver ingen egen TaskBoard-image. Där använder Compose en färdig databasimage. Frontend och backend innehåller däremot applikationsspecifik kod och behöver byggas från projektets egna Dockerfiles.

Det centrala mönstret i båda Dockerfilerna är detsamma: **byggverktygen hör hemma i build-steget, inte automatiskt i runtime-imagen**.

## En image är en leveransgräns

En Docker-image ska inte ses som en liten virtuell utvecklingsmaskin. Den är bättre att se som en versionsbar leveransartefakt som innehåller det som processen behöver för att starta och köra.

För TaskBoards webbdel betyder det:

```text
Nginx
nginx.conf
byggd HTML/CSS/JavaScript/PWA-assets
```

För backend betyder det:

```text
Java runtime
Quarkus runtime-filer
applikationskod och beroenden
```

Det behövs inte en TypeScript-kompilator i webbcontainern när TypeScript redan har kompilerats. Det behövs inte Maven i backendcontainern när applikationen redan har paketerats.

Detta ger tre praktiska fördelar.

För det första blir runtime-miljön mindre komplex. Färre verktyg behöver finnas installerade och förstås när tjänsten körs.

För det andra minskar kopplingen till utvecklingsmaskinen. Build-steget beskriver exakt hur artefakten produceras, och runtime-steget beskriver exakt vad den behöver.

För det tredje blir ansvarsfördelningen tydligare. Om något går fel i webbcontainern behöver vi i första hand tänka på Nginx, dess konfiguration och de statiska filerna — inte på Vites dev server eller npm.

Docker kallar detta **multi-stage builds**. En Dockerfile kan ha flera `FROM`-instruktioner, där varje `FROM` startar ett nytt build stage. Filer kan sedan kopieras från ett tidigare stage till ett senare, medan resten av build-miljön lämnas kvar. (Docker Docs, *Multi-stage builds*.)

## Frontend-imagen byggs i två världar

TaskBoards frontend-Dockerfile börjar så här:

```dockerfile
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build
```

Detta är inte webbservern. Det är en tillfällig byggmiljö.

`node:24-alpine` tillhandahåller Node.js och npm. Projektets `package.json` kopieras in och beroendena installeras. Därefter kopieras källkoden in och produktionsbygget körs.

I TaskBoard betyder:

```bash
npm run build
```

att TypeScript först byggs och att Vite därefter producerar produktionsfilerna i:

```text
/app/dist
```

Det är `dist` som är frontendens verkliga runtime-artefakt.

Build-steget innehåller däremot mycket som inte behövs när användaren öppnar TaskBoard:

```text
Node.js
npm
node_modules för build
TypeScript
Vite
frontendens källfiler
```

Därför börjar Dockerfilen om med en ny image:

```dockerfile
FROM nginx:1.30.4-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -q -O - http://127.0.0.1/healthz >/dev/null 2>&1 || exit 1
```

Det viktiga är raden:

```dockerfile
COPY --from=build /app/dist /usr/share/nginx/html
```

Den kopierar bara resultatet från det första steget. Build-miljön följer inte med som ett extra lager in i den färdiga runtime-imagen bara för att den användes tidigare i Dockerfilen.

Docker Official Image för Nginx använder `/usr/share/nginx/html` som standardplats för statiskt innehåll och dokumenterar samma grundmönster: bygg eller tillhandahåll statiska filer och lägg dem i Nginx-imagen. (Docker Official Image, *nginx*.)

## Varför inte köra Vite i produktion?

Under utveckling använder vi Vites dev server eftersom den ger snabb återkoppling, modulhantering och hot reload. Det är exakt vad vi vill ha när koden förändras hela tiden.

I den containeriserade tjänsten har uppgiften förändrats. JavaScript, CSS och HTML är redan byggda. Nu behöver vi främst:

- servera statiska filer effektivt,
- hantera SPA-fallback,
- vidarebefordra `/api`,
- styra vissa cache headers,
- erbjuda en enkel health-endpoint.

TaskBoard låter därför Nginx ta över runtime-rollen.

Det är en viktig arkitekturprincip:

> Ett verktyg som är idealiskt för utvecklingsloopen behöver inte vara rätt server i den färdiga tjänsten.

Vi ska inte göra Vite sämre än det är. Vi ska bara inte ge dev servern ett jobb den här arkitekturen har gett till Nginx.

## Nginx-imagen är mer än en statisk filserver

TaskBoards `nginx.conf` gör fyra saker som är viktiga för tjänsten.

Först deklareras frontendens rot:

```nginx
root /usr/share/nginx/html;
index index.html;
```

Sedan finns en health-endpoint:

```nginx
location = /healthz {
    access_log off;
    add_header Content-Type text/plain;
    return 200 'ok';
}
```

Detta gör att containerns healthcheck kan testa själva Nginx-processens HTTP-väg utan att vara beroende av backend eller PostgreSQL.

Tredje uppgiften är reverse proxy:

```nginx
location /api/ {
    proxy_pass http://backend:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Frontendens relativa `/api`-anrop landar alltså i samma container som serverar PWA:n och skickas vidare över Compose-nätverket till tjänsten `backend`.

Slutligen finns SPA-fallbacken:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

Om en fil verkligen finns serveras den. Annars faller Nginx tillbaka till `index.html`, vilket gör att en klientbaserad frontend kan hantera URL:en. TaskBoard använder ännu ingen router, men konfigurationen lämnar utrymme för en sådan utveckling.

Service workern får dessutom en särskild cacheinstruktion:

```nginx
location = /sw.js {
    add_header Cache-Control "no-cache";
    try_files $uri =404;
}
```

Det är alltså Nginx-konfigurationen, inte bara de byggda frontendfilerna, som gör webb-imagen till tjänstens publika HTTP-komponent.

## Healthchecken testar rätt sak — och måste själv fungera

Dockerfilen innehåller:

```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget -q -O - http://127.0.0.1/healthz >/dev/null 2>&1 || exit 1
```

Den detaljen ser trivial ut, men den har redan varit värdefull i referensimplementationens CI.

En tidigare variant använde `localhost`. Containern startade Nginx korrekt men rapporterades ändå som unhealthy. Healthchecken ändrades till explicit IPv4-loopback:

```text
127.0.0.1
```

Efter den ändringen gick startup-fasen vidare.

Lärdomen är större än just adressen:

> En healthcheck är en del av den körbara artefakten och måste testas som sådan.

Det räcker inte att endpointen ser korrekt ut på papperet. Verktyget som används i healthchecken måste finnas i runtime-imagen, adressen måste nå processen och exit-koden måste representera hälsan korrekt.

Detta är också skälet till att healthchecken håller sig lokal. Webbcontainerns egen hälsa ska inte bli `unhealthy` enbart för att databasen är nere. Hela tjänstens funktionsförmåga testas på andra nivåer, bland annat av full-stack-smoke-testet från kapitel 12.

## Backend-imagen använder samma princip

Backendens Dockerfile har också två stages:

```dockerfile
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /workspace
COPY pom.xml ./
RUN mvn -B -DskipTests quarkus:go-offline
COPY src ./src
RUN mvn -B -DskipTests package
```

Det första steget innehåller Maven och en JDK eftersom källkoden måste kompileras och Quarkus-applikationen paketeras.

`pom.xml` kopieras in före `src`. Det gör byggordningen begriplig och ger Docker möjlighet att återanvända tidigare lager när beroendedeklarationerna inte har förändrats men källkoden har gjort det.

TaskBoard använder också:

```bash
mvn -B -DskipTests quarkus:go-offline
```

innan källkoden kopieras. Syftet är att förbereda Quarkus/Maven-beroenden i ett lager som inte behöver byggas om vid varje ren källkodsändring.

Sedan körs:

```bash
mvn -B -DskipTests package
```

och Quarkus producerar sin runtime-distribution.

## Quarkus fast-jar är en katalog, inte bara en fil

Det är här en viktig Quarkus-detalj kommer in.

Quarkus använder `fast-jar` som standard för JAR-paketering. Resultatet ligger under:

```text
target/quarkus-app/
```

och innehåller bland annat:

```text
quarkus-run.jar
lib/
app/
quarkus/
```

Quarkus dokumenterar uttryckligen att hela `quarkus-app`-innehållet behövs för att den paketerade applikationen ska fungera korrekt. Det räcker alltså inte att hitta `quarkus-run.jar` och kopiera bara den till en runtime-image. (Quarkus, *Quarkus and Maven*.)

TaskBoards runtime-stage speglar detta:

```dockerfile
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /workspace/target/quarkus-app/lib/ ./lib/
COPY --from=build /workspace/target/quarkus-app/*.jar ./
COPY --from=build /workspace/target/quarkus-app/app/ ./app/
COPY --from=build /workspace/target/quarkus-app/quarkus/ ./quarkus/
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "quarkus-run.jar"]
```

Runtime-imagen behöver därför en Java Runtime Environment, men inte Maven och inte backendens Java-källkod.

Den kör:

```text
java -jar quarkus-run.jar
```

från `/app`, där fast-jar-strukturen har återskapats.

Detta är ett bra exempel på varför man behöver förstå ramverkets **paketeringsformat**, inte bara programmeringsmodellen. Ett Dockerfile-fel kan uppstå långt efter att Java-kompileringen lyckats.

Referensimplementationen har redan råkat ut för just den klassen av problem: Quarkus-packaging och Docker-kopieringen behövde anpassas så att den verkliga runtime-distributionen följde med. Den fungerande CI-kedjan verifierar nu att imagen faktiskt startar.

## Byggberoenden ska inte blandas ihop med runtime-beroenden

Skillnaden kan sammanfattas så här:

| Komponent | Build-stage | Runtime-stage |
|---|---|---|
| Frontend | Node.js, npm, TypeScript, Vite | Nginx |
| Frontendkod | React/TypeScript-källkod | byggda filer i `dist` |
| Backend | Maven + JDK 21 | JRE 21 |
| Backendkod | Java-källkod | Quarkus `fast-jar` |
| Reverse proxy | – | `nginx.conf` |
| Databas | ingen egen build | PostgreSQL Official Image |

Den här separationen gör inte automatiskt images minimala eller säkra. Men den skapar en stark grund för båda egenskaperna.

## Små images är ett medel, inte målet

Det är lätt att göra image-storlek till en tävling. Mindre images kan ge snabbare överföring och mindre onödig mjukvara, men den minsta möjliga basimagen är inte automatiskt det bästa valet.

TaskBoard använder Alpine-varianter för både Node-builden, Nginx, Maven-builden och Java-runtime. Docker beskriver Alpine-baserade Nginx-images som ett alternativ när liten image-storlek är viktig, men påpekar också skillnader som användningen av `musl` i stället för `glibc` och att många extra verktyg inte ingår. (Docker Official Image, *nginx*.)

För TaskBoards teknikstack fungerar de valda Alpine-images i den verifierade CI-kedjan. Det är den relevanta slutsatsen för referensimplementationen.

En generell regel bör däremot vara:

> Välj den minsta runtime-image som fortfarande är kompatibel, begriplig, underhållbar och verifierad för applikationen.

Om applikationen senare får native libraries, felsökningskrav eller andra OS-beroenden kan ett annat basimageval vara bättre även om imagen blir större.

## `EXPOSE` publicerar inte porten

Båda Dockerfilerna använder `EXPOSE`:

```dockerfile
EXPOSE 80
```

och:

```dockerfile
EXPOSE 8080
```

Det är viktigt att skilja detta från faktisk portpublicering.

`EXPOSE` beskriver vilken port imagen förväntar sig att processen använder. Det gör inte porten automatiskt åtkomlig från värddatorn.

I TaskBoard är det Compose som avgör vad som publiceras. Webbservicen får en host-port. Backend får ingen. Därför kan Nginx nå `backend:8080` på Compose-nätverket utan att Quarkus samtidigt blir en separat publik endpoint från värden.

Image och deployment har alltså olika ansvar:

```text
Dockerfile: vad innehåller processen och vilken port använder den?
Compose:    vilka processer kopplas ihop och vilka portar publiceras?
```

Nästa kapitel går vidare med just den andra frågan.

## Runtime-konfiguration ska inte kräva en ny build

En annan viktig image-egenskap är vad som **inte** bakas in.

Backendens databas-URL, användarnamn och lösenord kommer inte från Dockerfilen. De sätts av Compose som miljövariabler när containern startas.

Det innebär att samma backend-image i princip kan användas i flera miljöer med olika:

```text
databashost
användarnamn
lösenord
```

På motsvarande sätt innehåller frontendens JavaScript relativa `/api`-anrop i stället för en hårdkodad adress till en viss backendserver. Nginx och deploymentmiljön avgör vart `/api` går.

Det här är en central del av en reproducerbar leverans:

> En miljöskillnad ska i första hand vara konfiguration, inte ett skäl att kompilera om samma program till en ny specialimage.

Kapitel 11 tog upp säkerhetsaspekten på denna princip. Kapitel 16 återkommer till den ur release- och överlämningsperspektiv.

## Images är inte immutable om referensen kan flytta sig

När en image väl har byggts är dess innehåll i praktiken en bestämd artefakt. Men Dockerfilens `FROM`-referenser är inte nödvändigtvis lika fixerade över tid.

TaskBoard använder till exempel:

```dockerfile
FROM node:24-alpine
```

Det anger en huvudversion av Node, men inte ett exakt image-digest. En framtida build kan därför få en nyare `24-alpine`-variant än en tidigare build.

Andra referenser är mer precisa, exempelvis:

```dockerfile
FROM nginx:1.30.4-alpine
```

men även ett tag är en mänskligt läsbar referens, inte samma sak som ett innehållsadresserat digest.

Vi behöver inte lösa hela releasepolicyn i detta kapitel. Det viktiga är att skilja två frågor:

1. Är **den byggda imagen** en tydlig runtime-artefakt?
2. Kan vi **reproducera exakt samma image senare** från samma källkod och externa basimages?

TaskBoard har en bra lösning på den första frågan och en medvetet öppen punkt på den andra. Projektets faktakontroll har därför kvar beslutet om bas-/release-images ska låsas med digest i slutlig publiceringspipeline.

Detta tas upp igen i kapitel 16.

## CI testar images, inte bara Dockerfile-syntax

I kapitel 12 såg vi att GitHub Actions först bygger images:

```bash
docker compose build
```

och därefter startar den kompletta tjänsten:

```bash
docker compose up -d --wait --wait-timeout 120
```

Detta är viktigt eftersom ett Dockerfile kan vara syntaktiskt giltigt men ändå producera en oanvändbar runtime-image.

Exempel på fel som bara en verklig build eller start kan avslöja är:

- en sökväg i `COPY --from=build` är fel,
- frontendens `dist` skapas inte där Dockerfilen förväntar sig,
- Quarkus runtime saknar en del av `quarkus-app`,
- `ENTRYPOINT` pekar på fel fil,
- Nginx-konfigurationen är felaktig,
- healthcheckverktyget eller endpointen fungerar inte,
- Java-processen kan inte starta i vald runtime-image.

TaskBoards images är därför inte bara teoretiska exempel i boken. De byggs och startas av projektets kanoniska CI-workflow.

Det är en viktig kvalitetsnivå för en teknisk bok med referenskod: **koden som illustrerar deployment ska själv deployas i verifieringen**.

## Vad respektive image ska ansvara för

Efter containeriseringen kan vi formulera en tydlig ansvarskarta.

### Webb-imagen

Den ska:

- innehålla den byggda PWA:n,
- servera statiska filer,
- exponera HTTP på port 80 inne i containern,
- ge SPA-fallback,
- hantera service worker-cacheheadern,
- proxya `/api` till backend,
- erbjuda lokal `/healthz`.

Den ska inte:

- kompilera TypeScript vid containerstart,
- köra Vite dev server,
- innehålla applikationens databasuppgifter,
- ansvara för backendens readiness.

### Backend-imagen

Den ska:

- innehålla Java-runtime,
- innehålla hela Quarkus fast-jar-distributionen,
- starta `quarkus-run.jar`,
- lyssna på port 8080 inne i containern,
- läsa runtime-konfiguration från miljön.

Den ska inte:

- behöva Maven vid start,
- kompilera Java-källkod när containern startas,
- publicera sin port till omvärlden på egen hand,
- bära PostgreSQL-data.

### PostgreSQL-imagen

Den ska:

- köra databasservern,
- använda den persistenta volym som deploymenten tilldelar,
- hantera TaskBoards relationsdata.

Den behöver ingen specialbyggd TaskBoard-image eftersom schemaevolutionen redan ägs av Flyway i backendens release.

## Från två images till en tjänst

Efter detta kapitel har vi fortfarande inte en komplett installation. Vi har två TaskBoard-specifika runtime-images och en vald PostgreSQL-image.

Det som återstår är att beskriva hur de tre instanserna ska kopplas ihop:

```text
                    host-port
                       |
                       v
               +---------------+
               | web / Nginx   |
               +-------+-------+
                       |
                    /api
                       |
                       v
               +---------------+
               | backend       |
               | Quarkus       |
               +-------+-------+
                       |
                     JDBC
                       |
                       v
               +---------------+
               | db            |
               | PostgreSQL    |
               +---------------+
                       |
                    volume
```

Det är Docker Compose-filens uppgift.

Nästa kapitel lämnar därför frågan **vad finns i varje image?** och går vidare till **hur blir images tillsammans en portabel, startbar tjänst?**
