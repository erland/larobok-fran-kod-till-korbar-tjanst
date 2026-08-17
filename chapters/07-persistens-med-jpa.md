# 7. Persistens med JPA

I kapitel 6 följde vi ett HTTP-anrop genom `TaskResource` och `TaskService`. Nu fortsätter vi ett lager ned och tittar på hur TaskBoard gör Java-objekt persistenta utan att låta ORM-modellen bli hela applikationsarkitekturen.

Referensimplementationen använder Jakarta Persistence via Hibernate ORM i Quarkus. Den relevanta kedjan är liten:

```text
TaskService
    |
    v
TaskRepository
    |
    v
EntityManager
    |
    v
TaskEntity
    |
    v
PostgreSQL
```

Det är medvetet mindre abstraktion än i många enterprise-projekt. TaskBoard har ett repository, en entitet och en injicerad `EntityManager`. Det räcker för att visa de viktiga JPA-mekanismerna: mapping, persistence context, queries, dirty checking, transaktioner och optimistisk låsning.

Kapitlet förutsätter att du redan känner till grunderna i JPA. Fokus ligger därför inte på att lära ut varje annotation, utan på hur tekniken används i den körbara tjänsten och vilka arkitekturgränser den skapar.

## Hibernate ORM implementerar Jakarta Persistence

Backendens `pom.xml` innehåller Quarkus-extensionen:

```xml
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-hibernate-orm</artifactId>
</dependency>
```

Jakarta Persistence definierar API:t och programmeringsmodellen. Hibernate ORM är implementationen som Quarkus integrerar med applikationens datasource, CDI och transaktionshantering.

TaskBoard har ingen `persistence.xml`. Quarkus skapar den normala persistence-uniten från applikationens konfiguration och datasource när Hibernate ORM-extensionen finns med. Quarkus dokumenterar detta som standardvägen och visar också injektion av `EntityManager` direkt i en CDI-bean. (Quarkus, *Using Hibernate ORM and Jakarta Persistence*.)

Det ger en viktig separation:

```text
applikationskod        Jakarta Persistence API
                         |
                         v
                    Hibernate ORM
                         |
                         v
                    PostgreSQL JDBC
```

Applikationskoden behöver alltså inte konfigureras mot Hibernate-specifika sessioner för de operationer TaskBoard behöver. Den arbetar med standardiserade `jakarta.persistence`-typer.

## En separat entitet håller persistence-modellen intern

TaskBoards databasrepresentation är `TaskEntity`:

```java
@Entity
@Table(name = "task_item")
public class TaskEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    public UUID id;

    @Column(nullable = false, length = 160)
    public String title;

    @Column(columnDefinition = "TEXT")
    public String description;

    // ...
}
```

Det är inte samma klass som skickas över HTTP. I kapitel 6 såg vi i stället `SaveTaskRequest` och `TaskResponse`.

Skillnaden är avsiktlig. `TaskEntity` beskriver vad persistence-lagret behöver veta, medan DTO:erna beskriver vad API:t lovar klienten. Entiteten innehåller exempelvis fältet `version`, som behövs för optimistisk låsning men som inte ingår i TaskBoards publika JSON-representation.

En vanlig genväg i små CRUD-tjänster är att serialisera JPA-entiteten direkt. Det minskar antalet klasser, men binder samtidigt ihop tre förändringstakter:

- databasschemat,
- ORM-mappningen,
- HTTP-kontraktet.

TaskBoard accepterar några extra rader mappingkod för att hålla dessa gränser separata.

## Annotationerna är ett kontrakt mot persistence-lagret

Entiteten mappar flera typer av kolumner:

```java
@Enumerated(EnumType.STRING)
@Column(nullable = false, length = 32)
public TaskStatus status;

@Enumerated(EnumType.STRING)
@Column(nullable = false, length = 32)
public TaskPriority priority;

@Column(name = "due_date")
public LocalDate dueDate;

@Column(name = "created_at", nullable = false, updatable = false)
public OffsetDateTime createdAt;

@Column(name = "updated_at", nullable = false)
public OffsetDateTime updatedAt;
```

Det finns några medvetna val här.

Enumvärden lagras som strängar med `EnumType.STRING`. Det gör databasinnehållet begripligt och undviker att den persistenta betydelsen beror på enumkonstanternas numeriska ordning. Det kostar några fler byte än ordinaler, men för värden som `OPEN`, `DONE`, `LOW` och `HIGH` är det en rimlig byteskostnad för ett stabilare kontrakt.

`LocalDate` används för förfallodatum eftersom ett sådant datum inte behöver en tidpunkt. `OffsetDateTime` används för skapad/uppdaterad tid och tjänstelagret sätter dessa värden i UTC. ORM-lagret behöver därmed inte gissa applikationens tidssemantik.

`createdAt` är dessutom `updatable = false`. Det uttrycker i mappningen att kolumnen inte ska ingå i normala SQL-uppdateringar efter att entiteten skapats.

Mappningen är dock inte databasschemat i sig. TaskBoard låter Flyway äga schemats utveckling och har Hibernate ORM satt till validering. Vi återkommer till det i kapitel 9.

## UUID skapas som entitetens identitet

Id-fältet är:

```java
@Id
@GeneratedValue(strategy = GenerationType.UUID)
public UUID id;
```

Det innebär att applikationen inte behöver skapa ett eget sekvensvärde eller ett manuellt UUID före `persist`. Persistence-providern hanterar genereringen enligt den valda strategin.

För TaskBoard passar UUID bra eftersom id:t används hela vägen från backend till REST-URL:

```text
/api/tasks/550e8400-e29b-41d4-a716-446655440000
```

Det finns inget krav på att alla tjänster ska välja UUID. Sekvensbaserade numeriska nycklar är också utmärkta i många system. Poängen är att valet görs i persistence-modellen och att resten av TaskBoard behandlar id:t som en domänneutral identifierare.

## Repositoryt kapslar in EntityManager

`TaskRepository` är en vanlig CDI-bean:

```java
@ApplicationScoped
public class TaskRepository {
    @Inject
    EntityManager entityManager;
}
```

Quarkus skapar och injicerar den `EntityManager` som hör till standard-persistence-uniten. I Quarkus är den injicerade instansen en proxy kopplad till rätt persistence context för den aktuella exekveringen. (Quarkus, *Using Hibernate ORM and Jakarta Persistence*.)

Repositoryt erbjuder fyra operationstyper:

```java
list(...)
find(...)
persist(...)
delete(...)
```

Det är ett tunt lager. Det försöker inte dölja att implementationen använder JPA genom en stor egen generell repository-abstraktion.

Det är ett bra avvägningsval för referensprojektet. Ett repository ska ge applikationen en meningsfull persistence-gräns, men behöver inte reproducera hela `EntityManager`-API:t under nya metodnamn.

## Find ger en hanterad entitet

En enskild uppgift hämtas så här:

```java
public Optional<TaskEntity> find(UUID id) {
    return Optional.ofNullable(entityManager.find(TaskEntity.class, id));
}
```

`EntityManager.find` hämtar entiteten med den angivna primärnyckeln. När anropet sker i en aktiv persistence context blir resultatet en managed entity.

Det märks tydligast i `TaskService.update`:

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

Det finns inget explicit `repository.update(entity)` och inget `entityManager.merge(entity)`.

Det behövs inte här. Entiteten hämtades i samma transaktion och är managed. När dess fält förändras registrerar persistence-providern förändringarna och synkroniserar dem mot databasen när persistence context flushas, normalt senast vid commit.

Detta är JPA:s dirty checking i praktiken.

Det är också en viktig anledning att förstå transaktionsgränsen. Om man kopierar samma kod till ett sammanhang där entiteten har blivit detached ändras förutsättningarna. "Ändra Java-fält och returnera" fungerar inte magiskt för alla objekt; det fungerar eftersom objektet är en managed entity i rätt persistence context.

## Persist gör en ny entitet managed

Create-flödet är lika kompakt:

```java
var entity = new TaskEntity();
entity.title = request.title().trim();
// ...
repository.persist(entity);
```

Repositoryt gör bara:

```java
public void persist(TaskEntity entity) {
    entityManager.persist(entity);
}
```

Efter `persist` hanteras entiteten av persistence context. INSERT-operationen behöver inte nödvändigtvis ha skickats till databasen exakt på den raden; JPA kan synkronisera senare vid flush. För applikationskoden är den viktiga enheten därför transaktionen, inte ett antagande om att varje EntityManager-metod omedelbart motsvarar ett SQL-anrop.

Detta syns i create-metoden eftersom TaskBoard mappar entiteten till `TaskResponse` innan metoden lämnar transaktionsgränsen. Det genererade id:t finns då tillgängligt för svaret enligt den valda identifieringsstrategin.

## Delete kräver också en managed entitet

Delete-flödet är:

```java
@Transactional
public void delete(UUID id) {
    repository.delete(required(id));
}
```

och repositoryt:

```java
public void delete(TaskEntity entity) {
    entityManager.remove(entity);
}
```

`required(id)` hämtar först entiteten. Därmed får `remove` en managed instans i samma transaktion.

Det är ett enkelt mönster men visar samma grundprincip som update: service-metodens transaktion håller ihop load och mutation. Persistence-lagret behöver inte skicka runt detached objekt och försöka rekonstruera deras tillstånd senare.

## Listningen använder JPQL, inte SQL

TaskBoards listfråga är:

```java
return entityManager.createQuery(
        """
        select t from TaskEntity t
        where (:status is null or t.status = :status)
          and (:priority is null or t.priority = :priority)
        order by t.createdAt desc
        """, TaskEntity.class)
    .setParameter("status", status)
    .setParameter("priority", priority)
    .getResultList();
```

Frågan använder entitetsnamn och Java-attribut: `TaskEntity`, `t.status`, `t.priority` och `t.createdAt`. Det är JPQL, inte SQL mot tabellen `task_item` och dess fysiska kolumnnamn.

Båda filtren är frivilliga. Samma fråga hanterar därför:

```text
ingen filtrering
status=OPEN
priority=HIGH
status=OPEN + priority=HIGH
```

För ett så litet sökbehov är den statiska JPQL-frågan lätt att läsa. Vid många kombinerbara filter skulle Criteria API, en query builder eller ett annat sökmönster kunna bli mer lämpligt. Referensimplementationen introducerar inte den komplexiteten innan den behövs.

Det typade anropet `createQuery(..., TaskEntity.class)` gör dessutom att resultatlistan redan är en `List<TaskEntity>` i stället för en rå lista som måste castas.

## Transaktionen tillhör applikationsoperationen

I TaskBoard sitter `@Transactional` på de muterande servicemetoderna:

```java
@Transactional
public TaskResponse create(...)

@Transactional
public TaskResponse update(...)

@Transactional
public void delete(...)
```

Det är en viktig arkitekturmarkering. Transaktionen motsvarar en applikationsoperation, inte en enskild repository-metod.

Tänk på update:

```text
1. hämta task
2. kontrollera att den finns
3. ändra flera attribut
4. uppdatera tidsstämpel
5. flush/commit
```

Det ska vara en sammanhängande enhet. Om repositoryts `find` och en hypotetisk `save` var separata transaktioner skulle gränsen hamna på fel nivå.

Quarkus Hibernate ORM-guiden rekommenderar att databasmodifierande metoder körs inom en transaktion och beskriver `@Transactional` som transaktionsgränsen där den injicerade `EntityManager` deltar och flushas vid commit. (Quarkus, *Using Hibernate ORM and Jakarta Persistence*.)

TaskBoards läsmetoder saknar explicit `@Transactional`. Quarkus tillåter som standard användning av den request-scopade EntityManager-proxyn för read-only-operationer i requestkontext, medan skrivningar ska ligga i transaktion. Det är ett Quarkus-beteende som man bör känna till om man senare ändrar `quarkus.hibernate-orm.request-scoped.enabled`. (Quarkus, *Using Hibernate ORM and Jakarta Persistence*.)

## `@Version` skyddar mot samtidiga databasuppdateringar

Sista fältet i `TaskEntity` är:

```java
@Version
@Column(nullable = false)
public long version;
```

Jakarta Persistence använder versionsfältet för optimistisk låsning. När en versionerad entitet uppdateras kontrollerar persistence-providern att versionen som lästes fortfarande motsvarar versionen i databasen. Om en annan transaktion redan har ändrat samma rad ska en optimistisk låsningskonflikt upptäckas i stället för att uppdateringen tyst skriver över den parallella ändringen. (Jakarta Persistence, *Jakarta Persistence Specification 3.2*, avsnitt om entity versions och optimistic locking.)

En förenklad mental modell är:

```text
Transaktion A läser version 4
Transaktion B läser version 4
Transaktion A skriver -> version 5
Transaktion B försöker skriva version 4 -> konflikt
```

Det är viktigt att inte övertolka vad TaskBoard därmed löser.

`version` exponeras inte i `TaskResponse` och klienten skickar ingen förväntad version vid PUT. `@Version` skyddar alltså mot överlappande persistence-transaktioner som arbetar med samma rad. Det ger inte automatiskt ett HTTP-kontrakt för "uppdatera bara om klientens tidigare representation fortfarande är aktuell".

Ett sådant API skulle kunna exponera versionsinformation, använda ett explicit versionsfält i requesten eller HTTP-mekanismer som ETag/`If-Match`. Det har referensimplementationen inte byggt. Vi ska därför inte tillskriva den starkare concurrency-semantik än den faktiskt har.

Den distinktionen är typisk för hela boken: ORM kan lösa en persistence-fråga utan att därmed lösa motsvarande distribuerade system-fråga.

## Schema-validering i stället för automatisk schemaevolution

I `application.properties` står:

```properties
quarkus.hibernate-orm.schema-management.strategy=validate
```

Hibernate ORM får alltså kontrollera att den modell som applikationen startar med är förenlig med databasschemat. Den används inte för att automatiskt skapa eller förändra produktionsschemat.

Det är medvetet.

Entitetsmappningen svarar på frågan:

> Hur mappar Java-modellen mot det schema som tjänsten förväntar sig?

Flyway-migrationerna svarar på en annan fråga:

> Hur går databasen kontrollerat från schema-version N till N+1?

När de två ansvarsområdena separeras får vi både en tydlig kodmodell och en explicit historik över schemaförändringar. Hibernate kan då fungera som en startkontroll som fångar mismatch, snarare än som ett osynligt produktionsmigrationsverktyg.

I nästa kapitel tittar vi först på själva PostgreSQL-databasen. Därefter, i kapitel 9, följer vi hur Flyway gör schemat reproducerbart över miljöer.

## JPA behöver inte dominera arkitekturen

TaskBoards persistencekod är liten nog att sammanfatta:

```text
TaskEntity
  mappar Java-fält till schema

TaskRepository
  kapslar EntityManager och queries

TaskService
  äger applikationsregler och transaktionsgräns

Flyway
  äger schemahistoriken
```

Det här är den viktigaste designpoängen i kapitlet.

JPA är mycket kapabelt, men varje kapabilitet behöver inte synas i varje lager. TaskBoard använder ORM där den ger konkret värde:

- typad entitetsmappning,
- persistence context,
- dirty checking,
- JPQL,
- transaktionsintegration,
- optimistisk låsning.

Samtidigt får REST-kontraktet egna DTO:er, tjänstelagret äger applikationsreglerna och Flyway äger schemaevolutionen.

Resultatet är inte "JPA-arkitektur". Det är en tjänstearkitektur där JPA är persistence-mekanismen.

Det är en betydligt bättre utgångspunkt när tjänsten senare behöver förändras.
