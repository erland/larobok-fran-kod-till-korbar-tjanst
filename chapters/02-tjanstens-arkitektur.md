# 2. Tjänstens arkitektur

När en webbtjänst består av flera tekniker är den viktigaste arkitekturfrågan sällan vilken teknik som är bäst i isolation. Den avgörande frågan är **var ansvaret ska ligga och hur få vägar det finns mellan delarna**.

TaskBoard använder fyra tydliga nivåer i den körbara kedjan:

```text
Webbläsare
    |
    | HTTP
    v
Nginx
    | \
    |  \ statiska filer
    |   -> React/PWA
    |
    | /api
    v
Quarkus
    |
    | JDBC/JPA
    v
PostgreSQL
```

Diagrammet visar mer än teknikval. Det visar fyra arkitekturgränser:

- webbläsaren känner till den publika HTTP-ingången men inte den interna backenden eller databasen,
- Nginx äger gränsen mellan externa HTTP-anrop och de interna tjänsterna,
- Quarkus äger applikationskontraktet och all åtkomst till persistence,
- PostgreSQL äger den beständiga datan men inte applikationsreglerna.

Det här kapitlet fokuserar på dessa gränser. Senare kapitel går djupare in i respektive teknik, men om gränserna är otydliga hjälper det inte att varje komponent är välskriven var för sig.

## En publik ingång, flera interna ansvar

I TaskBoards produktionslika Compose-miljö är `web` den enda service som publicerar en port till värddatorn:

```yaml
web:
  ports:
    - "${TASKBOARD_PORT:-8080}:80"
```

Backenden har ingen `ports`-mappning. Det har inte heller databasen. Utifrån värddatorn är den avsedda vägen därför:

```text
http://localhost:8080/
```

eller motsvarande adress och port i den miljö där tjänsten körs.

Det förenklar den yttre systembilden. En klient behöver inte veta att frontend och backend är separata processer. Den behöver inte heller känna till vilken intern port Quarkus eller PostgreSQL använder. Det publika kontraktet är HTTP-ingången till Nginx.

Den här modellen är inte unik för Docker Compose. Samma princip kan senare användas bakom en lastbalanserare, ingress eller plattformsrouter. Det som är stabilt är arkitekturgränsen: klienten möter en kontrollerad ingång, medan interna adresser är en driftfråga.

## Same-origin som ett medvetet arkitekturval

Frontendkoden anropar API:t med relativa adresser, exempelvis:

```text
/api/tasks
```

Den behöver alltså inte innehålla en hårdkodad backendadress som `http://backend:8080` eller `https://api.example.se`.

När sidan och API:t nås genom samma schema, värd och port behandlar webbläsaren dem som samma origin. För TaskBoard betyder det i den produktionslika modellen att både webbappen och API-anropen går via Nginx.

Det ger flera praktiska fördelar:

- frontendens runtime-konfiguration behöver inte känna till backendcontainerns nätverksnamn,
- klienten behöver bara en publik basadress,
- grundflödet kräver ingen separat CORS-konfiguration mellan frontend och backend,
- TLS kan i en riktig miljö termineras vid den publika HTTP-gränsen utan att frontend behöver veta hur intern trafik är organiserad.

Same-origin löser däremot inte autentisering, auktorisering eller skydd av API:t. Det minskar antalet nätverksgränser som webbläsaren behöver hantera, men det gör inte anrop betrodda. Säkerhetsfrågorna behandlas i kapitel 11.

## Nginx har två tydliga roller

Nginx-konfigurationen i referensimplementationen har två huvuduppgifter.

Den första är att servera den byggda frontendapplikationen:

```nginx
root /usr/share/nginx/html;
index index.html;

location / {
    try_files $uri $uri/ /index.html;
}
```

Det innebär att React/PWA-applikationen vid runtime består av statiska filer som Nginx levererar. `try_files`-regeln ger dessutom SPA:n möjlighet att hantera klientrutter genom att falla tillbaka till `index.html` när en fysisk fil inte finns.

Den andra rollen är att vidarebefordra API-trafik:

```nginx
location /api/ {
    proxy_pass http://backend:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

`proxy_pass` skickar requesten vidare till Quarkus-servicen `backend` på dess interna port 8080. Eftersom `proxy_pass` här anges utan en ersättande URI behålls API-sökvägen i den proxade requesten. Ett anrop till `/api/tasks` når därför Quarkus som `/api/tasks`, vilket matchar `TaskResource` i referenskoden. Nginx dokumenterar `proxy_pass` och dess URI-beteende i den officiella proxy-moduldokumentationen. (NGINX, *Module ngx_http_proxy_module*)

Det är viktigt att inte låta reverse proxyn växa till ett andra applikationslager. I TaskBoard fattar Nginx inga domänbeslut. Den validerar inte uppgiftens status, känner inte till `TaskPriority` och skriver inte till databasen. Dess uppgift är HTTP-routing, statisk leverans och vissa transportrelaterade headers.

## Quarkus äger API- och applikationsgränsen

När requesten har passerat Nginx kommer den till Quarkus. Där finns den första komponent som förstår TaskBoards domän.

`TaskResource` exponerar resurser under:

```java
@Path("/api/tasks")
```

och mappar HTTP-operationer till applikationsoperationer:

- `GET /api/tasks` listar uppgifter,
- `GET /api/tasks/{id}` hämtar en uppgift,
- `POST /api/tasks` skapar en uppgift,
- `PUT /api/tasks/{id}` uppdaterar en uppgift,
- `DELETE /api/tasks/{id}` tar bort en uppgift.

Det är här transportformatet JSON möter TaskBoards applikationsmodell. Requestdata valideras och skickas vidare till tjänstelagret. Backenden avgör vad en giltig uppgift är och hur den ska behandlas.

Det är också Quarkus som äger databasanslutningen. Compose tillför JDBC-adress och credentials som miljövariabler:

```yaml
QUARKUS_DATASOURCE_JDBC_URL: jdbc:postgresql://db:5432/${POSTGRES_DB:-taskboard}
QUARKUS_DATASOURCE_USERNAME: ${POSTGRES_USER:-taskboard}
QUARKUS_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD:-taskboard-change-me}
```

Namnet `db` är inte en extern DNS-post. Det är Compose-servicens namn på det interna nätverket. På så sätt behöver backenden inte känna till en dynamisk container-IP.

Quarkus kör i referensimplementationen på `0.0.0.0`, vilket gör HTTP-servern tillgänglig från andra containrar på nätverket. Quarkus dokumenterar att produktionsläget normalt binder HTTP-servern till `0.0.0.0`, vilket är lämpligt för containerdeployment. (Quarkus, *All configuration options*)

## PostgreSQL ligger bakom applikationsgränsen

Webbläsaren anropar aldrig PostgreSQL. Nginx anropar aldrig PostgreSQL som en del av den avsedda requestkedjan. Det är Quarkus som översätter applikationsoperationer till persistenceoperationer.

Det ger en viktig egenskap: databasschemat blir inte ett publikt kontrakt mot frontend. En kolumn kan exempelvis byta namn eller en indexstrategi kan förändras utan att webbläsarkoden måste känna till det, så länge API-kontraktet fortfarande gäller.

I Compose-filen publiceras ingen port från PostgreSQL:

```yaml
db:
  image: postgres:18.4-alpine
```

Det betyder att port 5432 inte mappas till värddatorn. Databasen är därmed inte en extern ingång till TaskBoard i den här modellen.

### Intern betyder inte automatiskt nätverksisolerad

Här behöver beskrivningen vara exakt.

TaskBoards Compose-fil deklarerar inga separata nätverk. Docker Compose skapar därför ett gemensamt standardnätverk och ansluter samtliga services till det. På det nätverket kan containrar hitta varandra via servicenamn. Docker dokumenterar uttryckligen detta beteende för Compose-standardnätverket. (Docker Docs, *Networking in Compose*)

Det innebär att `db` är **intern i förhållande till värddatorn och den avsedda externa trafikvägen**, men inte strikt segmenterad från `web`-containern. Eftersom `web`, `backend` och `db` delar samma Compose-nätverk skulle en process i `web` tekniskt kunna försöka ansluta till `db:5432`.

För TaskBoards lilla referensarkitektur accepterar vi den förenklingen. Om nätverkssegmentering är ett krav kan Compose i stället definiera exempelvis ett frontendnät och ett backendnät:

```text
web <---- frontend-net ----> backend <---- data-net ----> db
```

Då behöver `web` och `db` inte dela nätverk alls. Docker Compose stöder uttryckliga nätverk och kan även skapa nätverk med `internal: true` när det behövs. (Docker Docs, *Networking in Compose*)

Den viktiga lärdomen är att **ingen publicerad port** och **nätverksisolering** är två olika egenskaper. Referensimplementationen använder den första men inte den andra.

## Ett requestflöde genom arkitekturen

Vi kan nu följa en förenklad skapandeoperation genom systemet utan att ännu gå ned på den detaljnivå som kapitel 10 använder.

Anta att användaren skapar uppgiften:

```json
{
  "title": "Förbered release",
  "description": "Kontrollera migrationsfiler och release notes",
  "status": "OPEN",
  "priority": "NORMAL",
  "dueDate": "2026-08-31"
}
```

### 1. Frontenden skickar en relativ request

Frontendens API-lager skickar en `POST` till:

```text
/api/tasks
```

Ur webbläsarens perspektiv går requesten till samma origin som levererade webbappen.

### 2. Nginx väljer API-vägen

Requesten matchar `location /api/`. Nginx serverar alltså inte en statisk fil utan proxar requesten till:

```text
http://backend:8080/api/tasks
```

Service discovery i Compose gör att namnet `backend` kan lösas till den aktuella backendcontainern. Docker rekommenderar att services refereras med namn snarare än dynamiska container-IP-adresser. (Docker Docs, *Networking in Compose*)

### 3. Quarkus tolkar requesten

`TaskResource.create()` tar emot JSON-representationen som en validerad requestmodell. Applikationslagret skapar uppgiften och persistence-lagret skriver den till PostgreSQL inom backendens ansvar.

### 4. PostgreSQL lagrar den beständiga representationen

Databasen ser tabeller, kolumner, datatyper, constraints och index. Den behöver inte känna till React, HTTP eller Nginx.

### 5. Svaret går tillbaka samma väg

Quarkus returnerar en HTTP-response med den skapade uppgiften. Nginx förmedlar svaret tillbaka till webbläsaren, och frontend uppdaterar användargränssnittet.

Det finns alltså ingen genväg från frontend till databas. Varje gräns har ett tydligt kontrakt:

```text
Frontend --HTTP/JSON--> Backend --JPA/JDBC--> PostgreSQL
```

Nginx ligger framför HTTP-gränsen och gör backendens interna adress transparent för klienten.

## Service discovery i stället för fasta adresser

Containrar är till sin natur utbytbara. En ny backendcontainer kan få en annan intern IP-adress än den gamla. Om Nginx-konfigurationen byggde på en sådan IP skulle arkitekturen bli onödigt skör.

Compose löser detta genom servicenamn. På standardnätverket kan `web` adressera `backend`, och `backend` kan adressera `db`. Docker beskriver detta som inbyggd service discovery på Compose-nätverket. (Docker Docs, *Networking in Compose*)

Referensimplementationen använder därför:

```text
backend:8080
```

i Nginx-konfigurationen och:

```text
db:5432
```

i JDBC-URL:en.

Det här är en liten men viktig skillnad mellan **logisk adress** och **fysisk instans**. Arkitekturen refererar till tjänster, inte till en enskild containers nuvarande nätverksidentitet.

## Startordning är också en arkitekturfråga

Även med rätt nätverk kan tjänsten misslyckas om komponenterna startar i fel ordning eller betraktas som färdiga för tidigt.

TaskBoard definierar därför healthchecks för databasen och backenden. Backenden har:

```yaml
depends_on:
  db:
    condition: service_healthy
```

och `web` väntar på att backenden är frisk:

```yaml
depends_on:
  backend:
    condition: service_healthy
```

Docker Compose dokumenterar att `service_healthy` gör att den beroende servicen väntar på att dependency-servicens healthcheck har blivit godkänd innan den startas. (Docker Docs, *Services*)

För TaskBoard betyder det i praktiken:

```text
PostgreSQL healthy
      |
      v
Quarkus startar
  - ansluter till databasen
  - Flyway migrerar schemat
  - applikationen blir ready
      |
      v
Nginx/web startar
```

Det här gör inte hela systemet självläkande och det ersätter inte en riktig driftplattform. Men det kodifierar en viktig del av tjänstens startkontrakt.

Healthchecken för backend använder Quarkus readiness-endpoint under `/q/health/ready`. Referensimplementationen inkluderar SmallRye Health, och den kompletta Compose-kedjan har verifierats i GitHub Actions.

## Reverse proxy och forwarded headers

Nginx skickar vidare flera headers:

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

Detta bevarar information om den ursprungliga requesten när trafiken går genom proxyn. Nginx dokumenterar `proxy_set_header` som en del av proxy-modulen. (NGINX, *Module ngx_http_proxy_module*)

Men det finns en viktig skillnad mellan att **skicka headers** och att **låta backenden lita på dem**. En backend bakom en proxy behöver en medveten policy för vilka forwarded headers som ska användas och vilka proxies som är betrodda. Quarkus har särskild konfiguration för proxy address forwarding och host-validering. (Quarkus, *HTTP Reference*)

TaskBoards nuvarande referensimplementation använder headers som en rimlig grund, men kapitlet gör inte antagandet att en publik internetdeployment därmed är fullständigt proxyhärdad. Det hör till säkerhets- och driftkonfigurationen i senare kapitel.

## Arkitekturgränserna gör systemet utbytbart

En styrka i den här uppdelningen är att teknik kan bytas inom en gräns utan att hela systembilden behöver ändras.

Några exempel:

- React skulle kunna ersättas av ett annat frontendramverk så länge klienten fortfarande levererar statiska assets och använder samma API-kontrakt.
- Nginx skulle kunna ersättas av en annan reverse proxy eller plattformsrouter om den fortfarande kan servera eller dirigera frontend och `/api` på motsvarande sätt.
- Quarkusimplementationen kan förändras internt utan att frontend påverkas så länge REST-kontraktet består.
- PostgreSQLversion, index eller intern schemastruktur kan utvecklas genom migrationer utan att frontend blir databasklient.

Det betyder inte att komponenterna är oberoende. API-kontrakt, databasmodell och deployment måste fortfarande utvecklas samordnat. Men beroendena går genom färre, tydligare gränser.

## Vad arkitekturen medvetet inte gör

Referensarkitekturen är liten och ska inte läsas som en generell blueprint för alla produktionssystem.

Den har exempelvis:

- en enda Nginx-instans,
- en enda Quarkus-instans,
- en enda PostgreSQL-instans,
- ett gemensamt Compose-standardnätverk,
- ingen inbyggd autentisering eller auktorisering,
- ingen TLS-terminering i själva Compose-exemplet,
- ingen extern secrets manager,
- ingen lastbalansering mellan backendinstanser,
- ingen hög tillgänglighet för databasen.

Det är medvetna avgränsningar. Bokens mål är att visa en komplett och begriplig kedja från kod till körbar tjänst. När kraven växer ska arkitekturen kunna utvecklas från tydliga gränser, inte börja med en plattformsnivå vars komplexitet döljer grundprinciperna.

## Fördjupning: varför inte publicera PostgreSQL-porten?

Under utveckling är det bekvämt att publicera en databasport för att ansluta med `psql`, ett IDE-verktyg eller en databasklient. I den produktionslika Compose-modellen gör TaskBoard inte det.

Skälet är inte att en opublicerad port gör databasen säker i alla avseenden. Skälet är att den externa exponeringsytan ska motsvara tjänstens avsedda gränssnitt.

TaskBoards externa klienter behöver HTTP. De behöver inte PostgreSQL-protokollet. Genom att inte publicera 5432:

- minskar antalet externa endpoints som måste skyddas och dokumenteras,
- blir det tydligt att API:t är den stödda vägen till applikationsdata,
- kan databasens interna adress och containerlivscykel förändras utan att skapa ett externt kontrakt,
- undviker vi att felsökningstillgång av misstag blir en permanent driftväg.

Om operatörer behöver administrativ databasåtkomst bör den lösas som en uttrycklig driftfunktion, exempelvis via kontrollerad nätverksåtkomst, ett separat administrativt flöde eller tillfälliga verktyg. Den behöver inte byggas in som en publik port i applikationens normala leveransmodell.

## Centrala fakta

- TaskBoards publika runtime-ingång är Nginx; endast `web` publicerar en värdport i Compose-modellen.
- Frontend och API använder samma origin genom att API-anrop går till relativa `/api`-adresser via Nginx.
- Nginx serverar statiska frontendfiler och proxar `/api` till Quarkus, men innehåller ingen domänlogik.
- Quarkus äger REST-kontraktet, applikationslogiken och åtkomsten till persistence.
- PostgreSQL nås av backend via servicenamnet `db` och publiceras inte till värddatorn.
- Compose-standardnätverket ger service discovery med servicenamn; container-IP-adresser ska inte vara del av applikationskonfigurationen.
- Att en databasport inte är publicerad är inte samma sak som full nätverkssegmentering. I den nuvarande implementationen delar `web`, `backend` och `db` standardnätverk.
- Healthchecks och `depends_on` med `service_healthy` kodifierar den valda startordningen mellan databas, backend och web.
- Forwarded headers från Nginx är transportinformation; hur Quarkus ska lita på dem är en separat säkerhetskonfiguration.
- Arkitekturens viktigaste egenskap är tydliga gränser: webbläsare → HTTP-ingång → applikations-API → persistence.

## Nästa steg

Arkitekturbilden är nu etablerad. Vi vet vilka runtime-delarna är, hur requesttrafiken rör sig och vilka gränser som ska hållas tydliga.

Nästa kapitel flyttar fokus från runtime till källkod och utvecklingsarbete. Där går vi igenom hur `code/taskboard/` är organiserat, hur frontend och backend kan utvecklas separat utan att kontrakten divergerar och hur Vite, Quarkus och PostgreSQL kopplas ihop i den lokala utvecklingsmiljön.
