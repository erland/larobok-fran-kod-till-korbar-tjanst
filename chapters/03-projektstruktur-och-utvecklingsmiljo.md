# 3. Projektstruktur och utvecklingsmiljö

En arkitektur blir inte särskilt användbar om den bara går att rita. Den behöver också få en fysisk form i källkodsträdet: kataloger som går att hitta i, byggkommandon som går att köra och en utvecklingsmiljö där förändringar kan provas utan att hela produktionslika stacken måste byggas om efter varje tangenttryckning.

För TaskBoard använder vi ett gemensamt repository för bokprojektet och referensimplementationen. Själva tjänsten ligger under `code/taskboard/`, med frontend, backend och Compose-konfiguration samlade på en plats. Det är inte den enda möjliga strukturen, men den gör ett viktigt samband synligt: React-applikationen, Quarkus-applikationen och PostgreSQL-konfigurationen är tre tekniska delar av **samma levererbara tjänst**.

Det här kapitlet handlar därför mindre om hur React- eller Java-kod skrivs och mer om hur arbetsytan organiseras. Målet är att en utvecklare som klonar projektet snabbt ska kunna svara på fyra frågor:

1. Var ligger koden för respektive del?
2. Hur startar jag frontend och backend för snabb lokal utveckling?
3. Hur får jag en databas utan att bygga en egen lokal installationsrutin?
4. Hur kör jag den kompletta tjänsten på samma sätt som CI verifierar den?

När de frågorna har tydliga svar minskar avståndet mellan arkitektur, utveckling och leverans.

## Referensprojektets fysiska struktur

Den del av repositoryt som utgör TaskBoard ser förenklat ut så här:

```text
code/taskboard/
├── .env.example
├── .gitignore
├── README.md
├── RELEASE.md
├── STACK-VERSIONS.md
├── create_release_bundle.py
├── docker-compose.yml
├── docker-compose.release.yml
├── validate_reference.py
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   ├── package-lock.json
│   ├── public/
│   │   └── icon.svg
│   ├── src/
│   │   ├── App.test.tsx
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── main.tsx
│   │   ├── styles.css
│   │   └── test/setup.ts
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   └── vitest.config.ts
└── backend/
    ├── Dockerfile
    ├── pom.xml
    └── src/
        ├── main/
        │   ├── java/se/erland/taskboard/task/
        │   │   ├── TaskDtos.java
        │   │   ├── TaskEntity.java
        │   │   ├── TaskPriority.java
        │   │   ├── TaskRepository.java
        │   │   ├── TaskResource.java
        │   │   ├── TaskService.java
        │   │   └── TaskStatus.java
        │   └── resources/
        │       ├── application.properties
        │       └── db/migration/
        │           └── V1__create_task.sql
        └── test/java/se/erland/taskboard/task/
            └── TaskResourceTest.java
```

Strukturen uttrycker samma ansvarsfördelning som arkitekturen i föregående kapitel. `frontend/` innehåller webbläsarkoden, komponenttesterna och dess produktionsserver, `backend/` innehåller Quarkus-applikationen, API-/integrationstestet och databasmigrationerna, medan `docker-compose.yml` beskriver hur de körbara delarna sätts samman med PostgreSQL. De separata releasefilerna beskriver hur redan verifierade images identifieras och lämnas över utan en ny lokal build.

Det är värdefullt att skilja på **komponentens interna byggstruktur** och **tjänstens sammansättningsstruktur**. Frontendens `package.json` behöver inte känna till PostgreSQL. Backendens `pom.xml` behöver inte veta vilken port Nginx publicerar mot värden. Compose-filen däremot måste känna till hur komponenterna kopplas ihop när de körs tillsammans.

## Ett repository, flera byggsystem

TaskBoard är ett litet mono-repo i betydelsen att flera tekniska delprojekt ligger i samma versionshanterade helhet. Det gör inte automatiskt projektet till ett Maven-multiprojekt eller ett npm-workspace. Frontend och backend behåller sina egna byggsystem:

```text
frontend/  -> npm + TypeScript + Vite
backend/   -> Maven + Quarkus
```

Det gemensamma lagret ovanför dem är i första hand Docker Compose och GitHub Actions.

Den här modellen passar referenstjänsten av tre skäl.

För det första kan en förändring av API-kontraktet göras i samma commit som motsvarande frontendändring. För det andra kan CI verifiera hela kedjan från en och samma revision. För det tredje blir bokens kodexempel enklare att relatera till en bestämd systemversion.

Ett alternativ hade varit separata repositoryn för frontend och backend. Det kan vara motiverat när komponenterna har olika ägare, releasecykler eller åtkomstregler. Kostnaden är att en systemversion då måste uttryckas genom en kombination av flera repositoryrevisioner och att end-to-end-testet behöver välja vilka versioner som ska sättas samman.

Här väljer vi alltså inte mono-repo för att det alltid är bäst, utan för att tjänsten är liten, samägd och levereras som en sammanhängande enhet.

## Frontendens arbetsyta

Frontendens viktigaste ingångar är `package.json`, `vite.config.ts` och `src/`.

`package.json` definierar bland annat tre skript:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  }
}
```

Under aktiv utveckling är `npm run dev` den snabba vägen. Vite startar då sin utvecklingsserver och kan leverera uppdateringar utan att vi behöver bygga en Nginx-image efter varje förändring.

Produktionsbygget är en annan sak. `npm run build` kör först TypeScript-kompilering och därefter Vites build. Resultatet blir statiska frontendartefakter som senare kopieras in i Nginx-imagen. Utvecklingsservern är alltså **inte** vår produktionsserver.

Den distinktionen är central. Vite ger en effektiv utvecklingsloop. Nginx representerar den körmiljö vi faktiskt vill paketera. Att båda kan leverera samma React-applikation betyder inte att de har samma roll.

## Vite-proxyn håller frontendkoden miljöneutral

När hela tjänsten körs via Compose skickar webbläsaren API-anrop till samma origin och Nginx proxar `/api` vidare till backenden. Under lokal utveckling har vi ingen Nginx i requestvägen om vi kör Vite direkt.

Vi skulle kunna ändra frontendkoden till att anropa `http://localhost:8080/api`, men då skulle utvecklingsmiljön börja läcka in i applikationskoden. TaskBoard använder i stället Vites dev-proxy:

```ts
server: {
  proxy: {
    '/api': 'http://localhost:8080'
  }
}
```

Vite dokumenterar `server.proxy` som regler där requests vars sökväg börjar med en angiven nyckel skickas vidare till ett target. (Vite, *Server Options*)

Frontendkoden kan därför använda samma relativa API-adress i båda fallen:

```text
/api/tasks
```

Skillnaden ligger i infrastrukturen runt koden:

```text
Lokal utveckling:
Browser -> Vite :dev-port -> proxy -> Quarkus :8080

Produktionslik körning:
Browser -> Nginx :8080 -> proxy -> Quarkus :8080
```

Det är ett bra exempel på varför utvecklingsmiljö och produktionsmiljö inte behöver vara identiska för att applikationskontraktet ska vara det.

## Backendens arbetsyta följer Maven-konventioner

Backenden använder Maven. Källkoden ligger under:

```text
backend/src/main/java/
```

och resurser under:

```text
backend/src/main/resources/
```

Det följer Mavens standardiserade kataloglayout. Maven rekommenderar `src/main/java` för applikationskällkod, `src/main/resources` för resurser och `target` för byggresultat. (Apache Maven, *Introduction to the Standard Directory Layout*)

I TaskBoard innebär det att Java-paketet kan vara fokuserat på domänen:

```text
se/erland/taskboard/task/
```

medan konfiguration och Flyway-migrationer ligger bland resurserna:

```text
src/main/resources/application.properties
src/main/resources/db/migration/V1__create_task.sql
```

Den strukturen är avsiktligt konventionell. För en erfaren Java-utvecklare ska det inte krävas en projektspecifik karta för att hitta en resursfil eller förstå var Maven lägger byggresultatet.

`pom.xml` fungerar samtidigt som backendens byggkontrakt. Där finns Java-version, Quarkus-plattform och extensions. Compose behöver inte känna till dessa detaljer. Den behöver bara kunna bygga backendens Dockerfile och starta den resulterande imagen.

## Quarkus dev mode som utvecklingsloop

För backendutveckling kan TaskBoard köras med:

```bash
cd code/taskboard/backend
mvn quarkus:dev
```

Quarkus dev mode är utvecklingsvägen, inte den paketerade produktionskörningen. Det ger en snabbare loop när Java-kod och resurser ändras och är den miljö där Quarkus utvecklingsfunktioner kan aktiveras.

TaskBoards `application.properties` innehåller ingen explicit JDBC-URL för utvecklingsprofilen:

```properties
quarkus.datasource.db-kind=postgresql
quarkus.hibernate-orm.schema-management.strategy=validate
quarkus.flyway.migrate-at-start=true
quarkus.flyway.locations=db/migration
quarkus.http.host=0.0.0.0
```

Eftersom PostgreSQL JDBC-extensionen finns och anslutningsuppgifter inte är konfigurerade kan Quarkus Dev Services tillhandahålla en PostgreSQL-instans automatiskt i dev mode, förutsatt att en fungerande container-runtime finns. Quarkus dokumenterar att database Dev Services aktiveras i dev/test när relevant datasource-extension finns och ingen anslutnings-URL är satt. (Quarkus, *Dev Services for Databases*)

Det ger en lokal utvecklingskedja med få manuella steg:

```text
mvn quarkus:dev
        |
        +--> Quarkus
        |
        +--> Dev Services -> PostgreSQL-container
```

Utvecklaren behöver alltså inte först skapa en lokal PostgreSQL-databas, användare och schema för att prova en backendändring.

Det betyder däremot inte att databasen saknar struktur. När Quarkus startar kör Flyway migrationerna, och Hibernate ORM är konfigurerat för att validera modellen mot det migrerade schemat. Vi använder en bekväm databaslivscykel i utveckling men behåller samma princip för schemaägarskap.

## Två rimliga lokala arbetsflöden

Referensprojektet stöder i praktiken två olika sätt att arbeta lokalt.

### Snabb utveckling av frontend och backend

Backenden körs i en terminal:

```bash
cd code/taskboard/backend
mvn quarkus:dev
```

Frontenden körs i en annan:

```bash
cd code/taskboard/frontend
npm ci
npm run dev
```

Quarkus kan då använda Dev Services för PostgreSQL och Vite proxar `/api` till Quarkus på port 8080.

Det här flödet optimerar feedbacktiden. Det är lämpligt när vi ändrar React-komponenter, REST-resurser eller applikationslogik och vill prova resultatet omedelbart.

### Produktionslik kontroll av den kompletta tjänsten

Från TaskBoard-katalogen:

```bash
cp .env.example .env
docker compose up --build
```

Då bygger och startar vi samma typer av images som används i den verifierade Compose-kedjan:

```text
Nginx + byggd frontend
Quarkus fast-jar
PostgreSQL 18
```

Det här flödet är långsammare men svarar på andra frågor. Fungerar Dockerfilerna? Går migrationerna mot den containeriserade databasen? Är healthchecks korrekta? Når Nginx backenden via Compose-nätverket?

En effektiv utvecklingsprocess behöver båda perspektiven. Snabb feedback ersätter inte systemverifiering, och systemverifiering är onödigt dyr som enda feedbackloop.

## Miljökonfiguration utan att checka in den lokala filen

TaskBoard innehåller `.env.example`:

```env
POSTGRES_DB=taskboard
POSTGRES_USER=taskboard
POSTGRES_PASSWORD=taskboard-change-me
TASKBOARD_PORT=8080
```

Det är en mall som visar vilka värden Compose kan läsa. Den faktiska `.env`-filen ignoreras av Git:

```gitignore
.env
```

Det ger två separata egenskaper:

- repositoryt dokumenterar vilka lokala variabler som finns,
- den lokala filen behöver inte versionshanteras.

I referensprojektet är standardlösenordet uttryckligen ett utvecklingsvärde. Det ska inte läsas som en modell för hemlighetshantering i produktion. Secrets, TLS och miljöhantering behandlas närmare i kapitel 11.

Compose-filen använder dessutom defaultvärden, till exempel:

```yaml
POSTGRES_DB: ${POSTGRES_DB:-taskboard}
```

Det gör att referensstacken går att förstå även utan en dold mängd lokal konfiguration. `.env` ger möjlighet att ändra värden; den är inte en förutsättning för att läsa arkitekturen.

## Genererade filer ska inte bli projektstruktur

När frontend och backend byggs skapas stora mängder material som inte är källkod:

```text
frontend/node_modules/
frontend/dist/
backend/target/
```

TaskBoards `.gitignore` utesluter dessa kataloger.

Det är mer än städning. Ett repository ska i första hand beskriva **hur resultatet produceras**, inte bära med varje lokalt producerat resultat. `node_modules` återskapas från npm-konfigurationen, `dist` från frontendbygget och `target` från Mavenbygget.

Samma princip gör Dockerbyggen begripliga: Dockerfile tar källkod och byggbeskrivning som input och producerar en image. Den ska inte behöva förlita sig på att utvecklaren råkade ha rätt `dist/` eller `target/` liggande sedan tidigare.

## npm-lockfilen som del av utvecklingsmiljön

Referensimplementationen har nu både `package.json` och en npm-genererad, incheckad `package-lock.json`. CI och Docker-build använder därför `npm ci`, och samma kommando är ett bra förstahandsval även när en utvecklare vill återskapa det låsta dependency-trädet lokalt.

För de centrala frontendpaketen är flera versionsnummer explicit låsta i `package.json`, medan vissa typer fortfarande anges med versionsintervall. Lockfilen fryser den faktiska resolutionen av både direkta och transitiva beroenden. Om `package.json` och `package-lock.json` inte stämmer överens ska `npm ci` avbryta i stället för att tyst skriva om lockfilen.

Detta gör frontendens dependency-installation betydligt mer reproducerbar, men det gör inte hela leveransen bitreproducerbar. Image-taggar, byggmiljö, Mavenartefakter och CI-beroenden är separata delar av supply chain och behandlas vidare i kapitel 16.

## CI är en tredje miljö, inte bara en robot som kör lokala kommandon

GitHub Actions-workflowen för TaskBoard gör mer än respektive utvecklare normalt gör efter varje kodändring. Den:

1. validerar referensstrukturen,
2. bygger frontend,
3. kör Maven `verify` för backend,
4. validerar Compose-konfigurationen,
5. bygger Docker-images,
6. startar hela stacken,
7. smoke-testar requestvägen genom Nginx, Quarkus och PostgreSQL.

Det ger oss tre tydliga miljöperspektiv:

```text
Utveckling       -> snabb feedback
Produktionslikt  -> korrekt paketering och sammansättning
CI               -> reproducerbar verifiering från ren checkout
```

CI är särskilt viktig eftersom den saknar utvecklarens historik. Den har inte en gammal `node_modules`, en tidigare Maven-build eller en manuellt skapad databas att falla tillbaka på. När samma revision fungerar där får vi en starkare signal om att repositoryt faktiskt innehåller det som behövs.

Den här verifieringskedjan har i praktiken avslöjat problem i TypeScript-konfiguration, Quarkus-paketering, PostgreSQL 18-volymen, Nginx-healthchecken och smoke-testdata. När hela kedjan passerar har vi därför mer än kod som ser rimlig ut: vi har en verifierad start- och anropsväg.

## Projektstruktur som gränssnitt för utvecklaren

En väl vald katalogstruktur är ett slags användargränssnitt. Den hjälper utvecklaren att avgöra var en förändring hör hemma.

Vill vi ändra en React-vy går vi till:

```text
frontend/src/
```

Vill vi ändra API- eller domänlogik går vi till:

```text
backend/src/main/java/
```

Vill vi ändra databasschemat skapar vi en migration under:

```text
backend/src/main/resources/db/migration/
```

Vill vi ändra hur den kompletta tjänsten sätts samman granskar vi:

```text
docker-compose.yml
```

Och vill vi ändra hur frontend eller backend paketeras i en image finns respektive `Dockerfile` nära komponenten som byggs.

När den fysiska strukturen följer systemets ansvar minskar behovet av muntliga regler. Repositoryt blir mer självinstruerande.

## Vad vi tar med oss vidare

Vi har nu två kartor över samma tjänst.

Den logiska kartan från kapitel 2 säger:

```text
Browser -> Nginx -> Quarkus -> PostgreSQL
```

Den fysiska kartan i repositoryt säger:

```text
frontend/ + backend/ + docker-compose.yml
```

Utvecklingsmiljön lägger sedan till en tredje dimension: komponenterna kan köras med verktyg som är optimerade för snabb utveckling utan att vi ändrar deras externa kontrakt. Vite proxar samma `/api` som Nginx gör i den produktionslika miljön, och Quarkus Dev Services kan ge backenden PostgreSQL utan manuell lokal databasinstallation.

Det är en medveten balans. Vi försöker inte göra utvecklingsmiljön identisk med produktion. Vi försöker göra den **snabb där skillnaderna är ofarliga och lik där skillnaderna faktiskt påverkar beteendet**.

Med projektstrukturen på plats kan vi nu gå djupare i frontendens första särskilda egenskap. I nästa kapitel lämnar vi katalogerna och studerar vad det innebär att TaskBoard inte bara är en React-applikation, utan en PWA med manifest, service worker, caching och en egen uppdateringslivscykel.
