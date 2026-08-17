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
| Persistence-/integrationstest | Quarkus + riktig PostgreSQL | JPA, SQL, migrationer, datatyper |
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

Detta är redan mer än ett vanligt byggjobb. Det verifierar att de artifacts som boken beskriver faktiskt går att sätta ihop till en körande tjänst.

Samtidigt är det viktigt att inte tillskriva workflowen tester som inte finns. Frontendens `package.json` har i dagsläget inget `test`-script och inga testberoenden. Backendens `pom.xml` innehåller `quarkus-junit5` och Rest Assured som testberoenden, men projektet har ännu inga incheckade klasser under `src/test`.

Kommandot:

```bash
mvn -B --no-transfer-progress verify
```

är därför värdefullt som bygg- och livscykelkontroll, men det ska inte beskrivas som en omfattande backend-testsuite. Om det inte finns några testklasser finns det heller inga applikationsbeteenden för Surefire att verifiera.

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

TaskBoards frontend är liten. `App.tsx` laddar uppgifter, visar formulär och lista och anropar `taskApi` för create, update och delete.

Om frontenden byggs ut är en rimlig teststack **Vitest** tillsammans med **React Testing Library**. Vitest är Vite-nära och kan använda samma konfigurationsmodell, medan React Testing Library är utformat för att testa UI via DOM och användarnära frågor i stället för React-komponenternas interna implementation. (Vitest, *Getting Started*; Testing Library, *React Testing Library*.)

En representativ komponenttest skulle inte behöva veta att `App` använder `useState`. Det kan i stället verifiera ett scenario:

```text
Givet att API:t returnerar en uppgift
När App renderas
Då visas uppgiftens titel och status
```

Ett annat:

```text
Givet ett tomt titel-fält
När användaren försöker skapa en uppgift
Då skickas ingen create-request
```

Och ett tredje:

```text
Givet att API:t svarar med fel
När listan laddas
Då visas ett element med role="alert"
```

I ett sådant test ska transporten normalt simuleras eller ersättas. Målet är att verifiera frontenden, inte att samtidigt starta PostgreSQL.

Det är också därför ett komponenttest inte ersätter full-stack-testet. Ett simulerat API kan råka acceptera `MEDIUM` även om den verkliga backendens enum inte gör det.

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

Ett framtida TaskBoard-test bör exempelvis verifiera:

```text
POST /api/tasks
  giltig body          -> 201
  tom title            -> 400
  title > 160 tecken   -> 400
  priority NORMAL      -> accepterad
  priority MEDIUM      -> 400
```

Just raden om `MEDIUM` är värd att ha som regressionstest. Det tidigare smoke-testfelet lärde oss att frontend/testdata och backendens enum kan glida isär.

Ett API-test kan dessutom kontrollera sådant som frontendens TypeScript-typer inte kan garantera vid runtime:

- JSON-deserialisering,
- Bean Validation,
- enumkonvertering,
- HTTP-statuskoder,
- `Location`-headern efter `POST`,
- 404 för okända id:n.

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

För TaskBoard är detta en naturlig framtida modell för backendens integrationstester:

```text
JUnit / @QuarkusTest
        |
        v
Quarkus
        |
        v
PostgreSQL Dev Service
```

Då kan testet verifiera både REST-lagret och den verkliga persistencekedjan utan att testkoden själv behöver skapa och konfigurera containern manuellt.

Det är här databasmigrationerna också ska få verklig testtäckning. Om Flyway körs vid uppstart ska integrationstestet starta från en tom testdatabas och låta migrationerna skapa schemat. Ett grönt test ger då information om både:

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

TaskBoard behöver inte lägga till alla testnivåer samtidigt. En pragmatisk ordning är:

```text
1. behåll nuvarande statiska validator och build-steg
2. lägg till backend/API-tester med @QuarkusTest
3. låt persistence/API-tester använda PostgreSQL via Dev Services
4. lägg till Vitest + React Testing Library när UI-logiken växer
5. utöka full-stack-smoke-testet till update och delete
6. håll full-stack-sviten liten och stabil
```

Varje steg täcker en lucka i den nuvarande portföljen.

Backend/API-testerna bör prioriteras eftersom mycket av TaskBoards kontrakt finns där och infrastrukturen redan har testberoenden. PostgreSQL Dev Services gör det möjligt att testa persistence på rätt databasprodukt. Frontendkomponenttester blir mer värdefulla när `App.tsx` delas upp och UI-beteendet blir rikare.

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

Det är teststrategin bakom TaskBoard. Snabba kontroller ska stoppa enkla fel tidigt. Riktiga integrationstester ska prova kontrakt och persistence där mocks annars skulle dölja risker. Och en liten full-stack-kontroll ska slutligen visa att React/PWA, Nginx, Quarkus och PostgreSQL faktiskt bildar en körbar tjänst.

Det är först då ett grönt bygge börjar betyda något för den som ska använda systemet.
