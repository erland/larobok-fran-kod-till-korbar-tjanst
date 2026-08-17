# 15. Från lokal körning till driftbar tjänst

Efter kapitel 14 har TaskBoard passerat en viktig gräns. Lösningen består inte längre bara av källkod och lösa komponenter. Den kan byggas som Docker-images, startas som en sammanhållen Compose-applikation och verifieras genom ett riktigt requestflöde från Nginx via Quarkus till PostgreSQL.

Det betyder ändå inte att tjänsten är färdig för långvarig drift.

Att en tjänst startar är ett ögonblickstillstånd. Driftbarhet handlar om vad som händer dagen efter, nästa månad och vid nästa version. Hur ser vi att något är fel? Vad händer när värdmaskinen startar om? Hur återställer vi data efter ett misstag? Hur gör vi en uppgradering som innehåller en databasmigration? Vad gör vi om den nya versionen inte fungerar? Och vilka delar måste finnas utanför själva applikationskoden för att någon annan ska kunna förvalta lösningen?

Det här kapitlet flyttar därför perspektivet från **startbar tjänst** till **förvaltningsbar tjänst**.

TaskBoard är fortfarande en liten referensimplementation. Vi bygger inte ett komplett produktionsplattformslager runt den. I stället använder vi den för att identifiera de driftprinciper som bör vara tydliga även i en enkel installation.

## Driftbarhet är ett system av rutiner

Det finns ingen enskild Compose-nyckel som gör en tjänst driftbar.

En rimlig miniminivå består av flera samverkande delar:

```text
startbar tjänst
     |
     +-- hälsa och readiness
     +-- restart-beteende
     +-- loggar
     +-- beständig data
     +-- backup och restore
     +-- kontrollerad uppgradering
     +-- databasmigrationer
     +-- rollback-plan
     +-- driftkonfiguration
     +-- observability
     |
     v
förvaltningsbar tjänst
```

Några av dessa finns redan delvis i TaskBoard. Andra är medvetet kvar som driftkrav snarare än incheckad produktionskonfiguration.

Det är en viktig distinktion genom hela kapitlet: vi ska inte tillskriva referensimplementationen egenskaper som den ännu inte har.

## Hälsa svarar på mer än frågan "kör processen?"

TaskBoard har healthchecks för alla tre tjänsterna.

PostgreSQL kontrolleras med `pg_isready`. Backend kontrolleras via Quarkus readiness-endpoint och webbcontainern via Nginx-endpointen `/healthz`.

I Compose används detta för startordningen:

```text
db healthy
   |
   v
backend healthy
   |
   v
web
```

Det är redan betydligt bättre än att bara kontrollera om processerna existerar.

Men en healthcheck är fortfarande bara en definierad signal. Den säger det som kontrollen faktiskt testar, inte allt vi önskar veta om tjänsten.

Nginx `/healthz` visar exempelvis att Nginx kan svara. Den visar inte att Quarkus kan nå PostgreSQL eller att det går att skapa en uppgift. Det senare verifieras i CI av full-stack-smoke-testet.

I drift behöver man därför skilja på åtminstone tre nivåer:

- **processliv** – processen/containerinstansen kör,
- **readiness** – komponenten är redo att ta emot relevant trafik,
- **funktionell hälsa** – tjänstens viktiga användarflöden fungerar genom hela kedjan.

TaskBoards nuvarande healthchecks täcker de två första delvis. CI-smoke-testet ger dessutom en funktionell verifiering vid bygg/test. En verklig driftmiljö behöver besluta om motsvarande funktionella övervakning också ska ske kontinuerligt och i så fall hur ofta och med vilka bieffekter.

## Restart-policy är ett separat driftbeslut

TaskBoards nuvarande `docker-compose.yml` anger ingen `restart:`-policy.

Det är rimligt för en referens- och utvecklingsmiljö. En operatör som kör tjänsten på en ensam Docker-värd behöver däremot normalt bestämma hur containrar ska bete sig efter processfel eller om Docker-daemonen startas om.

Docker stödjer bland annat policyerna `on-failure`, `always` och `unless-stopped`. Docker rekommenderar restart policies framför att lägga en separat processmanager inuti varje container. (Docker Docs, *Start containers automatically*.)

Ett möjligt produktionsöverlägg skulle exempelvis kunna innehålla:

```yaml
services:
  db:
    restart: unless-stopped
  backend:
    restart: unless-stopped
  web:
    restart: unless-stopped
```

Detta är ett **driftexempel**, inte TaskBoards nuvarande Compose-konfiguration.

Det löser inte alla former av fel. En container som omedelbart kraschar på grund av felaktig konfiguration blir inte frisk för att den startas om om och om igen. Restart-policy måste därför kombineras med loggar, hälsokontroller och larm.

## Loggar ska vara åtkomliga utan att gå in i containern

En container bör betraktas som utbytbar. Felsökning ska därför inte förutsätta att någon loggar in i containern och letar efter lokala textfiler.

Docker kan samla `stdout` och `stderr` via olika logging drivers. Den officiella Nginx-imagen är anpassad så att access- och felloggar exponeras till dessa strömmar, vilket gör dem åtkomliga genom containerruntimen. (Docker Docs, *View container logs*.)

För en liten TaskBoard-installation är därför följande ett naturligt första felsökningskommando:

```bash
docker compose logs
```

eller mer avgränsat:

```bash
docker compose logs backend
```

Men "vi kan läsa loggen" är inte samma sak som en färdig loggningsstrategi.

Docker använder normalt `json-file` som standarddriver om inget annat konfigureras. Docker påpekar att den standardkonfigurationen inte roterar loggar automatiskt och därför kan växa tills värdens disk fylls; `local`-drivern rekommenderas som ett alternativ med rotation som standard. (Docker Docs, *Configure logging drivers*.)

En driftbar installation behöver alltså minst besluta:

- var loggar hamnar,
- hur länge de sparas,
- hur rotation fungerar,
- hur mycket disk de får använda,
- om loggar ska skickas vidare till ett centralt system,
- vilken information som inte får loggas.

För TaskBoard är detta fortfarande en driftfråga utanför referens-Compose-filen.

## Persistent volume är inte en backup

PostgreSQL-data ligger i TaskBoard i den namngivna volumen:

```text
taskboard-postgres
```

Det gör att data överlever att PostgreSQL-containern återskapas.

Men det skyddar inte mot alla viktiga fel.

Om en användare raderar fel data skrivs den nya, felaktiga staten till samma volume. Om en migration förstör information finns den förstörda informationen i volumen. Om värdmaskinens lagring går sönder kan också volumen försvinna. Och ett kommando som explicit tar bort volymer kan naturligtvis radera datalagret.

Persistent lagring löser alltså frågan:

> Ska data överleva containern?

Backup löser en annan fråga:

> Kan vi återskapa en tidigare användbar databas när den aktuella datan inte längre räcker?

De två får inte blandas ihop.

## En enkel backupmodell för TaskBoard

PostgreSQL beskriver tre huvudsakliga backupfamiljer: SQL/logiska dumps, filsystembackup och kontinuerlig arkivering/PITR. (PostgreSQL 18, *Backup and Restore*.)

För den lilla TaskBoard-installationen är en logisk dump ett pedagogiskt bra första steg. `pg_dump` kan skapa en konsistent export av en enskild databas samtidigt som andra klienter använder databasen. Ett custom-format kan senare läsas av `pg_restore`. PostgreSQL-dokumentationen påpekar samtidigt att `pg_dump` inte är den generella lösningen för regelbunden backup av större eller mer krävande produktionsdatabaser; där kan andra backupstrategier behövas. (PostgreSQL 18, *pg_dump*.)

Ett möjligt manuellt exempel är:

```bash
docker compose exec -T db \
  pg_dump -U taskboard -d taskboard -Fc \
  > taskboard-2026-08-17.dump
```

Det viktiga är inte exakt filnamn eller kommando utan egenskaperna runt processen:

1. backupen ska skapas regelbundet,
2. den ska lagras utanför den enda Docker-volumen,
3. retention ska vara definierad,
4. åtkomst till backupen ska skyddas,
5. återställning ska vara dokumenterad och testad.

I en verklig installation behöver credentials naturligtvis hanteras bättre än genom hårdkodade exempelvärden.

## En backup är inte verifierad förrän den går att återställa

Det är lätt att kontrollera att en backupfil existerar och ändå sakna en fungerande återställning.

En restoreövning bör därför vara en del av driftmodellen.

För ett custom-format från `pg_dump` används `pg_restore`. PostgreSQL beskriver hur arkivet kan återställas till en databas och hur objekt kan återskapas selektivt eller i annan ordning. (PostgreSQL 18, *pg_restore*.)

En säker testmodell är att återställa till en separat testdatabas eller testmiljö och kontrollera att applikationen kan läsa den förväntade datan.

```text
produktion
   |
   | pg_dump
   v
backupfil
   |
   | pg_restore
   v
separat testdatabas
   |
   v
verifiering av data och applikationsstart
```

Det är först efter den sista pilen vi vet att backupkedjan faktiskt fungerar.

Det här är en av de viktigaste driftprinciperna i hela boken:

**Backup är en process. Restore är beviset.**

## RPO och RTO gör backupdiskussionen konkret

Två frågor hjälper till att avgöra om en backupstrategi är tillräcklig:

- Hur mycket data får vi högst förlora?
- Hur länge får tjänsten vara otillgänglig innan den är återställd?

De uttrycks ofta som RPO, Recovery Point Objective, respektive RTO, Recovery Time Objective.

Om TaskBoard exempelvis får förlora högst ett dygns ändringar kan en daglig dump vara en möjlig utgångspunkt. Om högst några minuters data får gå förlorade räcker den inte. Då behöver man överväga tätare backup, WAL-baserad kontinuerlig arkivering/PITR, repliker eller en hanterad databastjänst beroende på kravbilden.

Poängen är inte att varje liten tjänst måste införa avancerad hög tillgänglighet. Poängen är att backupfrekvensen ska härledas från ett accepterat dataförlustmål, inte från vad som råkar vara lättast att schemalägga.

## Uppgradering är ett ordnat tillståndsskifte

När en ny TaskBoard-version ska införas ändras potentiellt flera saker samtidigt:

```text
frontend-image
backend-image
PostgreSQL-image
databasmigrationer
Compose-konfiguration
runtime-konfiguration
```

Det gör en uppgradering till mer än `docker compose pull` eller `docker compose up`.

Ett rimligt uppgraderingsflöde för en liten självhostad installation kan se ut så här:

```text
1. Läs release-/uppgraderingsinformation
2. Kontrollera aktuell backup
3. Verifiera restore-möjlighet
4. Kontrollera konfigurationsändringar
5. Hämta/bygg den nya versionen
6. Starta den nya stacken kontrollerat
7. Låt Flyway köra avsedda migrationer
8. Kontrollera health/readiness
9. Kör funktionellt smoke test
10. Bevaka loggar och centrala mätvärden
```

I TaskBoard kör Quarkus Flyway vid applikationsstart genom:

```properties
quarkus.flyway.migrate-at-start=true
```

Det gör deploymenten bekväm, men innebär också att en ny backendversion kan ändra databasschemat som en del av uppstarten.

Det är därför backup och migreringsdisciplin hör ihop.

## Databasmigrationer påverkar rollback

Det är frestande att tänka att rollback alltid betyder:

```text
ny image fungerar inte
      |
      v
gå tillbaka till föregående image
```

Det fungerar bara om den föregående applikationsversionen fortfarande är kompatibel med databasschemat efter uppgraderingen.

Om en migration exempelvis har tagit bort en kolumn som den gamla backendversionen kräver räcker det inte att återgå till den gamla containern.

En säkrare migrationsstrategi bygger ofta på kompatibla steg. En förändring kan exempelvis delas upp så här:

```text
version A
  använder old_column

version B
  lägger till new_column
  kan hantera båda

version C
  använder new_column

senare migration
  tar bort old_column
```

Det gör det lättare att återgå mellan närliggande applikationsversioner utan att samtidigt behöva återställa hela databasen.

För TaskBoard finns ännu bara `V1__create_task.sql`, så vi har ingen verklig uppgraderingsmigration att demonstrera. Principen är ändå avgörande för hur framtida V2/V3 bör utformas.

## PostgreSQL-majorversionen är en egen uppgradering

Det är också viktigt att skilja applikationsuppgradering från PostgreSQL-majoruppgradering.

Att ändra image från en PostgreSQL-majorversion till nästa är inte samma typ av förändring som att byta en patchversion. PostgreSQL dokumenterar särskilda metoder för majoruppgradering, exempelvis dump/restore, `pg_upgrade` eller logisk replikering beroende på situation. (PostgreSQL 18, *Upgrading a PostgreSQL Cluster*.)

Det innebär att en framtida ändring från `postgres:18.x` till en senare majorversion ska behandlas som ett explicit databasprojekt, inte som en rutinmässig taggändring i Compose-filen.

Detta blir extra viktigt eftersom TaskBoard använder en persistent volume. En ny containerimage förändrar inte automatiskt datakatalogens format till ett nytt majorformat.

## Graceful shutdown minskar onödiga avbrott

Vid en kontrollerad uppgradering behöver gamla processer avslutas.

Quarkus har stöd för graceful shutdown där HTTP-runtime kan vänta på pågående requests upp till en konfigurerad timeout. Stödet är inte aktiverat genom en timeout i TaskBoards nuvarande `application.properties`. Quarkus har även möjlighet att låta readiness bli false före själva nedstängningen så att omgivande infrastruktur kan sluta skicka ny trafik innan processen avslutas. (Quarkus, *Application Initialization and Termination*.)

För en liten installation med en enda backendinstans kan man fortfarande få ett kort avbrott under uppgradering. Graceful shutdown gör inte systemet högtilgängligt, men det kan minska risken att pågående HTTP-anrop kapas i onödan.

Det illustrerar en återkommande princip:

**graceful shutdown löser en kvalitetsfråga vid stopp; redundans löser tillgänglighet under stopp.**

De är inte samma sak.

## Observability börjar med tre frågor

Begreppet observability används ofta för stora telemetristackar. För en liten tjänst är det mer användbart att börja med de frågor som en operatör faktiskt behöver kunna besvara:

1. **Är tjänsten tillgänglig?**
2. **Vad händer när något går fel?**
3. **Håller resurser eller svarstider på att utvecklas åt fel håll?**

TaskBoard har redan byggstenar för fråga 1 genom healthchecks och för fråga 2 genom containerloggar.

Fråga 3 kräver mer. Exempel på relevanta signaler är:

- CPU- och minnesanvändning,
- diskförbrukning på Docker-värden och PostgreSQL-volume,
- databasanslutningar,
- HTTP-felfrekvens,
- svarstider,
- antal omstarter,
- misslyckade healthchecks,
- backupjobbens status,
- senaste lyckade restore-test.

Referensimplementationen innehåller inte Prometheus, Grafana, OpenTelemetry eller en loggaggregator. Det är avsiktligt. Kapitlets poäng är att definiera behovet innan vi väljer verktyg.

## Larm ska knytas till åtgärd

En mätpunkt som ingen reagerar på är inte ett fungerande larm.

Varje viktigt larm bör kunna kopplas till åtminstone:

```text
signal
  -> sannolik betydelse
  -> första kontroll
  -> möjlig åtgärd
  -> eskalering
```

Ett enkelt exempel:

```text
backend unhealthy
  -> Quarkus är inte ready
  -> kontrollera docker compose ps och backendloggar
  -> kontrollera db-health och datasource-fel
  -> återstart/rollback först när orsaken är förstådd
```

Detta är början till en runbook.

För en liten installation behöver runbooken inte vara ett stort system. Några välskrivna sidor med verifierade kommandon och beslutspunkter kan vara mer värdefulla än avancerad övervakning utan dokumenterade åtgärder.

## Driftkonfiguration bör kunna skiljas från basdefinitionen

Docker beskriver uttryckligen hur en Compose-definition kan kompletteras med en separat produktionsfil som endast innehåller miljöspecifika ändringar, exempelvis portar, miljövariabler, restart-policy eller extra loggtjänster. (Docker Docs, *Use Compose in production*.)

Det passar TaskBoards struktur väl.

Basfilen kan fortsätta vara begriplig och användbar för lokal körning:

```text
docker-compose.yml
```

medan en verklig installation skulle kunna komplettera den:

```text
compose.production.yml
```

med exempelvis:

- restart-policy,
- driftspecifik loggning,
- hårdare nätverksindelning,
- resursgränser där det behövs,
- externa secrets,
- TLS-/ingressintegration,
- produktionsspecifika portar eller labels.

Det viktiga är att inte låta produktionskraven förvandlas till manuella, odokumenterade ändringar direkt på värdmaskinen.

Konfiguration som krävs för drift ska vara versionsbar eller på annat sätt kontrollerad, medan hemligheter och installationsspecifika värden hanteras separat.

## Ett konkret uppgraderingsscenario

Anta att TaskBoard får en ny version där backend innehåller migrationen:

```text
V2__add_task_category.sql
```

och frontend börjar visa kategori.

En disciplinerad driftprocess skulle kunna vara:

```text
Före:
  kontrollera att senaste backupen finns
  gör eller verifiera ett aktuellt restore-test
  läs migrationens kompatibilitet
  dokumentera aktuell version

Under:
  hämta den nya releasen
  starta/recreate tjänster enligt instruktion
  observera Flyway-migrationen i backendloggen
  vänta på healthy-status
  kör funktionellt smoke test

Efter:
  kontrollera fel- och varningsloggar
  verifiera att ny och gammal central data kan läsas
  markera uppgraderingen som godkänd
```

Om den nya backendversionen misslyckas efter att V2 har körts behöver rollbackplanen svara på frågan om föregående backendversion kan arbeta mot V2-schemat.

Om svaret är ja kan application rollback vara enkel.

Om svaret är nej kan återställning av databasen krävas, vilket i sin tur kan innebära att data som skapats efter backupögonblicket går förlorad.

Det visar varför backup, kompatibla migrationer och rollback inte får designas var för sig.

## Vad TaskBoard har – och vad driftmiljön måste komplettera

Efter kapitel 14 och 15 kan vi sammanfatta gränsen tydligt.

Referensimplementationen har redan:

- containeriserad frontend och backend,
- PostgreSQL med persistent named volume,
- healthchecks,
- health-baserad startordning,
- Flyway-migration vid start,
- containerloggar som grundläggande felsökningskälla,
- verifierat full-stack-smoke-test i CI.

Den har ännu inte som incheckad driftlösning:

- definierad restart-policy,
- automatiserad databasbackup,
- schemalagt restore-test,
- definierade RPO/RTO,
- central logghantering,
- metrics/telemetri och larm,
- färdig runbook,
- konfigurerad graceful shutdown-timeout,
- dokumenterad zero-/low-downtime-strategi,
- full produktionshärdning.

Det är inte ett misslyckande i referensimplementationen. Tvärtom gör den avgränsningen tydlig vad själva applikationspaketet ansvarar för och vad en verklig driftsättning måste komplettera.

## Från driftbar till levererbar

När backup, uppgraderingsflöde, hälsokontroller och driftgränser är tydliga återstår nästa fråga:

Hur paketerar vi allt detta så att en annan person eller organisation kan få **en bestämd version** och förstå exakt vilka artefakter, images, konfigurationsfiler och instruktioner som hör ihop?

Det är där kapitel 16 tar vid.

Där flyttar vi perspektivet från driftprocess till **reproducerbar leverans**: versionssättning, image-referenser, checksummor, release notes och ett paket som kan installeras utan tillgång till utvecklarens lokala miljö.
