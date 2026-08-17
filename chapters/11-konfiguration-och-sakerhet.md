# 11. Konfiguration och säkerhet

En körbar tjänst är inte färdig bara för att den kan starta. Den måste också kunna flyttas mellan miljöer utan att byggas om för varje installation, och den måste ha en tydlig säkerhetsgräns mellan sådant som får exponeras och sådant som ska förbli internt.

TaskBoard är fortfarande en liten referensimplementation, men just därför går det att se principerna tydligt. Samma frontend- och backend-images ska kunna användas med olika databasnamn, användare, lösenord och publicerad port. Samtidigt ska webbläsaren bara behöva känna till en publik ingång.

Den produktionslika formen kan sammanfattas så här:

```text
Webbläsare
    |
    | HTTP/HTTPS
    v
Nginx
    |
    | /api
    v
Quarkus
    |
    | JDBC
    v
PostgreSQL
```

I den aktuella Compose-filen är det bara `web` som har en publicerad port. `backend` och `db` kan nås av andra containrar på Compose-nätverket, men de publiceras inte direkt på värdens nätverksinterface.

Det är en bra start. Men det är inte samma sak som att tjänsten är komplett säkerhetshärdad för Internet. I det här kapitlet skiljer vi därför konsekvent mellan **vad TaskBoard faktiskt gör i dag** och **vad en skarp installation bör kompletteras med**.

## Samma artifact, olika miljöer

Ett vanligt misstag är att baka in miljöspecifika värden i koden eller imagen:

```text
localhost
prod-db-17.internal.example
lösenord
publik port
extern URL
```

Då blir bygget bundet till en viss miljö. En bättre modell är att låta artefakten vara stabil och tillföra miljöskillnader som runtime-konfiguration.

TaskBoards Compose-fil använder till exempel interpolation:

```yaml
environment:
  POSTGRES_DB: ${POSTGRES_DB:-taskboard}
  POSTGRES_USER: ${POSTGRES_USER:-taskboard}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-taskboard-change-me}
```

och för webbporten:

```yaml
ports:
  - "${TASKBOARD_PORT:-8080}:80"
```

Syntaxen `${VAR:-default}` betyder att Compose använder värdet från den omgivande miljön eller en env-fil om det finns och annars faller tillbaka till standardvärdet. Docker beskriver detta som Compose interpolation. (Docker Docs, *Set, use, and manage variables in a Compose file with interpolation*.)

Referensprojektet innehåller därför `.env.example`:

```text
POSTGRES_DB=taskboard
POSTGRES_USER=taskboard
POSTGRES_PASSWORD=taskboard-change-me
TASKBOARD_PORT=8080
```

Den filen är avsiktligt en **mall**, inte en hemlig produktionskonfiguration. Den verkliga `.env`-filen ignoreras av Git:

```gitignore
.env
```

Detta gör det möjligt att köra:

```bash
cp .env.example .env
```

och därefter ändra lokala värden utan att modifiera Compose-filen.

Principen är viktigare än mekanismen:

```text
image + kod          stabilt och versionsstyrt
runtime-konfiguration varierar mellan miljöer
hemligheter          tillförs utanför källkoden
```

## Quarkus konfigureras också utifrån

Backendens `application.properties` innehåller sådant som är stabilt för applikationen:

```properties
quarkus.datasource.db-kind=postgresql
quarkus.hibernate-orm.schema-management.strategy=validate
quarkus.flyway.migrate-at-start=true
quarkus.flyway.locations=db/migration
quarkus.http.host=0.0.0.0
```

Själva anslutningsuppgifterna kommer däremot från Compose:

```yaml
QUARKUS_DATASOURCE_JDBC_URL: jdbc:postgresql://db:5432/${POSTGRES_DB:-taskboard}
QUARKUS_DATASOURCE_USERNAME: ${POSTGRES_USER:-taskboard}
QUARKUS_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD:-taskboard-change-me}
```

Quarkus kan läsa konfiguration från flera källor och miljövariabler kan överstyra egenskaper vid runtime. (Quarkus, *Configuration Reference Guide*.)

Det gör att backend-imagen inte behöver känna till den slutliga databasens lösenord när den byggs.

Det är den egenskap vi vill åt:

```text
samma backend-image
       |
       +-- utveckling -> lokal/dev-databas
       +-- test       -> testdatabas
       +-- drift      -> driftens PostgreSQL
```

## Ett exempellösenord är inte en hemlighet

TaskBoards standardvärde:

```text
taskboard-change-me
```

är pedagogiskt praktiskt eftersom projektet kan startas utan extra förberedelser. Men ett sådant standardvärde får inte misstolkas som en säker driftkonfiguration.

En skarp installation ska ersätta det med ett unikt värde.

Dessutom är miljövariabler inte alltid den bästa transportmekanismen för känsliga värden. Docker rekommenderar att secrets används för känslig information som lösenord och API-nycklar, eftersom miljövariabler kan exponeras oavsiktligt, exempelvis vid felsökning eller processinspektion. Compose secrets gör i stället värdet tillgängligt som en fil under `/run/secrets/...` för de tjänster som uttryckligen beviljats åtkomst. (Docker Docs, *Manage secrets securely in Docker Compose*.)

Referensimplementationen använder ännu **inte** Compose secrets. Det är ett medvetet avgränsat nuläge, inte ett säkerhetsideal.

En mer härdad leverans skulle exempelvis kunna låta PostgreSQL och Quarkus läsa ett lösenord från en secret-fil, eller använda den secrets manager som målplattformen erbjuder.

Poängen är inte att alla installationer måste använda samma verktyg. Poängen är att hemligheten ska kunna bytas utan att:

- ändra applikationskoden,
- bygga om imagen,
- checka in lösenordet i Git,
- eller sprida det till komponenter som inte behöver det.

## En publik ingång minskar exponeringsytan

I TaskBoards Compose-fil har endast `web` en `ports`-mappning:

```yaml
web:
  ports:
    - "${TASKBOARD_PORT:-8080}:80"
```

`backend` har ingen publicerad port och `db` har ingen publicerad port.

Det betyder inte att de är nätverksisolerade från varandra. Alla tre ligger i Compose-projektets standardnätverk och kan kommunicera där. Men de behöver inte vara direkt adresserbara från nätet utanför Docker-värden. Docker skiljer mellan containerns interna nätverksanslutning och explicit publicerade portar. (Docker Docs, *Networking overview*.)

Det yttre kontraktet blir därmed enklare:

```text
klient -> Nginx
```

inte:

```text
klient -> frontendport
klient -> backendport
klient -> databasport
```

Att inte publicera onödiga portar är en grundläggande minskning av attackytan. Det är däremot inte en ersättning för brandväggar, nätverkspolicyer eller autentisering där sådant krävs.

## Same-origin förenklar browsergränsen

Frontendens API-klient använder relativa URL:er:

```ts
/api/tasks
```

I den produktionslika formen serverar Nginx både frontendresurserna och reverse proxyn för `/api`.

För webbläsaren kan därför båda anropen ligga på samma origin:

```text
https://taskboard.example/          frontend
https://taskboard.example/api/...  API
```

En origin bestäms av scheme, host och port. Browserns same-origin policy begränsar hur script från en origin får läsa resurser från en annan. (MDN Web Docs, *Same-origin policy*.)

TaskBoard behöver därför ingen CORS-konfiguration för sitt normala produktionsflöde: frontend och API exponeras bakom samma publika origin.

Det är en arkitektonisk fördel. Vi slipper exempelvis göra en generell regel som:

```text
Access-Control-Allow-Origin: *
```

bara för att få en separat frontend-host att prata med en separat API-host.

Om arkitekturen senare ändras så att frontend och API faktiskt ligger på olika origins måste CORS konfigureras medvetet. CORS är en HTTP-baserad mekanism som låter servern ange vilka andra origins browsern får exponera svar för. Tillåtna origins bör hållas så begränsade som möjligt. (MDN Web Docs, *Cross-Origin Resource Sharing (CORS) configuration*.)

Men CORS är inte autentisering. Det är framför allt en browserpolicy för cross-origin-åtkomst. En angripare behöver inte använda din frontend för att skicka HTTP-requests till ett publikt API.

## Reverse proxy är inte autentisering

Nginx-konfigurationen för API:t är:

```nginx
location /api/ {
    proxy_pass http://backend:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Det ger en bra routinggräns. Men inget i detta svarar på frågorna:

```text
Vem är användaren?
Får användaren läsa uppgiften?
Får användaren ändra den?
Är användaren administratör?
```

TaskBoard har i sin nuvarande referensform **ingen autentisering och ingen auktorisering**. Alla som kan nå den publicerade tjänsten kan använda CRUD-API:t.

Det är acceptabelt för en lokal pedagogisk referensimplementation. Det vore ett allvarligt säkerhetsantagande om samma tjänst exponerades publikt med känsliga data.

I en verklig tjänst kan autentisering och auktorisering införas i exempelvis Quarkus med OIDC/JWT eller via en betrodd identitetsproxy, beroende på miljö och krav. Exakt modell ligger utanför bokens TaskBoard-scope. Det viktiga här är ansvarsfördelningen:

```text
reverse proxy       dirigerar trafik
TLS                 skyddar transporten
autentisering       fastställer identitet
auktorisering       avgör behörighet
applikationslogik   upprätthåller domänregler
```

Ingen av dessa ersätter automatiskt de andra.

## Forwarded headers måste vara betrodda på rätt sätt

Nginx skickar bland annat:

```text
X-Forwarded-For
X-Forwarded-Proto
```

Dessa headers kan användas av backend för att förstå den ursprungliga klientadressen eller om den externa requesten kom via HTTPS även om proxy-till-backend-trafiken går över HTTP.

Men det finns ett säkerhetsproblem: en klient kan själv skicka headers med samma namn.

Quarkus aktiverar därför inte proxy address forwarding blint. Den aktuella TaskBoard-konfigurationen har **inte**:

```properties
quarkus.http.proxy.proxy-address-forwarding=true
```

Det innebär att Nginx skickar proxyinformationen, men att TaskBoard ännu inte har konfigurerat Quarkus att använda den som betrodd requestmetadata.

Om en framtida driftmiljö behöver korrekta externa scheme-, host- eller klientadressvärden måste proxy forwarding aktiveras med en genomtänkt trustmodell. Quarkus dokumenterar uttryckligen risken för spoofing och stöd för trusted proxies; inkommande forwarded headers från icke betrodda proxies kan då ignoreras. (Quarkus, *HTTP Reference*.)

Principen är:

```text
skicka forwarded headers      ≠      lita på alla forwarded headers
```

En publik deployment bör också se till att edge-proxyn skriver över eller tar bort klientstyrda forwarding-headers innan de når applikationen.

## TLS ska ligga vid den verkliga kanten

TaskBoards Nginx-container lyssnar i dag på vanlig HTTP port 80:

```nginx
listen 80;
```

Det är rimligt i den lokala Compose-miljön och i ett internt nät där en annan komponent terminerar TLS.

För en publik webbtjänst ska användartrafiken normalt gå över HTTPS. TLS kan termineras exempelvis i:

- en extern reverse proxy,
- en ingress-controller,
- en lastbalanserare,
- en managed edge-tjänst,
- eller Nginx själv om den äger den publika kanten.

Vi ska alltså inte läsa `listen 80` som rekommendationen "kör HTTP på Internet". Vi ska läsa den som att **TaskBoard-imagen inte äger certifikat- och TLS-livscykeln i referensmiljön**.

Det är ofta en bra separation. Certifikat kan då förnyas och hanteras av den plattform som redan ansvarar för publik trafik.

Om TLS termineras framför TaskBoards Nginx blir proxyinformation om ursprungligt scheme viktig om applikationen senare behöver skapa absoluta HTTPS-URL:er, tillämpa secure-cookie-policyer eller göra andra scheme-beroende beslut. Då återkommer frågan om trusted forwarded headers.

## Säkerhetsheaders och browserhärdning

Den nuvarande `nginx.conf` sätter få säkerhetsrelaterade response headers. Det finns exempelvis ingen explicit Content Security Policy i referenskoden.

Det är ytterligare ett område där vi ska skilja mellan **minimal fungerande referens** och **härdad publik drift**.

En riktig deployment kan behöva bedöma exempelvis:

- Content Security Policy,
- skydd mot oönskad framing,
- `Referrer-Policy`,
- HSTS när HTTPS-arkitekturen är fastställd,
- cookie-attribut om autentisering införs,
- rate limiting eller skydd vid den publika kanten.

Det vore däremot fel att bara klistra in en generell samling headers i boken och kalla tjänsten säker. En CSP måste exempelvis stämma med vilka script, styles och externa resurser den verkliga applikationen använder. HSTS förutsätter att domänen verkligen ska nås via HTTPS. Säkerhetskonfiguration måste höra ihop med deploymentmodellen.

## Konfiguration kan också vara en säkerhetskontroll

Det är lätt att se konfiguration som enbart bekvämlighet. I praktiken kan bra runtime-konfiguration också minska risk.

Ta databasen som exempel.

I referensprojektet kan följande värden bytas utan kodändring:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

Det gör det möjligt för en driftmiljö att använda unika credentials per installation i stället för ett gemensamt lösenord inbyggt i imagen.

På samma sätt kan publicerad port ändras:

```text
TASKBOARD_PORT
```

utan att frontend behöver kompileras om.

Detta är en viktig egenskap hos en portabel leverans: miljön får välja sina externa parametrar, medan artefakten förblir densamma.

Men alla värden ska inte nödvändigtvis vara fritt konfigurerbara. Ju fler säkerhetskritiska flaggor som kan ändras utan kontroll, desto fler kombinationer måste vi förstå och testa. Konfiguration är därför också en del av systemets kontrakt.

## Vad TaskBoard har – och vad den saknar

Efter de föregående resonemangen kan referensimplementationens aktuella säkerhetsläge beskrivas utan överdrifter.

**Den har:**

- en enda publicerad webbingång,
- ingen publicerad PostgreSQL-port,
- ingen publicerad Quarkus-port,
- relativa same-origin-API-URL:er i frontend,
- miljöbaserad databas- och portkonfiguration,
- `.env` exkluderad från Git,
- Nginx som tydlig reverse proxy-gräns,
- validering i backend,
- versionsstyrt databasschema,
- healthchecks som kan stoppa felaktig startup.

**Den har ännu inte:**

- autentisering,
- auktorisering,
- Compose secrets eller extern secrets manager,
- TLS-terminering i referensstacken,
- explicit Quarkus trusted-proxy-konfiguration,
- en genomarbetad uppsättning security headers,
- rate limiting,
- separat nätverkssegmentering mellan `web`, `backend` och `db`.

Det senare är inte en lista över fel som måste lösas innan vi kan lära oss av tjänsten. Det är en lista över avgränsningar som vi måste känna till innan vi kallar den produktionsredo för ett visst hotlandskap.

## En rimlig härdningsordning

Om TaskBoard skulle tas från pedagogisk referens till en verklig tjänst är en rimlig ordning ungefär:

1. bestäm var TLS termineras,
2. ersätt standardcredentials och inför säker secret-hantering,
3. inför autentisering och auktorisering utifrån verksamhetskrav,
4. definiera trusted-proxy- och forwarded-header-policy,
5. begränsa nätverk och publicerade portar utifrån faktisk driftplattform,
6. komplettera response/security headers utifrån verklig frontend och autentiseringsmodell,
7. inför loggning, övervakning, backup och incidentrutiner,
8. hotmodellera lösningen och testa de viktigaste säkerhetsgränserna.

Ordningen är inte universell, men den visar en viktig princip: säkerhet är inte en enstaka Nginx-rad eller ett ramverksberoende. Den uppstår genom flera samverkande gränser.

## Konfigurationens roll i den körbara tjänsten

Vi kan nu komplettera bilden från tidigare kapitel:

```text
Källkod
   |
   v
Byggda images
   |
   +------------------+
   | runtime config   |
   | credentials      |
   | port / endpoints |
   +------------------+
   |
   v
Körande tjänst i en bestämd miljö
```

En reproducerbar image och en reproducerbar miljö är alltså två olika saker.

Imagen ska vara stabil. Miljön tillför sina konfigurationsvärden. Säkerhetsgränserna avgör vilka komponenter som får nås och vilka identiteter som får göra vad.

TaskBoard visar redan flera bra byggstenar: externa databasvärden, same-origin genom reverse proxy och begränsad portpublicering. Samtidigt visar den lika pedagogiskt vad som **inte** följer automatiskt av containerisering: hemligheter blir inte säkra bara för att de är miljövariabler, reverse proxy ger ingen identitet, same-origin ersätter inte auktorisering och forwarded headers får inte behandlas som sann information utan en trustmodell.

Det är just den skillnaden som gör konfiguration och säkerhet till en arkitekturfråga snarare än en sista checkruta före drift.

I nästa kapitel går vi vidare till **testning av den kompletta tjänsten**. Där blir frågan inte bara om varje komponent fungerar var för sig, utan vilka fel som endast kan upptäckas när frontend, proxy, backend, migrationer och en riktig PostgreSQL-instans får arbeta tillsammans.
