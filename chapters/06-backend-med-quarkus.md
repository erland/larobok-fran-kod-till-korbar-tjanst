# 6. Backend med Quarkus

I kapitel 5 såg vi frontendens kontrakt mot `/api/tasks`. Nu går vi över samma HTTP-gräns från andra hållet och tittar på den backend som faktiskt tar emot anropen.

TaskBoards backend är liten med flit. Den består av en REST-resurs, ett tjänstelager, ett repository, DTO:er, en JPA-entitet och två enumtyper. Det räcker för att visa de delar av Quarkus som en erfaren Java-utvecklare behöver förstå för att bli produktiv utan att boken förvandlas till en generell Quarkus-kurs.

Den centrala kedjan är:

```text
HTTP-request
    |
    v
TaskResource
    |
    v
TaskService
    |
    v
TaskRepository
    |
    v
EntityManager / PostgreSQL
```

I det här kapitlet stannar vi huvudsakligen i de två första leden. Persistenslagret och databasschemat får egna kapitel eftersom de har andra designfrågor än HTTP-API:t.

## Quarkus är ramen runt vanlig Java

TaskBoard använder Java 21 och Quarkus 3.33.3.1. I `pom.xml` är projektet deklarerat med Quarkus-specifik packaging:

```xml
<groupId>se.erland.taskboard</groupId>
<artifactId>taskboard-backend</artifactId>
<version>0.1.0</version>
<packaging>quarkus</packaging>
```

Quarkus Maven-pluginen knyter därmed Quarkus build-steg till Mavens vanliga livscykel. Det är viktigt i referensprojektet eftersom samma `mvn package` som fungerar lokalt också måste producera den katalogstruktur som backendens Dockerfile kopierar in i runtime-imagen. Quarkus dokumenterar `quarkus` som packaging för själva applikationsmodulen och använder den för att koppla in sina genererings- och build-steg i Maven-livscykeln. (Quarkus, *Quarkus Maven Plugin*.)

Det är ändå i huvudsak vanlig Java vi skriver. TaskBoard har inga Quarkus-specifika basklasser för REST-resurser eller tjänster. I stället kombineras standardiserade Jakarta-API:er med Quarkus extensions:

- Jakarta REST för HTTP-resurser,
- CDI för dependency injection,
- Jakarta Validation för indata,
- Jakarta Transactions för transaktionsgränser,
- Jakarta Persistence för databasanrop.

Quarkus tillhandahåller implementationen och den build-/runtime-integration som binder ihop dessa delar.

## Extensions är funktionella byggblock

De viktigaste Quarkus-beroendena i TaskBoard är:

```xml
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-rest-jackson</artifactId>
</dependency>
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-hibernate-orm</artifactId>
</dependency>
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-jdbc-postgresql</artifactId>
</dependency>
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-hibernate-validator</artifactId>
</dependency>
```

Därutöver finns Flyway och SmallRye Health, som vi återkommer till senare.

`quarkus-rest-jackson` ger TaskBoard Quarkus REST tillsammans med Jackson-baserad JSON-serialisering. Quarkus officiella guide använder samma extension för REST-tjänster som tar emot och returnerar JSON. (Quarkus, *Writing JSON REST Services*.)

Det är en användbar mental modell att se extensions som integrationspaket snarare än som vanliga hjälpbibliotek. Ett Quarkus-extension kan bidra med konfiguration, build-time processing och runtime-komponenter som arbetar tillsammans. Man väljer därför normalt extension efter vilken plattformsfunktion applikationen behöver, inte genom att själv montera varje underliggande implementation.

## REST-resursen uttrycker HTTP-kontraktet

TaskBoards publika API börjar i `TaskResource`:

```java
@Path("/api/tasks")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class TaskResource {
    @Inject
    TaskService service;

    // endpoints
}
```

Tre saker etableras direkt.

`@Path` sätter resursens bas-URL. `@Produces` säger att svar representeras som JSON. `@Consumes` anger att request bodies för operationer som har body förväntas vara JSON.

Quarkus REST bygger på Jakarta REST-programmeringsmodellen, så en Java-utvecklare som redan har arbetat med JAX-RS/Jakarta REST känner igen annotationerna. Quarkus REST är samtidigt Quarkus egen implementation, tätt integrerad med plattformens build-time-modell. (Quarkus, *Writing REST Services with Quarkus REST*.)

TaskBoard har fem operationer:

```text
GET    /api/tasks
GET    /api/tasks/{id}
POST   /api/tasks
PUT    /api/tasks/{id}
DELETE /api/tasks/{id}
```

Det räcker för det CRUD-liknande användningsfall som frontend behöver.

## Query-parametrar kan bindas direkt till domännära typer

Listoperationen tar två frivilliga filter:

```java
@GET
public List<TaskResponse> list(
        @QueryParam("status") TaskStatus status,
        @QueryParam("priority") TaskPriority priority) {
    return service.list(status, priority);
}
```

Resursen behöver inte själv läsa query-strängen eller konvertera normala enumvärden. HTTP-parametrarna binds till `TaskStatus` och `TaskPriority` innan tjänstelagret anropas.

Det är praktiskt, men det gör också kontraktet strikt. Frontendens prioritet `NORMAL` måste motsvara backendens enum. När CI-smoke-testet tidigare skickade det påhittade värdet `MEDIUM` svarade backend med HTTP 400. Det var inte ett infrastrukturfel utan ett kontraktsfel, och just därför är starka, begränsade värdemängder användbara.

Samma princip gäller id-parametern:

```java
@GET
@Path("/{id}")
public TaskResponse get(@PathParam("id") UUID id) {
    return service.get(id);
}
```

Resursmetoden arbetar med `UUID`, inte med en rå sträng som måste tolkas längre ned i systemet.

## DTO:er håller HTTP-modellen separat från entiteten

TaskBoard exponerar inte `TaskEntity` direkt. I stället finns två records i `TaskDtos`:

```java
public record SaveTaskRequest(
        @NotBlank @Size(max = 160) String title,
        @Size(max = 4000) String description,
        TaskStatus status,
        TaskPriority priority,
        LocalDate dueDate) {
}
```

och:

```java
public record TaskResponse(
        UUID id,
        String title,
        String description,
        TaskStatus status,
        TaskPriority priority,
        LocalDate dueDate,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt) {
}
```

Detta är samma arkitekturgräns som vi såg från frontend i föregående kapitel. Klienten skriver inte `id`, `createdAt` eller `updatedAt`; backend äger dem.

Separationen är viktig av fler skäl än JSON-format. Databasentiteten innehåller till exempel ett versionsfält för optimistisk låsning. Det är inte automatiskt en del av det externa API-kontraktet. Genom att mappa entiteten till `TaskResponse` kan persistens-modellen utvecklas utan att varje intern förändring blir en publik API-förändring.

I en större tjänst skulle create och update kunna få olika DTO:er. TaskBoard använder samma `SaveTaskRequest` för båda eftersom operationerna ännu har samma indataform. Det är ett medvetet förenklingsval, inte ett krav från Quarkus.

## Bean Validation stoppar ogiltiga requests vid gränsen

`SaveTaskRequest` har två centrala constraints:

```java
@NotBlank @Size(max = 160) String title,
@Size(max = 4000) String description
```

Resursmetoderna använder sedan `@Valid`:

```java
@POST
public Response create(@Valid SaveTaskRequest request) {
    var created = service.create(request);
    return Response.created(URI.create("/api/tasks/" + created.id()))
            .entity(created)
            .build();
}
```

`@Valid` gör att valideringen kaskaderar till request-objektets constraints. Quarkus dokumenterar samma mönster för REST endpoint validation och kan generera en valideringsrespons när indatan bryter mot constraints. (Quarkus, *Validation with Hibernate Validator*.)

Det betyder att tjänstelagret kan utgå från att en accepterad titel inte är blank och inte längre än 160 tecken. Vi duplicerar inte samma kontroll i React, REST-resurs, service och repository som om varje lager vore en egen värld.

Frontendens `maxLength={160}` är fortfarande bra UX, men backendvalideringen är den auktoritativa gränsen. En API-klient kan alltid kringgå webbläsarens formulär.

## HTTP-status är en del av kontraktet

List- och get-operationerna kan returnera sina DTO:er direkt. För create och delete behöver TaskBoard styra statuskod och headers tydligare.

Create använder:

```java
return Response.created(URI.create("/api/tasks/" + created.id()))
        .entity(created)
        .build();
```

Det ger HTTP 201 och en `Location` som pekar på den nya resursen. Response body innehåller samtidigt den skapade representationen.

Delete använder:

```java
return Response.noContent().build();
```

vilket ger HTTP 204 och ingen body.

Frontendens generiska request-funktion känner redan till detta och försöker inte JSON-parsa ett 204-svar.

När en uppgift inte finns kastar tjänstelagret `NotFoundException`:

```java
private TaskEntity required(UUID id) {
    return repository.find(id).orElseThrow(NotFoundException::new);
}
```

Jakarta REST/Quarkus översätter detta till ett 404-svar. Det gör att resursmetoderna kan hålla sig små utan att varje metod upprepar samma `if (entity == null)` och response-byggande.

För en större produktions-API-design kan man vilja standardisera felkroppar med egna exception mappers. TaskBoard har ännu inte ett sådant kontrakt. Det är bättre att vara tydlig med den begränsningen än att beskriva ett felramverk som referenskoden inte använder.

## CDI binder ihop resurs och tjänst

`TaskService` är en CDI-bean:

```java
@ApplicationScoped
public class TaskService {
    @Inject
    TaskRepository repository;
}
```

och resursen får i sin tur tjänsten injicerad:

```java
@Inject
TaskService service;
```

Quarkus DI-implementation heter ArC och bygger på CDI Lite med valda utökningar. `@ApplicationScoped` är ett normalt CDI-scope och är också Quarkus rekommenderade standardval när man inte har ett särskilt skäl att välja ett annat scope. (Quarkus, *Introduction to Contexts and Dependency Injection*; *Contexts and Dependency Injection*.)

TaskBoard använder fältinjektion eftersom den håller exemplet kort. För större kodbaser är konstruktorinjektion ofta attraktiv för att göra beroenden tydliga och förenkla rena unit-tester. Det är dock en kodstilsfråga; den arkitektoniska poängen är att `TaskResource` inte själv skapar `TaskService`, och `TaskService` skapar inte sitt repository.

Containern äger beroendegrafen och livscykeln.

## Tjänstelagret samlar applikationsreglerna

TaskBoard hade kunnat lägga allt direkt i `TaskResource`. För en mycket liten demo fungerar det. Referensprojektet väljer ändå ett separat `TaskService` eftersom det finns regler som inte är HTTP-specifika.

Create-metoden är ett bra exempel:

```java
@Transactional
public TaskResponse create(SaveTaskRequest request) {
    var now = OffsetDateTime.now(ZoneOffset.UTC);
    var entity = new TaskEntity();
    entity.title = request.title().trim();
    entity.description = normalize(request.description());
    entity.status = request.status() == null ? TaskStatus.OPEN : request.status();
    entity.priority = request.priority() == null ? TaskPriority.NORMAL : request.priority();
    entity.dueDate = request.dueDate();
    entity.createdAt = now;
    entity.updatedAt = now;
    repository.persist(entity);
    return TaskResponse.from(entity);
}
```

Här finns flera applikationsbeslut:

- titel trimmas,
- tom beskrivning normaliseras till `null`,
- saknad status blir `OPEN`,
- saknad prioritet blir `NORMAL`,
- tidsstämplar sätts i UTC,
- persistens sker som en sammanhängande operation.

Inget av detta handlar om hur HTTP-parametrar läses. Därför hör reglerna bättre hemma i service-lagret.

Det är också här `@Transactional` ligger. Vi går djupare in i transaktionsgränsen i kapitel 7, men redan nu är det värt att se att muterande operationer `create`, `update` och `delete` är transaktionella medan läsoperationerna inte annoteras på samma sätt. Quarkus Hibernate ORM-guiden visar `@Transactional` som mekanismen för att göra en applikationsmetod till transaktionsgräns. (Quarkus, *Using Hibernate ORM and Jakarta Persistence*.)

## Update visar skillnaden mellan validering och affärssemantik

Update återanvänder samma requesttyp:

```java
@Transactional
public TaskResponse update(UUID id, SaveTaskRequest request) {
    var entity = required(id);
    entity.title = request.title().trim();
    entity.description = normalize(request.description());
    entity.status = request.status() == null ? entity.status : request.status();
    entity.priority = request.priority() == null ? entity.priority : request.priority();
    entity.dueDate = request.dueDate();
    entity.updatedAt = OffsetDateTime.now(ZoneOffset.UTC);
    return TaskResponse.from(entity);
}
```

Bean Validation avgör om requesten är strukturellt tillåten. Tjänstelagret avgör däremot vad utelämnade värden betyder.

För `status` och `priority` betyder `null`: behåll befintligt värde. För `dueDate` betyder `null`: sätt deadline till null. Dessa två tolkningar råkar alltså skilja sig trots att fälten alla kan vara null i Java.

Det är en subtil API-egenskap. Om applikationen växer kan det bli motiverat att skilja create/update eller införa en särskild PATCH-modell för att uttrycka "utelämnat" och "sätt till null" entydigt. TaskBoard behöver inte den komplexiteten ännu, men kapitlet ska inte dölja att semantiken finns.

## Konfiguration är runtime-data, inte Java-konstanter

TaskBoards `application.properties` är kort:

```properties
quarkus.datasource.db-kind=postgresql
quarkus.hibernate-orm.schema-management.strategy=validate
quarkus.flyway.migrate-at-start=true
quarkus.flyway.locations=db/migration
quarkus.http.host=0.0.0.0
```

Databasens URL, användarnamn och lösenord finns inte hårdkodade där för Compose-körningen. De sätts som environment variables:

```text
QUARKUS_DATASOURCE_JDBC_URL
QUARKUS_DATASOURCE_USERNAME
QUARKUS_DATASOURCE_PASSWORD
```

Quarkus konfigurationsmodell läser från flera källor med definierad prioritet; environment variables ligger högre än klasspathens `application.properties`. Quarkus beskriver också hur egenskapsnamn konverteras till versala environment-variable-namn med understreck. (Quarkus, *Configuration Reference Guide*.)

Det är därför samma backend-artefakt kan köras lokalt och i Compose utan att byggas om för varje databasadress.

Vi går djupare in i miljökonfiguration och secrets i kapitel 11. Här räcker principen: applikationskoden ska inte behöva känna till att databasen i Compose heter `db` eller att en annan installation använder ett helt annat hostnamn.

## `0.0.0.0` behövs i containern

TaskBoard sätter:

```properties
quarkus.http.host=0.0.0.0
```

Det gör backendens HTTP-server nåbar på containerns nätverksinterface i stället för enbart loopback. Det är vad Nginx-containern behöver när den ansluter till `backend:8080` över Compose-nätverket.

Samtidigt publiceras inte backendporten till värddatorn i Compose. Att Quarkus lyssnar på alla interface inne i containern betyder alltså inte att backend automatiskt exponeras externt. Exponeringen bestäms också av containernätverk och portpublicering, som vi såg i kapitel 2.

## Dev mode är ett utvecklingsverktyg, inte runtime-modellen

Vid lokal backendutveckling kan TaskBoard startas med:

```bash
mvn quarkus:dev
```

Quarkus dev mode ger live coding: ändringar i Java- och resursfiler kan tas upp utan att utvecklaren manuellt bygger om och startar om den paketerade applikationen. Quarkus har dessutom Dev UI och stöd för continuous testing. (Quarkus, *Creating Your First Application*; *Continuous Testing*.)

Det är en stor produktivitetsfördel, men dev mode ska inte blandas ihop med hur tjänsten körs efter leverans. Quarkus dokumenterar uttryckligen arkitektoniska skillnader mellan dev mode och den paketerade produktionsapplikationen och varnar för att använda dev mode i produktion. (Quarkus, *How dev mode differs from a production application*.)

TaskBoards produktionslika väg är i stället:

```text
mvn package
    |
    v
target/quarkus-app/
    |
    v
Docker runtime image
    |
    v
java -jar quarkus-run.jar
```

Det var just denna skillnad som blev viktig när referensimplementationens Docker-build först saknade korrekt Quarkus-produktionspaketering. Felet gjorde en nyttig sak synlig: ett Maven-kommando som ser lyckat ut är inte tillräckligt om det inte producerar den körningslayout som Dockerfilen förutsätter.

## Byggtid och runtime är båda delar av Quarkus-modellen

Quarkus flyttar mycket ramverksarbete till build time. För en applikationsutvecklare märks det bland annat genom att extensions och konfiguration inte alltid beter sig som ett traditionellt bibliotek som bara läses dynamiskt när JVM-processen redan är igång.

Quarkus dokumenterar att vissa konfigurationsvärden är fixed at build time medan andra kan överskridas vid runtime. (Quarkus, *Configuration Reference Guide*.)

Det betyder att "allt ska kunna styras med miljövariabler" är för grovt som tumregel. Egenskaper som kan bestämmas vid start, exempelvis databasens inloggningsuppgifter, passar väl där, men byggtidsegenskaper kräver ett annat resonemang. När vi senare diskuterar reproducerbara images behöver vi därför veta vilka beslut som hör till artefaktbygget och vilka som ska lämnas till installationen.

TaskBoard håller sig i detta skede till en enkel modell där de viktigaste miljöspecifika värdena — databasanslutningen — är runtime-konfiguration.

## Vad Quarkus inte behöver lösa åt oss

Det är lätt att tillskriva ett ramverk mer arkitekturansvar än det faktiskt har.

Quarkus väljer inte åt oss:

- var HTTP-gränsen mot frontend ska ligga,
- om DTO och entitet ska vara samma klass,
- hur create och update ska skilja sig semantiskt,
- vilken felmodell API:t ska ha,
- var transaktionsgränserna är mest begripliga,
- hur databasschemat ska versionshanteras,
- hur tjänsten ska containeriseras och överlämnas.

Det är våra designbeslut.

Quarkus ger däremot en väl integrerad plattform för att implementera dem: REST, CDI, validering, transaktioner, persistens, konfiguration, health och build tooling kan fungera som en sammanhängande helhet.

Det är den viktigaste lärdomen för en erfaren Java-utvecklare. Produktivitet i Quarkus handlar mindre om att lära sig ett helt nytt programmeringsspråk och mer om att förstå vilka standard-API:er Quarkus använder, vilka extensions som aktiverar funktionerna och vilka delar som sker vid build time respektive runtime.

## TaskBoards backendgräns i sammanfattning

Vi kan nu beskriva backendens första halva utan att blanda in persistens-detaljerna:

```text
POST /api/tasks
      |
      v
JSON -> SaveTaskRequest
      |
      v
Bean Validation
      |
      v
TaskResource
      |
      v
TaskService
  - normalisering
  - defaultvärden
  - tidsstämplar
  - not-found-semantik
  - transaktionsgräns
      |
      v
TaskRepository
```

Resursen äger HTTP-kontraktet. DTO:erna äger transportformen. Bean Validation stoppar strukturellt ogiltig indata. Tjänstelagret äger applikationsreglerna. CDI kopplar ihop delarna. Konfigurationen hålls utanför Java-koden där den är miljöberoende.

Nästa steg är att följa kedjan vidare in i persistens-lagret. Där blir frågan inte längre främst hur Quarkus tar emot en request, utan hur vi använder JPA och transaktioner utan att låta ORM-modellen bli hela applikationsarkitekturen.
