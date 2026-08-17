# 9. Databasschemat som kod med Flyway

I kapitel 8 såg vi PostgreSQL som en egen runtime-komponent med tabeller, datatyper, constraints, index och persistent lagring. Nästa fråga är hur samma schema kan återskapas och utvecklas på ett kontrollerat sätt när applikationen förändras.

Det räcker inte att databasen *råkar* ha rätt struktur på utvecklarens dator. En driftbar tjänst behöver kunna ta en tom databas till rätt version och, ännu viktigare, uppgradera en redan använd databas utan att data kastas bort.

TaskBoard löser det med Flyway.

I referensimplementationen finns i dag en enda migration:

```text
backend/
└── src/main/resources/
    └── db/migration/
        └── V1__create_task.sql
```

Quarkus är konfigurerat att köra migrationerna automatiskt vid start:

```properties
quarkus.flyway.migrate-at-start=true
quarkus.flyway.locations=db/migration
```

Samtidigt är Hibernate ORM satt till:

```properties
quarkus.hibernate-orm.schema-management.strategy=validate
```

Den kombinationen uttrycker en viktig arkitekturprincip:

```text
Flyway      äger schemaevolutionen
Hibernate   validerar att Java-modellen passar schemat
```

Det är kärnan i kapitlet.

## Schemat måste vara reproducerbart

Tänk dig två miljöer:

```text
Utvecklarens dator        Test-/driftmiljö
------------------        ----------------
Databas finns redan       Ny tom databas
Tabeller skapades igår    Ingen tabell finns
```

Om databasschemat bara byggs genom manuella SQL-kommandon eller genom att ORM-lagret automatiskt skapar tabeller blir det svårt att svara på frågor som:

- Vilka steg skapade databasen?
- Vilken databasversion hör till en viss applikationsrelease?
- Hur uppgraderar vi en befintlig installation?
- Har två miljöer verkligen fått samma ändringar?
- Vad händer om en gammal migrationsfil ändras i efterhand?

Flyway behandlar i stället schemaändringar som versionshanterad kod.

En migration är en fil som beskriver en förändring från ett känt läge till nästa. Versionerade migrationer körs i versionsordning och normalt bara en gång per databas. Flyway registrerar vad som har körts i sin schemahistorik och lagrar även checksummor för att upptäcka att en redan applicerad versionerad migration har ändrats. (Redgate Flyway, *Versioned migrations*.)

Det gör databashistoriken explicit.

## V1 skapar TaskBoards första schema

Referensimplementationens faktiska fil heter:

```text
V1__create_task.sql
```

Namnet kan läsas som:

```text
V       versionerad migration
1       versionsnummer
__      separator
create_task  beskrivning
.sql    SQL-migration
```

Flyways standardkonvention för versionerade SQL-migrationer följer samma modell: prefix, version, dubbel underscore, beskrivning och suffix. Quarkus använder Flyways vanliga `db/migration` som standardplats och TaskBoard anger samma location uttryckligen. (Quarkus, *Using Flyway*.)

Filen innehåller hela den första databasutvecklingen:

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

CREATE INDEX idx_task_item_status ON task_item(status);
CREATE INDEX idx_task_item_priority ON task_item(priority);
CREATE INDEX idx_task_item_created_at ON task_item(created_at DESC);
```

Det betyder att en tom PostgreSQL-databas inte behöver någon manuell förberedelse av `task_item`. När backend startar kan Flyway applicera `V1` och skapa både tabellen och indexen.

Det är samma schema som vi analyserade i kapitel 8, men här betraktar vi det som ett *versionssteg* i stället för som ett statiskt slutresultat.

## Migrate-at-start kopplar schemat till applikationsstarten

TaskBoard har:

```properties
quarkus.flyway.migrate-at-start=true
```

Quarkus dokumenterar att detta gör att Flyway kör migrationerna som en del av applikationens startup. (Quarkus, *Using Flyway*.)

I Compose-flödet blir den förenklade ordningen därför:

```text
PostgreSQL blir healthy
        |
        v
backend startar
        |
        v
Flyway kontrollerar schemahistorik
        |
        +--> kör ej applicerade migrationer
        |
        v
Hibernate validerar mappningen mot schemat
        |
        v
Quarkus blir redo
```

Det här är mer än bekvämlighet. Det innebär att applikationen själv bär med sig de SQL-steg som krävs för dess förväntade databasschema.

Det finns andra möjliga driftsmodeller, exempelvis att migrationer körs i ett separat deploy-steg innan applikationen startas. För TaskBoards referensimplementation är `migrate-at-start` däremot ett medvetet enkelt val: samma backend-artefakt innehåller både applikationskod och migrationsresurser.

## Hibernate ska inte konkurrera med Flyway

När en ORM finns tillgänglig är det frestande att låta den skapa eller uppdatera databasschemat automatiskt. Det kan vara praktiskt tidigt i utvecklingen, men det ger ett annat ansvarsförhållande.

TaskBoard använder i stället:

```properties
quarkus.hibernate-orm.schema-management.strategy=validate
```

Hibernate får alltså inte uppdraget att evolvera produktionsschemat. Det ska kontrollera att den mappade Java-modellen kan användas mot den struktur som redan finns efter Flyways migrationer.

Quarkus beskriver Flyway som vägen från tidig automatisk schemagenerering till en produktionsmodell där schemaändringar hanteras med migrationer. (Quarkus, *Using Hibernate ORM and Jakarta Persistence*.)

Det ger en tydligare ansvarsfördelning:

| Lager | Ansvar |
|---|---|
| Flyway | Skapa och förändra databasschemat i kontrollerad ordning |
| PostgreSQL | Lagra data och verkställa SQL-schema/constraints |
| Hibernate ORM | Mappa Java-objekt och validera att mappningen passar schemat |
| Applikationskod | Använda modellen och genomföra verksamhetsoperationer |

Om `TaskEntity` ändras utan motsvarande migration, eller om migrationen skapar en struktur som inte längre matchar entiteten, ska detta behandlas som ett fel som behöver rättas — inte som något Hibernate tyst ska skriva om i databasen.

## Nästa ändring ska bli V2, inte en omskriven V1

Anta att TaskBoard senare behöver en ny kolumn:

```text
archived_at TIMESTAMPTZ
```

När `V1__create_task.sql` redan har körts i en permanent miljö bör vi inte ändra V1 för att låtsas att kolumnen alltid har funnits.

I stället skapar vi exempelvis:

```text
V2__add_archived_at.sql
```

med:

```sql
ALTER TABLE task_item
ADD COLUMN archived_at TIMESTAMPTZ;
```

Detta är ett hypotetiskt exempel; `V2__add_archived_at.sql` finns inte i den nuvarande referensimplementationen.

En ny installation får då:

```text
V1  skapa task_item
V2  lägg till archived_at
```

En befintlig installation där V1 redan har körts får bara:

```text
V2  lägg till archived_at
```

Det är själva poängen med schemaevolution.

Flyways rekommenderade modell för versionerade migrationer är att inte redigera en migration som redan har applicerats i permanenta downstream-miljöer, utan att lägga till en ny migration och rulla framåt. Flyway använder checksumman i historiken för att upptäcka ändringar av redan körda migrationer. (Redgate Flyway, *Versioned migrations*.)

## En migration bör vara kompatibel med en verklig uppgradering

Det räcker inte att SQL-syntaxen fungerar mot en tom databas.

En schemaändring ska också fungera mot data som redan finns.

Anta exempelvis att vi vill göra `description` obligatorisk. Den naiva migrationen vore:

```sql
ALTER TABLE task_item
ALTER COLUMN description SET NOT NULL;
```

Den fungerar bara om ingen befintlig rad har `NULL` i `description`.

I en använd databas kan en säkrare evolution behöva delas upp:

```text
1. introducera nytt schema som tolererar gamla data
2. migrera eller fyll befintliga rader
3. ändra applikationen
4. skärp constraint när datan är kompatibel
```

Exakt ordning beror på ändringen och på hur deployment sker. Den viktiga lärdomen är att migrationer beskriver *förändring av ett existerande tillstånd*, inte bara skapandet av ett önskat slutläge.

Det blir särskilt viktigt när flera applikationsinstanser kan vara igång under en utrullning. Då kan gamla och nya versioner behöva fungera mot samma övergångsschema under en period.

TaskBoard har ingen sådan zero-downtime-deploymentmodell i dag, men migrationsdisciplinen bör ändå göra sådana framtida krav möjliga i stället för att blockera dem.

## Schemahistoriken är Flyways minne

När Flyway arbetar med en databas använder det en schema history table för att registrera migrationernas status och ordning. Därifrån kan Flyway avgöra vilka versioner som redan är applicerade och om tillgängliga migrationsfiler fortfarande stämmer med historiken. (Redgate Flyway, *Flyway schema history table*.)

Konceptuellt kan man tänka:

```text
Databas
├── task_item
└── flyway_schema_history
       ├── V1 applicerad
       ├── checksum för V1
       └── metadata om körningen
```

Det är därför en permanent databas och migrationskatalogen tillsammans utgör en historik. En migrationsfil är inte bara installations-SQL; efter att den har applicerats blir den en del av det dokumenterade ursprunget för databasen.

Det är också skälet till att man ska vara försiktig med att radera gamla versionerade migrationer bara för att de känns historiska.

## Repair är inte ett vanligt sätt att ändra historien

Flyway har ett `repair`-kommando. Det kan bland annat justera metadata/checksummor i schemahistoriken och hantera vissa trasiga historiktillstånd. (Redgate Flyway, *Repair*.)

Det betyder inte att `repair` bör användas rutinmässigt för att göra det legitimt att skriva om redan publicerade migrationer.

En sund huvudregel är:

```text
Fel i en ännu opublicerad migration
    -> rätta migrationen

Ändring efter att migrationen nått permanent miljö
    -> skapa en ny framåtriktad migration

Skadad eller avsiktligt omstrukturerad Flyway-historik
    -> överväg repair med tydlig förståelse för konsekvenserna
```

Quarkus kan konfigureras för repair vid start, men TaskBoard gör inte det. Det är bra: automatisk historikreparation skulle vara ett starkt beteende att slå på utan ett konkret behov.

## Baseline behövs inte för TaskBoards gröna start

Flyway har också baseline-koncept för situationer där man börjar använda migrationshantering på en databas som redan har ett etablerat schema.

Det är inte TaskBoards nuvarande situation.

Referensimplementationen är byggd så att en tom databas kan skapas från `V1` och framåt. Det finns därför inget behov av att märka en äldre, redan existerande TaskBoard-databas som startpunkt.

Baseline blir relevant om man introducerar Flyway i ett äldre system där databasschemat redan finns, eller om migrationshistoriken efter många versioner behöver kompletteras med en kontrollerad startpunkt för nya miljöer. Flyways dokumentation skiljer också mellan att baselina en existerande miljö och särskilda baseline migrations för nya miljöer. (Redgate Flyway, *Baselines*; *Baseline migrations*.)

För en grön tjänst är den enklaste modellen fortfarande bäst:

```text
Tom databas -> V1 -> V2 -> V3 -> ...
```

## En framtida V3 kan visa varför versionsordning spelar roll

Anta att vi efter den hypotetiska V2 vill indexera arkiveringsfältet:

```text
V3__add_archived_at_index.sql
```

```sql
CREATE INDEX idx_task_item_archived_at
ON task_item(archived_at);
```

Även detta är bara ett undervisningsexempel och finns inte i dagens TaskBoard-kod.

Ordningen är meningsfull:

```text
V1  skapar tabellen
V2  skapar kolumnen
V3  skapar index på kolumnen
```

Om V3 försökte köras före V2 skulle kolumnen inte finnas.

Flyways versionsnummer är därför inte dekorativa etiketter. De uttrycker ett beroende mellan successiva databastillstånd.

## Applikationsrelease och databasversion hör ihop

När en release innehåller både Java-kod och en ny migration finns det i praktiken två kompatibilitetsfrågor:

```text
Ny kod <-> nytt schema
Gammal data <-> nytt schema
```

Det är lätt att bara testa den första genom att starta mot en ny tom databas. En robust leverans behöver också testa uppgraderingsvägen från ett tidigare databastillstånd.

För TaskBoard är den nuvarande CI:n ännu främst inriktad på att starta en ny Compose-miljö och smoke-testa hela requestkedjan. När migrationshistoriken får V2 och senare blir det värdefullt att komplettera med ett explicit uppgraderingstest:

```text
1. starta databas på tidigare schema
2. lägg in representativ data
3. starta nya backend-versionen
4. låt Flyway migrera
5. verifiera att gammal data finns kvar och ny kod fungerar
```

Det är en naturlig fördjupning i kapitel 12 om testning.

## Migrationsfilerna är en del av leveransen

`V1__create_task.sql` ligger under:

```text
src/main/resources/db/migration
```

Den packas därför med backend-applikationen. När Quarkus-runtime startar finns migrationsresursen tillgänglig i samma leverans som koden som kräver schemat.

Det ger ett starkt samband:

```text
backend-version
   |
   +-- Java-kod
   +-- JPA-mappning
   +-- Flyway-migrationer
```

Men det betyder också att en migrationsändring är en produktionsförändring även om ingen Java-fil ändras. SQL-filer under `db/migration` ska granskas, testas och versionshanteras med samma omsorg som applikationskoden.

## TaskBoards modell i ett stycke

Den nuvarande referensimplementationens schemahantering kan sammanfattas så här:

```text
PostgreSQL startar
      |
      v
Quarkus ansluter
      |
      v
Flyway läser db/migration
      |
      v
V1__create_task.sql appliceras om V1 saknas
      |
      v
Flyway registrerar migrationen i schemahistoriken
      |
      v
Hibernate ORM validerar JPA-modellen mot schemat
      |
      v
Applikationen kan ta emot trafik
```

Det är en liten implementation, men ansvarsfördelningen skalar väl.

När TaskBoard får sitt första verkliga schemaändringsbehov ska lösningen alltså inte vara att ändra databasen manuellt och inte heller att låta Hibernate gissa hur den ska uppdateras. Vi lägger till nästa migrationsversion, testar uppgraderingen och levererar den tillsammans med applikationen.

Databasschemat blir därmed inte något som lever vid sidan av koden. Det blir en versionshanterad del av tjänsten.
