# Kapitelplan

## Bokprofil
- book_kind: factbook
- book_type: subject_overview

## Inledning
- Syfte: Presentera bokens mål, målgrupp, förkunskaper, referenstjänsten TaskBoard, den valda teknikstacken och hur boken ska användas.
- Status: skriven, första manusversion

## Del 1: Tjänsten och arkitekturen

### Kapitel 1: Från kod till körbar tjänst
- Syfte: Definiera slutmålet: en komplett tjänst som kan byggas, startas och överlämnas reproducerbart.
- Nivå/faktadjup: erfaren utvecklare; översikt med tydliga tekniska gränser.
- Nya huvudbegrepp/faktaområden: tjänst, frontend, backend, persistence, reverse proxy, containerisering, reproducerbar leverans.
- Exempel/case: TaskBoard introduceras som genomgående referenstjänst.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Vad krävs för att gå från två kodbaser till en tjänst någon annan faktiskt kan starta och drifta?
- Centrala fakta: stackens komponenter och deras övergripande ansvar.
- Fördjupning/faktaruta: utvecklingsmiljö kontra körmiljö.
- Käll-/verifieringsbehov: översiktligt; exakta versionsval verifieras senare.

### Kapitel 2: Tjänstens arkitektur
- Syfte: Etablera referensarkitekturen och komponenternas ansvar, gränssnitt och dataflöden.
- Nivå/faktadjup: arkitekturnivå med konkreta teknikval.
- Nya huvudbegrepp/faktaområden: same-origin, `/api`, reverse proxy, intern Docker-nätverkstrafik, databasgräns.
- Exempel/case: Browser/PWA → Nginx → Quarkus → PostgreSQL.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Var ska respektive ansvar ligga för att lösningen ska vara enkel att förstå, köra och överlämna?
- Centrala fakta: Nginx serverar frontend och proxar API; Quarkus äger backendlogik; PostgreSQL är intern persistence.
- Fördjupning/faktaruta: varför PostgreSQL normalt inte exponeras från produktionslik Compose-miljö.
- Käll-/verifieringsbehov: Nginx/Docker networking och Quarkus HTTP-konfiguration.

### Kapitel 3: Projektstruktur och utvecklingsmiljö
- Syfte: Visa hur referensprojektet organiseras och hur utvecklingsflödet skiljer sig från den färdiga körmiljön.
- Nivå/faktadjup: praktisk struktur utan grundläggande språkintroduktion.
- Nya huvudbegrepp/faktaområden: repo-struktur, frontend/backend, miljökonfiguration, Vite dev proxy, Quarkus Dev Services, lokal PostgreSQL/Docker och CI som ren verifieringsmiljö.
- Exempel/case: `code/taskboard/`.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Hur organiserar man projektet så att både utveckling och leverans förblir begripliga?
- Centrala fakta: rekommenderad katalogstruktur och lokalt arbetsflöde.
- Fördjupning/faktaruta: mono-repo som vald referensmodell och alternativens trade-offs.
- Käll-/verifieringsbehov: Vite och Quarkus utvecklingskommandon.

## Del 2: Frontend

### Kapitel 4: PWA som frontendarkitektur
- Syfte: Förklara vad PWA-egenskaper tillför och hur de påverkar deployment och caching.
- Nivå/faktadjup: arkitektur och praktisk setup, inte webbutvecklingsgrundkurs.
- Nya huvudbegrepp/faktaområden: web app manifest, service worker, installation, cache, uppdateringar, offline-strategi.
- Exempel/case: TaskBoard installeras som PWA och får en medvetet begränsad offline-modell.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: När blir en React-app en PWA, och vilka driftkonsekvenser följer med det?
- Centrala fakta: manifest, service worker, HTTPS-krav i riktiga miljöer, cachekontroll.
- Fördjupning/faktaruta: varför service worker och `index.html` kräver genomtänkta cache headers.
- Käll-/verifieringsbehov: MDN/webbstandarder och vald PWA-plugin/tooling.

### Kapitel 5: Frontend med React och TypeScript
- Syfte: Visa frontendens interna struktur och dess kontrakt mot API:t.
- Nivå/faktadjup: erfaren React/TypeScript-läsare.
- Nya huvudbegrepp/faktaområden: komponentkomposition, API-lager, state, formulär, felhantering, transporttyper och expansionspunkter för routing.
- Exempel/case: TaskBoards sammanhållna lista, skapande, statusändring och radering.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Hur håller vi frontendens struktur ren när backend och PWA-beteende växer fram?
- Centrala fakta: tydligt API-lager, separering mellan UI och transportmodell, konsekvent felhantering.
- Fördjupning/faktaruta: frontendens API-bas i utveckling kontra via Nginx i körmiljö.
- Käll-/verifieringsbehov: React/Vite officiell dokumentation där syntax eller rekommendation är versionsberoende.

## Del 3: Backend och data

### Kapitel 6: Backend med Quarkus
- Syfte: Sätta upp Quarkus och etablera REST-API:t utan att göra boken till en Quarkus-kurs.
- Nivå/faktadjup: praktisk introduktion för erfaren Java-utvecklare.
- Nya huvudbegrepp/faktaområden: Quarkus-projekt, extensions, CDI, REST-resurser, konfiguration, dev mode.
- Exempel/case: `/api/tasks`.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Vad behöver en erfaren Java-utvecklare faktiskt känna till för att bli produktiv i Quarkus?
- Centrala fakta: projektsetup, relevanta extensions, REST- och konfigurationsmodell.
- Fördjupning/faktaruta: Quarkus dev mode och skillnaden mot paketerad körning.
- Käll-/verifieringsbehov: Quarkus officiell dokumentation och aktuella extension-namn.

### Kapitel 7: Persistens med JPA
- Syfte: Placera JPA i Quarkus-lösningen och beskriva persistence- och transaktionsgränser.
- Nivå/faktadjup: JPA antas känt.
- Nya huvudbegrepp/faktaområden: entiteter, persistence-lager, transaktioner, Quarkus/Hibernate ORM-integration.
- Exempel/case: `TaskEntity`, `TaskRepository`, `EntityManager`, JPQL, dirty checking och `@Version`.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Hur använder vi känd JPA-teknik utan att låta ORM styra hela applikationsarkitekturen?
- Centrala fakta: mapping, repositories/persistence access, transaktionsgränser, schemahantering separerad från JPA.
- Fördjupning/faktaruta: varför Flyway, inte automatisk schemaevolution, äger produktionsschemat.
- Käll-/verifieringsbehov: Quarkus Hibernate ORM/JPA-konfiguration.

### Kapitel 8: PostgreSQL som databas
- Syfte: Ge den praktiska PostgreSQL-kunskap som behövs för referenstjänsten.
- Nivå/faktadjup: setup och relevanta egenskaper, inte generell SQL-kurs.
- Nya huvudbegrepp/faktaområden: databas, användare, JDBC-anslutning, datatyper, constraints, index, healthcheck och persistenta volumes.
- Exempel/case: TaskBoards faktiska `task_item`-schema och Compose-databas.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Vad behöver applikationsutvecklaren förstå om PostgreSQL för att tjänsten ska bli robust och portabel?
- Centrala fakta: anslutningsdata, datatyper, indexering på relevant nivå, containeriserad databas.
- Fördjupning/faktaruta: databasdata är inte samma sak som containerlivscykel.
- Käll-/verifieringsbehov: PostgreSQL officiell dokumentation och Docker Official Image.

### Kapitel 9: Databasschemat som kod med Flyway
- Syfte: Göra schemaevolution reproducerbar och versionshanterad.
- Nivå/faktadjup: praktisk migrationsstrategi.
- Nya huvudbegrepp/faktaområden: migrationer, versionsordning, baseline/repair-koncept vid behov, kompatibla uppgraderingar.
- Exempel/case: faktisk `V1__create_task.sql` samt tydligt markerade hypotetiska V2/V3-exempel för framtida schemaevolution.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Hur ser vi till att en ny release kan uppgradera en befintlig databas i stället för att skapa om den?
- Centrala fakta: migrationsfiler som kod, körordning, kopplingen till applikationsrelease.
- Fördjupning/faktaruta: JPA-modell och databasschema måste utvecklas i samordning.
- Käll-/verifieringsbehov: Flyway officiell dokumentation och Quarkus integration.

## Del 4: Den sammanhängande applikationen

### Kapitel 10: Från frontend till databas och tillbaka
- Syfte: Följa ett komplett användningsfall genom hela stacken.
- Nivå/faktadjup: integrationsfokus.
- Nya huvudbegrepp/faktaområden: DTO, JSON, HTTP-status, validering, tjänstelager, transaktion, felrespons.
- Exempel/case: markera en TaskBoard-uppgift som klar.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Vad händer egentligen i varje lager när användaren klickar på "Klar"?
- Centrala fakta: request/response-kedjan och ansvar i varje komponent.
- Fördjupning/faktaruta: kontrakt och felhantering över lagringsgränser.
- Käll-/verifieringsbehov: Quarkus REST/Jakarta validation där syntax är versionsberoende.

### Kapitel 11: Konfiguration och säkerhet
- Syfte: Visa hur samma artifact kan konfigureras för olika miljöer och hur exponeringsytan hålls begränsad.
- Nivå/faktadjup: arkitektur och praktisk konfiguration.
- Nya huvudbegrepp/faktaområden: environment variables, secrets, same-origin, CORS, proxy headers, TLS-principer, autentisering/auktorisering på översiktsnivå.
- Exempel/case: Nginx som enda exponerade entry point; Quarkus och PostgreSQL på internt nätverk.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Hur undviker vi att bygga in miljöspecifika adresser och credentials i våra images?
- Centrala fakta: runtime-konfiguration, secrets, origin-modell och nätverksgränser.
- Fördjupning/faktaruta: varför reverse proxy förenklar frontend/backend-kommunikation men inte ersätter autentisering.
- Käll-/verifieringsbehov: Nginx, Docker och Quarkus säkerhets-/proxykonfiguration.

## Del 5: Kvalitet och paketering

### Kapitel 12: Testning av den kompletta tjänsten
- Syfte: Ge en rimlig teststrategi över frontend, backend, persistence och integration.
- Nivå/faktadjup: principer och representativa körbara exempel.
- Nya huvudbegrepp/faktaområden: statisk verifiering, unit, component, API, integration, testdatabas, Dev Services, healthchecks och full-stack smoke test.
- Exempel/case: TaskBoards faktiska GitHub Actions-workflow, create/read-smoke-testet och en rekommenderad CRUD-utbyggnad.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Vilka fel kan respektive testnivå hitta, och vilka tester bör få använda en riktig PostgreSQL-instans?
- Centrala fakta: testpyramid/-portfölj, isolering, databasmigrationer i test.
- Fördjupning/faktaruta: testmiljön ska likna produktionsförutsättningarna där det faktiskt spelar roll.
- Käll-/verifieringsbehov: Quarkus testing, React/Vite testverktyg och eventuell containerbaserad testlösning.

### Kapitel 13: Frontend, reverse proxy och backend som Docker-images
- Syfte: Containerisera frontend/Nginx och Quarkus på ett reproducerbart sätt.
- Nivå/faktadjup: praktiska Dockerfiles och image-principer.
- Nya huvudbegrepp/faktaområden: multi-stage build, statiska assets, Nginx image, Quarkus fast-jar, immutable artifacts, healthcheck och runtime config.
- Exempel/case: TaskBoards faktiska frontend- och backend-Dockerfiles som byggs och startas i GitHub Actions.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Hur gör vi images små, begripliga och oberoende av utvecklingsmaskinen?
- Centrala fakta: build stage kontra runtime stage och image-ansvar.
- Fördjupning/faktaruta: varför Vite dev server inte är produktionsserver.
- Käll-/verifieringsbehov: Docker, Nginx och Quarkus container-build-dokumentation.

### Kapitel 14: Den kompletta tjänsten med Docker Compose
- Syfte: Koppla samman de tre runtime-delarna till en portabel installation.
- Nivå/faktadjup: komplett men liten Compose-lösning.
- Nya huvudbegrepp/faktaområden: services, default network/service discovery, volumes, health checks, `depends_on`/readiness, miljövariabler och publicerade portar.
- Exempel/case: `docker compose up --build` startar TaskBoard; CI använder `docker compose up -d --wait --wait-timeout 120` före smoke-test.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Vad krävs för att mottagaren ska kunna starta hela tjänsten med ett fåtal kommandon?
- Centrala fakta: Nginx som enda publicerad service, backend/databas internt på Compose-standardnätet, persistent PostgreSQL-volume och health-baserad startkedja db → backend → web.
- Fördjupning/faktaruta: vanlig startordning är inte samma sak som readiness; `service_healthy` kopplar dependency till healthcheck.
- Käll-/verifieringsbehov: verifierat 2026-08-17 mot Docker Compose officiella dokumentation och faktisk CI-körning.

## Del 6: Drift och leverans

### Kapitel 15: Från lokal körning till driftbar tjänst
- Syfte: Förklara vad som måste läggas till för att lösningen ska vara hanterbar över tid.
- Nivå/faktadjup: driftprinciper för utvecklare.
- Nya huvudbegrepp/faktaområden: health/readiness, restart-policy, loggning/rotation, backup/restore, RPO/RTO, graceful shutdown, persistent data, migrations vid upgrade, rollback, observability och runbook.
- Exempel/case: TaskBoard uppgraderas utan att tappa PostgreSQL-data och med en explicit rollback-/restore-plan.
- Status: skriven
- Kärnfråga/nyfikenhetskrok: Vad skiljer "det startar" från "det går att förvalta"?
- Centrala fakta: hälsokontroller, loggar, backup och restore, uppgraderingsflöde, migrationskompatibilitet och driftkonfiguration.
- Fördjupning/faktaruta: backup är en process; en verifierad restore är beviset.
- Käll-/verifieringsbehov: verifierat 2026-08-17 mot PostgreSQL 18 backup/restore/upgrade, Quarkus lifecycle/graceful shutdown samt Docker restart-, logging- och production Compose-dokumentation.

### Kapitel 16: En reproducerbar leverans
- Syfte: Definiera vad som ska överlämnas för att en annan organisation ska kunna köra och uppgradera tjänsten.
- Nivå/faktadjup: leverans- och releaseperspektiv.
- Nya huvudbegrepp/faktaområden: release-tag/commit, lockfil och `npm ci`, Maven-reproducerbarhet, image-tag/digest, Compose som releaseartefakt, checksums, Actions-pinning, release notes, installations-/uppgraderingsinstruktion och release-manifest.
- Exempel/case: TaskBoard 1.x levereras som ett sammanhållet paket där Git-version, images, digests, migrationsnivå och deploymentdefinition kan kopplas ihop.
- Status: skriven, första manusversion
- Kärnfråga/nyfikenhetskrok: Kan mottagaren förstå exakt vad som ska köras utan tillgång till vår utvecklingsmiljö?
- Centrala fakta: skillnaden mellan återskapningsbar leverans, deterministisk dependency resolution och bitreproducerbar build; artefakter, versionskoppling och proveniens.
- Fördjupning/faktaruta: konfiguration ska vara data, inte en ny specialbyggd image per mottagare; digest-låsning kräver aktiv uppdateringsprocess för säkerhetsfixar.
- Käll-/verifieringsbehov: verifierat 2026-08-17 mot Docker tag/digest-dokumentation, npm lockfile/`npm ci`, Maven reproducible builds och GitHub Actions säker pinning.

### Kapitel 17: Arkitekturen i backspegeln
- Syfte: Sammanfatta referensarkitekturens styrkor, begränsningar och naturliga utvecklingsvägar.
- Nivå/faktadjup: arkitekturell reflektion.
- Nya huvudbegrepp/faktaområden: trade-offs, skalning, extern identitet, TLS-terminering, orkestrering, plattformstjänster.
- Exempel/case: När TaskBoard växer bortom den lilla självhostade Compose-installationen.
- Status: planerad
- Kärnfråga/nyfikenhetskrok: Vilka delar av lösningen är stabila principer och vilka är medvetet enkla val för den här typen av tjänst?
- Centrala fakta: lösningens avgränsningar och möjliga nästa steg.
- Fördjupning/faktaruta: när Docker Compose inte längre är rätt driftsmodell.
- Käll-/verifieringsbehov: huvudsakligen syntes av tidigare verifierat material; nya jämförelser verifieras vid skrivning.

## Källförteckning
- En exporterad källförteckning ligger efter kapitel 17.
- Kapitel ska använda synliga hänvisningar när ett påstående eller en rekommendation behöver stöd.
- Källförteckningen ska i första hand bygga på officiell dokumentation och andra primärkällor.

## Helhetskontroll – faktabok
- Ämnestäckning: hela kedjan från frontendarkitektur till databas, containerisering, drift och överlämning täcks.
- Logisk ordning: först helhet, därefter frontend, backend/data, integration, kvalitet/containerisering och slutligen drift/leverans.
- Balans bredd/djup: djupast fokus på integrationspunkter och leverans; mindre djup i redan kända språk/ramverksgrunder.
- Upprepningar/luckor: Nginx, konfiguration och Docker återkommer med olika perspektiv; varje kapitel ska undvika att återförklara grundprinciper som redan etablerats.
- Kapitel med extra faktakontroll: 4, 6, 8, 9, 11–16 på grund av versions- och konfigurationsberoende fakta.
