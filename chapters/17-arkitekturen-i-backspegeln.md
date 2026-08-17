# 17. Arkitekturen i backspegeln

Vi började med en till synes enkel fråga: hur går man från kod till en tjänst som faktiskt går att bygga, starta, testa, överlämna och drifta?

Efter sexton kapitel har TaskBoard fått en komplett teknisk kedja:

```text
Browser
   |
   v
Nginx
   |
   v
Quarkus
   |
   v
PostgreSQL
```

Runt den kedjan finns lika viktiga delar: TypeScript-typer, REST-kontrakt, JPA, Flyway, healthchecks, Docker-images, Compose, CI och en leveransmodell. Ingen av delarna är särskilt exotisk. Det intressanta är hur de tillsammans bildar en tjänst vars beteende går att resonera om från användarens klick till den rad som lagras i databasen.

Det sista kapitlet handlar därför inte om ännu ett verktyg. Det handlar om att se tillbaka på arkitekturen och skilja mellan tre saker:

- principer som bör överleva även om teknikstacken byts,
- förenklingar som passar TaskBoards storlek,
- och gränser där lösningen behöver utvecklas när kraven förändras.

## Den viktigaste arkitekturvinsten är tydliga ansvar

TaskBoard är liten nog för att kunna byggas som en enda applikation. Ändå är den uppdelad i tydliga tekniska ansvar:

- React ansvarar för användargränssnitt och klientstate,
- Nginx är den publika HTTP-ingången i den produktionslika miljön,
- Quarkus äger API och applikationslogik,
- JPA/Hibernate översätter mellan objektmodell och relationsdatabas,
- Flyway äger schemaevolutionen,
- PostgreSQL är persistent datalager,
- Docker-images paketerar runtime-komponenterna,
- Compose beskriver hur de körs tillsammans,
- GitHub Actions verifierar att kedjan faktiskt fungerar.

Den här ansvarsfördelningen är mer långlivad än de exakta produkterna.

Produkterna är däremot utbytbara. Den publika HTTP-gränsen kan implementeras av något annat än Nginx, applikationslagret av något annat än Quarkus och körmodellen av något större än Compose. Det långlivade är i stället kraven på en tydlig publik gräns, ett definierat API, en kontrollerad persistensmodell, versionsstyrda schemaändringar och en verifierad leverans.

Det är därför mer värdefullt att förstå **varför gränserna finns** än att memorera varje konfigurationsnyckel.

## En liten domän gjorde infrastrukturen synlig

TaskBoard har medvetet liten domänkomplexitet. En uppgift har titel, beskrivning, status, prioritet och några metadatafält. Vi har inte lagt till användare, team, roller, etiketter, kommentarer, bilagor eller notifieringar bara för att göra applikationen mer realistisk.

Det beslutet har varit viktigt.

Om domänen hade varit större skulle mycket av boken ha handlat om verksamhetsregler. Nu har vi i stället kunnat följa samma objekt genom hela kedjan:

```text
React-formulär
   -> JSON
   -> REST-resurs
   -> tjänstelager
   -> JPA-entitet
   -> SQL-rad
   -> JSON
   -> React-state
```

Det har också gjort integrationsfel tydliga. När smoke-testet skickade prioriteten `MEDIUM` medan backendkontraktet accepterade `LOW`, `NORMAL` och `HIGH` var varje enskild komponent byggbar. Felet fanns i övergången mellan dem.

Det är en av bokens viktigaste lärdomar:

> En tjänsts arkitektur består inte bara av komponenter. Den består lika mycket av kontrakten mellan komponenterna.

## Same-origin var ett litet val med stor effekt

I den färdiga körmodellen går webbläsaren till en enda publik origin. Nginx serverar frontendens statiska filer och proxar `/api` vidare till Quarkus.

Det gav flera egenskaper samtidigt:

- frontend behöver inte känna till backendens interna hostname,
- normalflödet behöver ingen separat CORS-konfiguration,
- backend behöver inte publiceras direkt till värdmaskinen,
- deploy-konfigurationen blir enklare för klienten,
- samma relativa `/api` kan användas som tydlig applikationsgräns.

Det här är ett exempel på ett arkitekturval som är stabilt även om Nginx i framtiden försvinner. På en molnplattform kan motsvarande gräns implementeras av en ingress, load balancer, gateway eller managed reverse proxy.

Principen är fortfarande densamma: klienten behöver en stabil publik adress, medan interna tjänsteadresser ska kunna förändras utan att frontend behöver byggas om.

## Ett REST-API är inte bara URL:er

TaskBoards API är avsiktligt enkelt, men arbetet med det visar varför API-kontrakt kräver disciplin.

Kontraktet omfattar bland annat:

- vilka endpoints som finns,
- vilka HTTP-metoder de använder,
- vilka fält som skickas,
- vilka enumvärden som är giltiga,
- vilka valideringsregler som gäller,
- vilka statuskoder som används,
- och hur fel representeras.

TypeScript hjälper frontendutvecklaren vid kompilering. Bean Validation hjälper backend vid requestgränsen. JPA och databasen har ytterligare regler. Men inget av dessa lager kan ensamt garantera att hela systemet använder samma kontrakt.

Därför blev full-stack-testet en arkitekturkomponent i praktiken. Det verifierar inte bara kod; det verifierar att gränserna fortfarande stämmer överens.

## Databasen är inte en implementationdetalj

Det är lätt att beskriva PostgreSQL som något som ligger "under" applikationen. Men i en långlivad tjänst är databasen en av de mest beständiga delarna.

Applikationscontainrar kan byggas om på minuter. Databasinnehållet måste överleva releaser, omstarter och ofta flera generationer av applikationskod.

Det är därför TaskBoard skiljer på:

```text
JPA-modell        -> hur Java arbetar med data
Flyway-migration  -> hur schemat förändras över tid
PostgreSQL        -> hur data faktiskt lagras och skyddas
```

Den gränsen är viktigare än valet mellan repository-mönster, Panache eller direkt `EntityManager`.

När tjänsten växer blir databasen dessutom en driftsfråga: backup, restore, kapacitet, index, majoruppgraderingar, åtkomstkontroll och recovery-mål. En named Docker-volume löser persistens över containeromstarter, men den ersätter inte någon av dessa förvaltningsfrågor.

## Compose är rätt för problemet vi faktiskt har

TaskBoard använder Docker Compose som huvudmodell för den kompletta tjänsten. Det är ett rimligt val för bokens mål:

- tre runtime-komponenter,
- en värd eller liten självhostad miljö,
- tydliga beroenden,
- en persistent databas,
- och behov av att kunna starta samma stack lokalt och i CI.

Compose gör arkitekturen läsbar i en fil. Vi kan se builds, miljövariabler, volymer, portar, healthchecks och startberoenden utan att införa en separat plattformsmodell.

Men Compose är inte en universell slutpunkt.

Om TaskBoard skulle behöva flera instanser av backend, automatisk failover mellan noder, avancerad trafikstyrning, självservice för många team eller policybaserad hantering av hundratals tjänster kan en annan driftsplattform bli motiverad.

Det viktiga är **varför** man byter.

Att ersätta Compose med Kubernetes för att tjänsten har "blivit seriös" är inget arkitekturargument. Ett relevant skäl är däremot att kraven på skalning, tillgänglighet, schemaläggning, policy eller plattformsautomation har vuxit bortom vad den nuvarande modellen hanterar rimligt.

## När ska tjänsten skalas horisontellt?

TaskBoards backend är i grunden väl lämpad att köras i fler än en instans eftersom den persistenta domändatan ligger i PostgreSQL och inte i containerns lokala filsystem.

Men "starta två backendcontainrar" är inte hela skalningslösningen.

En verklig horisontell skalning kräver bland annat svar på frågor som:

- Hur fördelas trafiken mellan instanser?
- Hur dimensioneras databasens connection pool?
- Finns någon lokal state som måste elimineras eller externaliseras?
- Hur hanteras bakgrundsjobb om sådana införs?
- Hur görs rolling upgrades med flera appversioner mot samma schema?
- Hur observeras kapacitet och fel per instans?

Det är ännu ett exempel på att arkitektur följer krav. För TaskBoard som referenstjänst skulle extra instanser främst öka komplexiteten. För en publik tjänst med verklig last kan samma egenskap bli central.

## Autentisering är den tydligaste sak som saknas

Referensimplementationen har ingen autentisering eller auktorisering. Det är medvetet: användaridentitet skulle ha introducerat ett helt eget område och skymt bokens huvudkedja.

Men om TaskBoard ska exponeras för verkliga användare är detta inte en valfri kosmetisk förbättring.

En större lösning behöver ta ställning till åtminstone:

- vem som autentiserar användaren,
- hur identiteten når backend,
- hur sessioner eller tokens valideras,
- vilka operationer olika användare får göra,
- hur objektnivåbehörighet hanteras,
- och hur säkerhetsrelaterade händelser loggas.

Det betyder inte automatiskt att TaskBoard ska bygga en egen identitetsserver. Tvärtom är extern identitet ofta ett område där en etablerad identity provider eller plattformstjänst minskar den egna säkerhetsytan.

Arkitekturgränsen bör då vara tydlig: autentisering kan delegeras, men backend måste fortfarande fatta auktoriseringsbeslut för den data och de operationer den äger.

## TLS hör till den publika kanten

Nginx är publik ingång i referensstacken, men TLS-terminering ingår inte i den lokala Compose-modellen.

För lokal utveckling och CI över loopback är det rimligt. För internetexponering är det inte en färdig säkerhetsmodell.

I en verklig miljö kan TLS termineras på flera ställen:

```text
Internet
   |
   v
managed load balancer / ingress / reverse proxy
   |
   v
TaskBoard
```

eller direkt i en edge-proxy som drivs tillsammans med tjänsten.

Vilken lösning som väljs är mindre viktig än att gränsen är explicit. När proxykedjor introduceras måste även forwarded headers och vilka proxies som får vara betrodda konfigureras medvetet. Det var därför kapitel 11 skilde mellan att Nginx **skickar** `X-Forwarded-*` och att Quarkus faktiskt **litar på** uppgifterna.

## Observability blir viktigare när utvecklaren inte står bredvid

Healthchecks var tillräckliga för att Compose och CI skulle kunna avgöra om TaskBoards komponenter var redo att användas. Men driftbarhet kräver mer än en grön health-status.

När tjänsten får verkliga användare behöver den kunna svara på frågor som:

- Hur många requests misslyckas?
- Har svarstiderna förändrats?
- Är databasen flaskhalsen?
- Fylls connection poolen?
- Har en release orsakat fler 5xx-fel?
- Är lagringsutrymmet på väg att ta slut?

Där börjar metrics, strukturerade loggar, tracing och larm bli arkitekturfrågor snarare än driftdekoration.

Det är ändå klokt att lägga till dem från observerade behov. TaskBoards lilla referensimplementation vinner på att de inte göms bakom ett stort observability-ramverk innan det finns något att observera.

## PWA:n visar samma princip på klientsidan

TaskBoard är installerbar som PWA, men den är inte en offline-first-applikation. Service workern kan precacha det statiska appskalet, medan API-data fortfarande kräver anslutning till backend.

Det är en avsiktlig avgränsning.

Full offline-redigering skulle kräva helt nya arkitekturfrågor:

- lokal persistent kö för ändringar,
- konflikthantering,
- synkroniseringsprotokoll,
- versions- eller concurrency-kontrakt,
- hantering av borttagna objekt,
- och användarfeedback när lokal och serverbaserad state skiljer sig.

Det är alltså inte en "PWA-inställning" som saknas. Det är ett annat systembeteende.

Det är en nyttig tumregel för många arkitekturdiskussioner: om en till synes liten feature kräver nya konsistensregler är det sannolikt en arkitekturförändring, inte bara en UI-förbättring.

## Vad skulle vi behålla om vi började om?

Om TaskBoard skulle byggas om i morgon, men med samma krav, finns mycket som bör överleva:

1. **En publik HTTP-ingång.** Frontend och API bör presenteras bakom en stabil origin.
2. **Ett explicit API-kontrakt.** Klient och backend ska inte behöva gissa varandras modeller.
3. **Separat schemaägarskap.** Flyway-liknande migrationer bör fortsatt styra schemaevolutionen.
4. **Extern persistent data.** Applikationscontainrar ska kunna ersättas utan att domändata följer med dem.
5. **Bygg- och runtime-separation.** Kompilatorer och byggverktyg behöver inte finnas i produktionsimagen.
6. **Health/readiness som maskinläsbart kontrakt.** Orkestrering och CI ska kunna avgöra när komponenter är redo.
7. **Full-stack-verifiering.** Minst ett test ska gå genom samma publika väg som den verkliga klienten.
8. **Konfiguration utanför imagen.** Samma byggda artefakt ska kunna användas i flera miljöer.
9. **Versionsstyrd leverans.** Kod, migrationer, images och releaseinformation ska kunna kopplas till samma version.

Däremot skulle följande val kunna ändras utan att arkitekturen förlorar sin kärna:

- React mot ett annat frontendramverk,
- Nginx mot en plattformsgateway,
- Quarkus mot ett annat backendramverk,
- JPA mot en annan persistensmekanism,
- Compose mot en annan orkestreringsmodell.

Det är skillnaden mellan **arkitekturprincip** och **teknikval**.

## Vad bör förbättras innan en verklig release?

Tidigare kapitel har medvetet lämnat några hårdningssteg öppna. Test- och leveranshärdningen är nu genomförd på den nivå boken behöver: backend/API-testning mot PostgreSQL Dev Services, frontendkomponenttester, `package-lock.json`/`npm ci`, full-SHA-pinnade TaskBoard-Actions, en separat releasekedja, publicerade release-images, registry-digests och maskinläsbart release-manifest finns i referensimplementationen.

De mest värdefulla nästa stegen ligger därför i verkliga produktionskrav:

```text
1. Behåll frontend-, backend- och full-stack-testerna som regressionstest och bygg ut dem när nya beteenden tillkommer.
2. Lägg till autentisering och auktorisering innan publik användning.
3. Definiera TLS-terminering och en genomtänkt trusted-proxy-policy.
4. Flytta känsliga värden till en lämplig secrets-lösning.
5. Etablera backup/restore-test, central loggning, metrics och larm.
6. Lägg till attestering/signering, SBOM eller annan supply-chain-härdning om risk- och regelkraven motiverar det.
```

Ordningen kan ändras beroende på mål. Om nästa steg bara är fortsatt bokutveckling är test- och reproducerbarhetshärdning mest relevant. Om tjänsten i stället ska publiceras till verkliga användare flyttar identitet, TLS, secrets och driftrutiner snabbt upp i prioritet.

Det centrala är att inte blanda ihop dessa två mål.

## Arkitektur är en serie verifierbara beslut

Det är lockande att tänka på arkitektur som en bild man ritar innan utvecklingen börjar. TaskBoard visar en annan modell.

Arkitekturen började som en enkel skiss:

```text
Browser -> Nginx -> Quarkus -> PostgreSQL
```

Sedan blev varje pil ett konkret kontrakt:

- `/api` fick en faktisk proxyregel,
- backend fick health/readiness,
- JPA fick ett verkligt schema,
- schemaevolution fick Flyway,
- databasen fick persistent volume,
- tjänsterna fick health-baserad startordning,
- CI fick ett smoke-test genom hela kedjan,
- leveransen fick tydligare versions- och reproducerbarhetskrav.

Och flera av de viktigaste förbättringarna kom inte från diagrammet utan från verkliga fel. PostgreSQL 18:s volume-layout behövde korrigeras. Nginx-healthchecken behövde en explicit IPv4-loopback. Smoke-testet avslöjade ett felaktigt enumvärde.

Det är inte misslyckanden i arkitekturarbetet. Det är själva arkitekturarbetet när det är kopplat till körbar kod.

En arkitektur som aldrig byggs och testas är fortfarande en hypotes.

## En beslutsordning att bära med sig

När en ny tjänst ska byggas är det lätt att börja med produktnamn. En mer robust ordning är att börja med gränserna och först därefter välja verktyg:

1. **Vilket beteende är publikt?** Definiera klientens kontrakt och den yttre ingången.
2. **Vilken data måste överleva?** Bestäm ägarskap, schema, migrationer och återställning.
3. **Vilka delar måste kunna bytas oberoende?** Låt dessa gränser styra bygg- och körningsartefakter.
4. **Hur vet vi att helheten fungerar?** Lägg verifiering på både komponent- och systemgränser.
5. **Hur identifierar och överlämnar vi en version?** Knyt källa, images, konfiguration, migrationer och instruktioner till samma release.

Den ordningen gör inte teknikvalen oviktiga. Den gör dem möjliga att utvärdera mot ett konkret ansvar i stället för mot en generell uppfattning om vad som är modernt.

## Från kod till körbar tjänst

Bokens titel handlar om en förflyttning.

I början hade vi källkod och ett antal teknikval. I slutet har vi en modell för hela tjänstens livscykel:

```text
källkod
   |
   v
build
   |
   v
test
   |
   v
images
   |
   v
Compose / driftplattform
   |
   v
körande tjänst
   |
   v
loggar, backup, uppgradering och nästa release
```

Den viktigaste slutsatsen är därför inte att React, Quarkus, PostgreSQL och Docker Compose är den rätta stacken för alla system.

Slutsatsen är att en tjänst blir begriplig och överlämningsbar när varje steg från kod till drift har ett tydligt ansvar, ett explicit kontrakt och en verifierbar väg till nästa steg.

Det är då arkitekturen slutar vara en bild och blir en egenskap hos den körande tjänsten.
