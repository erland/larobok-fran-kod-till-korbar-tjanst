# 8. PostgreSQL som databas

I kapitel 7 såg vi databasen genom JPA:s ögon: `TaskEntity`, `EntityManager`, queries och transaktionsgränser. Det perspektivet är viktigt, men det räcker inte för att förstå en driftbar tjänst. Under ORM-lagret finns en faktisk PostgreSQL-instans med egna datatyper, constraints, index, anslutningar och datafiler.

TaskBoard använder PostgreSQL 18.4. I den produktionslika Compose-miljön är databasen en egen tjänst:

```text
Quarkus backend
      |
      | JDBC
      v
PostgreSQL 18.4
      |
      v
persistent Docker volume
```

Kapitlet är inte en allmän PostgreSQL-kurs. Fokus ligger på de delar en applikationsutvecklare måste förstå för att kunna resonera korrekt om referenstjänsten: vad som faktiskt lagras, hur anslutningen fungerar, vilka garantier databasschemat ger, varför vissa index finns och vad en persistent volume betyder för livscykeln.

## Databasen är en separat runtime-komponent

Compose-definitionen börjar så här:

```yaml
services:
  db:
    image: postgres:18.4-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-taskboard}
      POSTGRES_USER: ${POSTGRES_USER:-taskboard}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-taskboard-change-me}
```

När den officiella PostgreSQL-imagen initieras första gången används dessa variabler för att skapa den databas och användare som applikationen ska arbeta mot.

Backend-containern får motsvarande anslutningsdata:

```yaml
environment:
  QUARKUS_DATASOURCE_JDBC_URL: jdbc:postgresql://db:5432/${POSTGRES_DB:-taskboard}
  QUARKUS_DATASOURCE_USERNAME: ${POSTGRES_USER:-taskboard}
  QUARKUS_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD:-taskboard-change-me}
```

Det viktiga i URL:n är inte bara databasnamnet utan värdnamnet `db`:

```text
jdbc:postgresql://db:5432/taskboard
                  ^^
```

Det är Compose-tjänstens namn. Backend behöver inte känna till containerns IP-adress. Docker-nätverket ger service discovery mellan containrarna, vilket vi såg i kapitel 2.

PostgreSQL-port 5432 publiceras däremot inte till värddatorn i den här Compose-filen. Databasen är därför inte en extern endpoint för användare eller webbläsare. Den nås av backend över det interna Compose-nätverket.

Det är en bra standard för en sådan här tjänst: exponera den HTTP-ingång som faktiskt behövs och låt databasen vara en intern komponent.

## Datasource-konfigurationen hör till körmiljön

I `application.properties` finns bara den databasspecifika typen:

```properties
quarkus.datasource.db-kind=postgresql
```

Den konkreta JDBC-URL:n och inloggningsuppgifterna kommer i Compose-miljön från environment variables.

Det är en medveten uppdelning. Applikationen behöver veta att den arbetar med PostgreSQL, eftersom drivrutin och SQL-dialekt beror på databastypen. Men adress, användarnamn och lösenord är runtime-konfiguration och bör kunna variera mellan utveckling, CI och drift.

Det innebär också att samma backend-image kan startas mot olika PostgreSQL-instanser utan att byggas om.

I lokal Quarkus-utveckling kan Dev Services skapa en PostgreSQL-container automatiskt när ingen explicit datasource-URL är satt. I Compose är databasen däremot deklarerad uttryckligen. De två arbetssätten har samma applikationsmodell men olika ansvar för runtime-miljön.

## Det verkliga schemat består av nio kolumner

TaskBoards första migration skapar tabellen:

```sql
CREATE TABLE task_item (
    id UUID PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL,
    priority VARCHAR(32) NOT NULL,
    due_date DATE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    version BIGINT NOT NULL DEFAULT 0
);
```

Detta är databasens kontrakt. JPA-mappningen ska stämma med det, men PostgreSQL är den komponent som faktiskt lagrar raderna och verkställer SQL-constraints.

Kolumnerna kan delas in i fyra grupper:

```text
identitet        id
innehåll         title, description
klassificering   status, priority, due_date
audit/concurrency created_at, updated_at, version
```

Att läsa schemat på det sättet gör det lättare att se varför olika SQL-typer har valts.

## UUID är en riktig PostgreSQL-typ

Primärnyckeln är:

```sql
id UUID PRIMARY KEY
```

PostgreSQL har en inbyggd `uuid`-typ. Den lagrar UUID som ett 128-bitars värde i stället för som godtycklig text. PostgreSQL kan lagra UUID oavsett om värdet genererades i databasen eller i applikationslagret. (PostgreSQL, *UUID Type*.)

I TaskBoard genereras identifieraren genom JPA:

```java
@GeneratedValue(strategy = GenerationType.UUID)
public UUID id;
```

Databasen ansvarar alltså inte för själva genereringsalgoritmen i den här implementationen. Däremot lagrar och indexerar den id:t som rätt datatyp.

`PRIMARY KEY` innebär dessutom två centrala garantier: värdet måste vara unikt och får inte vara `NULL`. PostgreSQL skapar också ett unikt B-tree-index för primärnyckeln. (PostgreSQL, *Constraints*.)

Det gör uppslag som:

```java
entityManager.find(TaskEntity.class, id)
```

effektiva utan att projektet behöver skapa ett separat index för `id`.

## VARCHAR och TEXT uttrycker olika begränsningar

Titeln lagras som:

```sql
title VARCHAR(160) NOT NULL
```

Det matchar JPA-mappningen:

```java
@Column(nullable = false, length = 160)
public String title;
```

Här finns alltså en databasconstraint som skyddar mot `NULL` och en längdgräns på 160 tecken.

Det är värt att skilja den garantin från HTTP-valideringen i `SaveTaskRequest`. API-lagret kan ge ett snabbt och begripligt 400-svar när en titel är ogiltig. Databasens constraint är den sista integritetsgränsen om data skulle nå persistens-lagret från någon annan kodväg.

Beskrivningen är i stället:

```sql
description TEXT
```

Den får vara `NULL` och har ingen applikationsspecifik maxlängd i schemat. Det passar TaskBoards modell där tom eller blank beskrivning normaliseras till `null`.

Poängen är inte att `VARCHAR` alltid är bättre än `TEXT`, utan att schemat bör uttrycka verkliga krav. Titeln har en definierad produktgräns; beskrivningen har det inte i referensimplementationen.

## Enumvärden lagras som läsbara strängar

`status` och `priority` är:

```sql
status VARCHAR(32) NOT NULL,
priority VARCHAR(32) NOT NULL
```

JPA använder `EnumType.STRING`, så databasen får värden som:

```text
OPEN
DONE
LOW
NORMAL
HIGH
```

Det ger ett schema som är enkelt att inspektera manuellt och mindre känsligt för om Java-enumernas deklarationsordning ändras.

Men notera en viktig detalj: databasen har i dag ingen `CHECK`-constraint som begränsar kolumnerna till just dessa värden.

PostgreSQL garanterar alltså att `status` och `priority` inte är `NULL` och att texten ryms i 32 tecken, men inte att texten motsvarar en giltig Java-enum.

I den nuvarande arkitekturen skyddas detta huvudsakligen av applikationen och JPA. Om flera system skulle skriva direkt mot samma databas vore en databasconstraint eller en annan modell värd att överväga.

Det är ett bra exempel på varför man måste skilja mellan *vad Java-modellen säger* och *vad databasen själv kan garantera*.

## DATE och TIMESTAMPTZ har olika semantik

Ett förfallodatum är:

```sql
due_date DATE
```

Det motsvarar Java-typen `LocalDate`. Ett datum som 2026-08-31 har ingen inbyggd klockslagstid eller tidszon, vilket passar betydelsen "förfaller den här dagen".

Skapad och uppdaterad tid lagras däremot som:

```sql
created_at TIMESTAMPTZ NOT NULL,
updated_at TIMESTAMPTZ NOT NULL
```

`TIMESTAMPTZ` är PostgreSQLs namnform för `timestamp with time zone`. TaskBoard sätter värdena från `OffsetDateTime` i UTC.

Det är en mer lämplig modell för faktiska tidpunkter än att lagra lokal klocktid utan tidszonskontext.

En viktig PostgreSQL-detalj är att `timestamp with time zone` representerar en absolut tidpunkt. PostgreSQL normaliserar tidszonsmedvetna indata internt och visar värdet enligt sessionens tidszon vid output. Det betyder att applikationen ska tänka i *instant/offset-semantik*, inte förvänta sig att PostgreSQL bevarar exakt den ursprungliga textuella offsetrepresentationen.

TaskBoards val att skapa tidsstämplar i UTC gör detta lättare att resonera om.

## Version är både data och samtidighetsmekanism

Den sista kolumnen är:

```sql
version BIGINT NOT NULL DEFAULT 0
```

JPA markerar motsvarande fält med `@Version`:

```java
@Version
@Column(nullable = false)
public long version;
```

Som vi såg i kapitel 7 används värdet av Hibernate ORM för optimistisk låsning. PostgreSQL lagrar det som `BIGINT` och ser till att värdet inte är `NULL`.

Databasen känner däremot inte själv till JPA:s optimistiska låsningsprotokoll. Det är ORM-lagret som genererar SQL där versionsvärdet ingår och som upptäcker om en samtidig uppdatering har gjort villkoret ogiltigt.

Återigen samarbetar lagren: databasen ger atomiska SQL-operationer och lagrar versionskolumnen; JPA använder den för ett högre nivå-kontrakt.

## Indexen speglar läsmodellen

Efter tabellen skapar migrationen tre index:

```sql
CREATE INDEX idx_task_item_status ON task_item(status);
CREATE INDEX idx_task_item_priority ON task_item(priority);
CREATE INDEX idx_task_item_created_at ON task_item(created_at DESC);
```

De motsvarar den huvudsakliga listfrågan:

```java
select t from TaskEntity t
where (:status is null or t.status = :status)
  and (:priority is null or t.priority = :priority)
order by t.createdAt desc
```

Det är logiskt att indexera kolumner som används för filtrering och sortering. PostgreSQLs dokumentation betonar samtidigt att index inte är gratis: de kan göra läsningar snabbare men kostar lagring och underhåll vid skrivningar. De bör därför väljas utifrån faktisk query-belastning. (PostgreSQL, *Indexes*.)

TaskBoards tre index är rimliga för referensimplementationen, men de ska inte läsas som en universell optimal lösning.

Exempelvis kan en större datamängd och ett vanligt kombinerat filter på status och prioritet motivera ett sammansatt index. Om nästan alla rader har samma status kan ett enskilt statusindex ge mindre nytta än man först tror. PostgreSQLs query planner avgör dessutom om ett index faktiskt används för en viss fråga.

Den robusta arbetsmetoden är därför:

1. utgå från de frågor tjänsten faktiskt gör,
2. skapa rimliga initiala index,
3. observera verklig belastning,
4. använd `EXPLAIN`/`EXPLAIN ANALYZE` när prestanda behöver analyseras,
5. ändra index med en versionshanterad migration.

Index är en del av databasdesignen, inte dekorativa standardrader som läggs till på alla kolumner.

## Healthchecken testar databasserverns tillgänglighet

Compose-konfigurationen innehåller:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-taskboard} -d ${POSTGRES_DB:-taskboard}"]
  interval: 5s
  timeout: 3s
  retries: 10
  start_period: 5s
```

Backend startas först när `db` är `service_healthy`.

Detta löser ett konkret runtime-problem: att en containerprocess har startats betyder inte att PostgreSQL redan är redo att ta emot anslutningar. Healthchecken ger Compose ett bättre tillstånd att synkronisera mot.

Men `pg_isready` är inte ett fullständigt funktionstest av TaskBoard. Det verifierar databasens anslutningsberedskap, inte att Flyway-migrationen lyckas eller att applikationens CRUD-flöde fungerar. Därför behövs även backend-healthcheck och det end-to-end-smoke test som CI kör.

Vi får alltså flera nivåer av verifiering:

```text
pg_isready
    -> PostgreSQL kan ta emot anslutningar

/q/health/ready
    -> Quarkus är redo

HTTP smoke test
    -> hela tjänstekedjan fungerar
```

## Data måste överleva containern

Den kanske viktigaste raden i databasens Compose-definition är:

```yaml
volumes:
  - taskboard-postgres:/var/lib/postgresql
```

och längst ned:

```yaml
volumes:
  taskboard-postgres:
```

`taskboard-postgres` är en named volume. PostgreSQLs datafiler ligger därmed utanför den enskilda containerinstansens skrivbara lager.

Det betyder att följande två livscykler skiljs åt:

```text
container
kan tas bort och skapas om

volume
kan leva kvar och återanvändas
```

Det är avgörande för en databas. En image och en container är utbytbara körningsartefakter; applikationsdata är det inte.

Det betyder dock inte att en Docker-volume automatiskt är en backup. Om volymen skadas, raderas eller innehåller logiskt felaktiga data hjälper inte det faktum att den är persistent. Backup, restore och uppgraderingsstrategi är separata driftfrågor som vi återkommer till i kapitel 15.

## PostgreSQL 18 ändrade volymens mountpunkt

TaskBoard använder medvetet:

```text
/var/lib/postgresql
```

inte den äldre:

```text
/var/lib/postgresql/data
```

Detta är versionsberoende. I Docker Official Image för PostgreSQL 18 ändrades standardvärdet för `PGDATA` till en versionsspecifik katalog, `/var/lib/postgresql/18/docker`, och image-definitionens `VOLUME` flyttades till `/var/lib/postgresql`. Den officiella image-dokumentationen rekommenderar därför att mounts för version 18 och senare riktas mot `/var/lib/postgresql`. (Docker Official Image for PostgreSQL, *PGDATA*.)

Den skillnaden var inte teoretisk i vårt projekt. En tidigare CI-version använde den gamla mountpunkten och PostgreSQL-containern kunde inte starta korrekt. När Compose ändrades till:

```yaml
- taskboard-postgres:/var/lib/postgresql
```

startade PostgreSQL 18.4 och blev healthy.

Det är en konkret illustration av varför exakta image-versioner och primärdokumentation spelar roll. En Compose-fil som var korrekt för en äldre majorversion behöver inte vara korrekt efter en majoruppgradering.

## Persistens är mer än att "ha en databas"

När alla delarna sätts ihop har TaskBoard flera separata skydd:

```text
HTTP-validering
      |
      v
Java/JPA-typer
      |
      v
SQL-datatyper och constraints
      |
      v
PostgreSQL-transaktioner
      |
      v
persistent volume
```

Varje nivå löser olika problem.

Bean Validation kan ge användaren ett begripligt 400-svar. JPA mappar domänens Java-typer. PostgreSQL upprätthåller primärnyckel, `NOT NULL` och SQL-datatyper. Databasmotorn ger transaktionella operationer. Volymen separerar data från containerlivscykeln.

Ingen enskild nivå ersätter de andra.

Det är också därför en robust tjänst inte bör behandla databasen som en svart låda bakom ORM. Applikationsutvecklaren behöver inte vara heltids-DBA, men måste förstå det schema och den runtime-konfiguration som tjänsten faktiskt förlitar sig på.

## Databasen är persistent – schemat måste också vara reproducerbart

Vi har nu sett vad TaskBoard-databasen består av vid en given tidpunkt. Nästa problem uppstår när den modellen behöver förändras.

En ny release kanske lägger till en kolumn, ändrar ett index eller introducerar en ny constraint. Då räcker det inte att JPA-entiteten ändras i Git. En redan existerande PostgreSQL-volume innehåller fortfarande det gamla schemat.

Det leder direkt till nästa kapitel:

```text
applikationskod förändras
        +
existerande databas måste uppgraderas
        =
versionshanterade schemaändringar
```

I TaskBoard är det Flyway som äger den processen.
