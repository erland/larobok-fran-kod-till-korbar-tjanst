# 12. Testning av den kompletta tjänsten

En tjänst kan vara korrekt på varje enskild nivå och ändå vara trasig som helhet. Frontenden kan kompilera. Backend kan byggas. SQL-migrationen kan vara syntaktiskt korrekt. Docker-images kan skapas. Ändå kan en verklig användare mötas av ett fel när webbläsaren skickar sin första request.

TaskBoard har redan gett oss ett konkret exempel. GitHub Actions lyckades bygga frontend och backend och starta hela Compose-stacken, men smoke-testets `POST /api/tasks` fick först svaret `400 Bad Request`. Felet låg inte i nätverket, databasen eller Nginx. Testet skickade prioriteten `MEDIUM`, medan API-kontraktet accepterade `LOW`, `NORMAL` eller `HIGH`.

Det är precis därför testning av en komplett tjänst inte kan reduceras till frågan:

> Har varje del en egen testsuite?

Den bättre frågan är:

> Vilka typer av fel vill vi upptäcka, och på vilken nivå är det billigast och mest tillförlitligt att upptäcka dem?

För TaskBoard leder det till en testportfölj i flera lager. Några kontroller ska vara mycket snabba och isolerade. Andra behöver starta Quarkus och en riktig PostgreSQL-instans. Minst ett test behöver gå genom samma publika ingång som den körbara tjänsten använder.

## Testnivåerna har olika jobb

Det är frestande att tala om en strikt testpyramid där det alltid ska finnas många unit tests, färre integrationstester och nästan inga end-to-end-tester. Grundidén om kostnad är användbar, men ett modernt system behöver oftare en **testportfölj** än en matematisk pyramid.

För TaskBoard kan nivåerna beskrivas så här:

| Nivå | Exempel | Hittar främst |
|---|---|---|
| Statisk verifiering | TypeScript-kompilering, Python-validator | strukturfel, typfel, fel versionsval |
| Enhetstest | normalisering, små rena funktioner | lokal logik |
| Komponenttest | React-komponent med simulerat API | UI-beteende och användarflöden |
| API-/backendtest | Quarkus + HTTP | routing, JSON, validering, statuskoder |
| persistens-/integrationstest | Quarkus + riktig PostgreSQL | JPA, SQL, migrationer, datatyper |
| Full-stack smoke test | Nginx + Quarkus + PostgreSQL | kopplingen mellan alla runtime-delar |

Ingen rad ersätter någon annan. Ett full-stack-test är till exempel bra på att visa att kedjan fungerar, men dåligt på att exakt lokalisera ett fel i en liten hjälpfunktion. Ett enhetstest kan lokalisera ett sådant fel perfekt men kan aldrig bevisa att Nginx proxar `/api` till rätt container.

## Vad TaskBoard faktiskt verifierar i dag

Den kanoniska CI-workflowen heter:

```text
.github/workflows/04-test-reference-implementation.yml
```

Den kör i följande ordning:

```text
1. validera referensstrukturen
2. bygg frontend
3. kompilera och kör Maven verify för backend
4. validera Docker Compose-konfigurationen
5. bygg Docker-images
6. starta hela Compose-stacken och vänta på healthchecks
7. kör smoke test genom den publika webbporten
8. visa status/loggar vid fel
9. stäng ned stacken och ta bort testvolymen
```

Detta är redan mer än ett vanligt byggjobb. Det verifierar att de artefakter som boken beskriver faktiskt går att sätta ihop till en körande tjänst.

Samtidigt är det viktigt att beskriva vad workflowen faktiskt exekverar. Frontenden har nu ett `test`-script som kör Vitest och en incheckad komponenttestsvit med React Testing Library. Backenddelen har en incheckad `TaskResourceTest` under `src/test` som använder `@QuarkusTest` och Rest Assured.

Kommandot:

```bash
mvn -B --no-transfer-progress verify
```

kör därför inte längre bara backendens bygglivscykel. Det startar också Quarkus-testmiljön och exekverar API-testet. Testprofilen låser PostgreSQL Dev Services till samma PostgreSQL-version som referensstacken, `postgres:18.4-alpine`, så att Flyway, Hibernate ORM, repository och HTTP-lager provas tillsammans mot riktig PostgreSQL när en container-runtime finns tillgänglig.

Testsuiten är fortfarande medvetet liten. Den ska beskrivas som ett representativt API-/integrationstestlager, inte som fullständig täckning av all backendlogik.

Det är en viktig generell regel:

> Ett grönt testkommando betyder bara det som faktiskt exekverades.

## Statisk verifiering är också testning

Först i workflowen körs:

```bash
python3 "$TASKBOARD_DIR/validate_reference.py"
```

Validatorn kontrollerar bland annat att centrala filer finns, att versionsvalen i `package.json` och `pom.xml` är de förväntade, att Compose använder rätt PostgreSQL-image och volymmount samt att Nginx-konfigurationen innehåller den förväntade `/api`-proxyn.

Detta är inte ett runtime-test. Det bevisar till exempel inte att Nginx verkligen kan nå Quarkus. Men det ger snabb feedback på sådant som annars skulle orsaka dyrare fel längre fram i workflowen.

Frontendens byggsteg ger en annan sorts statisk kontroll:

```bash
npm run build
```

I TaskBoard betyder det:

```text
tsc -b && vite build
```

TypeScript kan därmed hitta fel i de statiska typerna och Vite kan verifiera att produktionsbundlen går att skapa.

Det fel vi tidigare fick med TypeScript-inställningen `allowImportingTsExtensions` är ett exempel på något som ska fångas här — innan Docker eller någon databas behöver startas.

## Enhetstester ska vara små av en anledning

TaskBoard innehåller inte mycket ren domänlogik ännu. Mycket av beteendet ligger i ett tunt tjänstelager och är beroende av repository eller HTTP.

Ett exempel på lokalt beteende är normaliseringen i `TaskService`:

```java
private String normalize(String value) {
    return value == null || value.isBlank() ? null : value.trim();
}
```

Sådan kod kan testas utan databas om den bryts ut till en testbar funktion eller klass. Detsamma gäller regler som i framtiden kan avgöra om en statusövergång är tillåten.

Poängen är inte att varje metod måste ha ett eget test. Poängen är att **ren logik bör testas utan att starta hela världen**.

Ett bra enhetstest är:

- snabbt,
- deterministiskt,
- enkelt att förstå när det misslyckas,
- oberoende av nätverk och containrar.

Om en regel kan testas så är det onödigt dyrt att bara upptäcka felet i full-stack-testet fem steg senare.

## Frontend: testa beteende, inte implementation

TaskBoards frontend är liten. `App.tsx` laddar uppgifter, visar formulär och lista och anropar `taskApi` för create, update och delete. Referensimplementationen använder nu **Vitest 4.1.10**, **React Testing Library 16.3.2** och **jsdom 30.0.1** för komponenttesterna. Vitest körs med ett browserliknande jsdom-environment, medan Testing Library låter testet fråga efter samma typer av DOM-element som användaren möter i gränssnittet. (Vitest, *Test Environment*; Testing Library, *React Testing Library*.)

Den incheckade `App.test.tsx` verifierar fyra representativa beteenden:

```text
1. initial laddning visar uppgifter från API:t
2. formuläret kan skapa en uppgift och återställs efter lyckat svar
3. en statusändring skickar PUT och ersätter uppgiften med API-svaret
4. ett HTTP-fel visas via role="alert"
```

Testerna känner inte till att `App` råkar använda `useState`; de interagerar med titel-fält, knappar, comboboxar och synlig text. `user-event` används för användarinteraktionerna. Det följer Testing Library-principen att tester bör ligga nära hur gränssnittet faktiskt används.

HTTP-transporten ersätts i komponenttestet genom att den globala `fetch`-funktionen stubbas. Det gör att även den riktiga `api.ts`-koden provas — inklusive relativa `/api`-URL:er, HTTP-metoder, JSON-body och felhantering — utan att starta Quarkus eller PostgreSQL. Målet på den här nivån är att verifiera frontendens beteende, inte hela stacken.

Det är också därför komponenttestet inte ersätter full-stack-testet. En stub av `fetch` kan returnera data som den verkliga backendens kontrakt skulle avvisa. Full-stack-testet behövs fortfarande för att visa att frontendens antaganden och den deployade backendens kontrakt faktiskt passar ihop.

## API-test: starta Quarkus på riktigt

Backendens `pom.xml` innehåller redan de byggstenar som behövs för Quarkus-testning:

```xml
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-junit5</artifactId>
  <scope>test</scope>
</dependency>

<dependency>
  <groupId>io.rest-assured</groupId>
  <artifactId>rest-assured</artifactId>
  <scope>test</scope>
</dependency>
```

Quarkus stödjer HTTP-baserade tester där `@QuarkusTest` startar applikationen och Rest Assured kan anropa endpoints mot testservern. Quarkus använder som standard en separat testport, vilket gör att tester kan köras utan att kollidera med en vanlig utvecklingsinstans. (Quarkus, *Testing Your Application*.)

TaskBoards nuvarande `TaskResourceTest` verifierar bland annat:

```text
POST   giltig body            -> 201
GET    lista/filter           -> 200 och skapad uppgift
GET    känt id                -> 200
PUT    känt id                -> 200 och uppdaterad uppgift
DELETE känt id                -> 204
GET    borttaget/okänt id     -> 404
POST   tom title              -> 400
POST   priority MEDIUM        -> 400
```

Just raden om `MEDIUM` är ett medvetet regressionstest. Det tidigare smoke-testfelet lärde oss att testdata och backendens enum kan glida isär. Testet kontrollerar också `Location`-headern efter `POST`, normalisering av titel/beskrivning och att filtrerad listning hittar den skapade uppgiften.

API-testet täcker därmed sådant som frontendens TypeScript-typer inte kan garantera vid runtime:

- JSON-deserialisering,
- Bean Validation,
- enumkonvertering,
- HTTP-statuskoder,
- `Location`-headern efter `POST`,
- 404 för okända id:n,
- faktisk persistens genom JPA/Flyway/PostgreSQL.

## När en riktig PostgreSQL-instans behövs

Persistencekapitlen har visat att TaskBoard använder funktioner och beteenden som tillhör PostgreSQL och JPA tillsammans:

```text
UUID
TIMESTAMPTZ
Flyway
Hibernate schema validation
JPQL
@Version
```

Det är därför riskabelt att låta alla integrationstester använda en annan databasprodukt bara för att den är lättare att starta. Ett test mot en in-memory-databas kan vara snabbt, men det bevisar inte att PostgreSQLs verkliga typer, constraints och migrationer fungerar.

Quarkus Dev Services kan automatiskt starta en containeriserad PostgreSQL-databas i dev- och testläge när PostgreSQL-driverextensionen finns och ingen extern JDBC-URL konfigureras. Quarkus kopplar sedan applikationen till databasen automatiskt. (Quarkus, *Dev Services for Databases*.)

TaskBoard använder nu denna modell för backendens API-/integrationstester:

```text
JUnit / @QuarkusTest
        |
        v
Quarkus
        |
        v
PostgreSQL Dev Service
```

Testet kan därmed verifiera både REST-lagret och den verkliga persistenskedjan utan att testkoden själv behöver skapa och konfigurera containern manuellt.

Flyway körs när Quarkus-testmiljön startar och Hibernate validerar modellen mot det skapade schemat. Därmed får migrationen också verklig testtäckning. Ett grönt API-/integrationstest ger information om kedjan:

```text
migration -> Hibernate-validering -> repository -> API
```

## Testdata ska inte läcka mellan tester

Databastester skapar ett nytt problem: state.

Anta att ett test skapar:

```text
"Skriv kapitel 12"
```

och nästa test förväntar sig en tom task-lista. Om båda använder samma kvarvarande databas kan det andra testet misslyckas av fel anledning.

Testmiljön bör därför ha en tydlig isoleringsstrategi. Exempel är:

- ny databas/container per testsvit,
- transaktionsrollback där det är lämpligt,
- explicit datarensning mellan tester,
- unika testdata och inga beroenden på körordning.

Vilket alternativ som passar beror på kostnad och typ av test. Det viktiga är att ett test inte ska behöva känna till att ett annat test råkade köras före det.

CI-workflowens full-stack-test gör detta mycket enkelt genom att avsluta med:

```bash
docker compose down -v --remove-orphans
```

Flaggan `-v` tar bort den Compose-volume som användes av PostgreSQL. Nästa CI-körning börjar därför från en ny databas i stället för att återanvända gamla testdata.

## Healthcheck är inte samma sak som funktionsprov

Vid stackstart använder workflowen:

```bash
docker compose up -d --wait --wait-timeout 120
```

Databasen har en healthcheck med `pg_isready` och backend kontrollerar Quarkus readiness-endpoint:

```text
/q/health/ready
```

Webbcontainerns image kontrollerar:

```text
http://127.0.0.1/healthz
```

Detta ger viktig startup-synkronisering. Compose kan vänta tills de tjänster som behöver vara healthy faktiskt är det.

Men en healthcheck svarar på en begränsad fråga:

```text
Är den här processen/tjänsten redo enligt sin definierade kontroll?
```

Den svarar inte automatiskt på:

```text
Kan en användare skapa och läsa en uppgift genom hela systemet?
```

Därför behövs smoke-testet efter `docker compose up --wait`.

## Smoke-testet använder den publika vägen

Det viktigaste designvalet i TaskBoards befintliga smoke test är URL:en:

```text
http://localhost:18080
```

Testet går alltså via den port som Nginx publicerar. Det anropar inte Quarkus direkt på port 8080 och det ansluter inte själv till PostgreSQL.

Först verifieras webbcontainern:

```text
GET /healthz -> 200 och "ok"
GET /         -> 200 och HTML som innehåller "TaskBoard"
```

Sedan skickas en riktig create-request:

```json
{
  "title": "GitHub Actions smoke test",
  "description": "Created through Nginx, Quarkus and PostgreSQL",
  "status": "OPEN",
  "priority": "NORMAL",
  "dueDate": null
}
```

Svaret måste vara `201`. Testet tar id:t från svaret och läser sedan tillbaka uppgiften via:

```text
GET /api/tasks/{id}
```

och därefter via:

```text
GET /api/tasks
```

Denna lilla sekvens verifierar förvånansvärt mycket:

```text
Nginx routing
    +
JSON request
    +
Quarkus REST
    +
Bean/Jackson mapping
    +
service + transaction
    +
JPA/Hibernate
    +
Flyway-skapat schema
    +
PostgreSQL write/read
    +
JSON response
```

Det är därför smoke-testet hittade kontraktsfelet `MEDIUM`/`NORMAL` trots att frontend- och backendbyggena var gröna.

## Vad smoke-testet ännu inte provar

Ett bra smoke-test ska vara litet. Om det försöker verifiera varje detalj blir det långsamt, svårt att felsöka och dyrt att underhålla.

TaskBoards nuvarande test provar create och read/list. Det provar ännu inte hela CRUD-kontraktet.

En rimlig framtida utbyggnad är:

```text
POST   skapa
PUT    ändra status
GET    läs tillbaka ändringen
DELETE ta bort
GET    verifiera 404 eller frånvaro
```

Då följer testet samma livscykel som en vanlig TaskBoard-uppgift.

Samtidigt bör detaljer som `@NotBlank`, maxlängd och alla enumkombinationer hellre ligga i snabbare backend/API-tester. Full-stack-testet behöver framför allt visa att **den deployade sammansättningen fungerar**.

## Fel ska vara diagnostiserbara

Ett integrationsjobb är bara användbart om ett fel går att förstå.

Workflowen har därför diagnostik vid startfel:

```bash
docker compose ps -a
docker compose logs --no-color
```

och ett separat failure-steg som också visar containerstatus och loggar.

Detta blev viktigt när `web`-containern tidigare rapporterades som unhealthy. Nginx startade normalt och backend var healthy; felet låg i webbcontainerns healthcheck. När URL:en ändrades från `localhost` till explicit IPv4-loopback `127.0.0.1` försvann den osäkerheten.

En generell princip är:

> Ju fler komponenter ett test startar, desto viktigare är bra felinformation.

För ett mer avancerat system kan diagnostiken kompletteras med exempelvis health-state från `docker inspect`, HTTP-response bodies och artefakter från testverktyg. Men loggning ska hjälpa till att hitta felet — inte bara producera tusentals rader text.

## En rekommenderad utbyggnadsordning

TaskBoard behöver inte lägga till alla testnivåer samtidigt. De två viktigaste kompletteringarna utöver full-stack-smoke-testet är nu genomförda: backend/API-testet kör mot PostgreSQL via Dev Services och frontendens kritiska UI-flöden provas med Vitest + React Testing Library. En pragmatisk fortsatt ordning är:

```text
1. behåll statisk validator, frontendkomponenttester och backend/API-test
2. utöka full-stack-smoke-testet till update och delete om behovet motiverar det
3. komplettera backendtesten med fler kontrakts- och domänfall när funktionaliteten växer
4. komplettera frontendtesten när UI-beteendet blir rikare
5. håll full-stack-sviten liten och stabil
```

Varje framtida steg ska täcka en verklig kvarvarande risk, inte bara öka antalet tester. Frontend- och backendtesterna ger nu snabbare lokalisering av fel, medan smoke-testet behåller ansvaret för att verifiera den deployade helheten.

Det befintliga smoke-testet ska däremot behållas även när de snabbare testerna blir fler. Det är fortfarande den kontroll som svarar på frågan:

> Fungerar den tjänst vi faktiskt tänker leverera?

## Testmiljön ska likna produktion där det spelar roll

Det betyder inte att varje test ska köras i en full produktionsmiljö.

För en ren TypeScript-funktion spelar PostgreSQL-versionen ingen roll. För en React-komponent behöver Nginx inte startas. För valideringen av en REST-request behövs normalt inte hela frontenden.

Men när testets syfte är att verifiera databasmigrationer spelar databasprodukten roll. När syftet är att verifiera reverse proxy-konfiguration spelar Nginx roll. När syftet är att verifiera hela leveransen spelar Docker-images och Compose-filen roll.

En användbar tumregel är därför:

```text
Gör testet så litet som möjligt,
men inte mindre än felet du vill kunna hitta.
```

Det är teststrategin bakom TaskBoard. Snabba kontroller ska stoppa enkla fel tidigt. Riktiga integrationstester ska prova kontrakt och persistens där mocks annars skulle dölja risker. Och en liten full-stack-kontroll ska slutligen visa att React/PWA, Nginx, Quarkus och PostgreSQL faktiskt bildar en körbar tjänst.

Det är först då ett grönt bygge börjar betyda något för den som ska använda systemet.
