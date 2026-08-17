# 16. En reproducerbar leverans

Vi har nu en tjänst som kan byggas, testas, startas och förvaltas. Men en sista fråga återstår innan TaskBoard verkligen kan lämnas över till någon annan:

> Kan mottagaren i efterhand förstå exakt vilken version som kördes, vilka bygginstruktioner som användes och vilka artefakter som hörde ihop?

Det är kärnan i en reproducerbar leverans.

Begreppet kan betyda olika saker. I strikt mening är en reproducerbar build en byggprocess där samma källkod, byggmiljö och instruktioner ger bit-för-bit-identiska artefakter. Maven använder just den definitionen i sin dokumentation om reproducible builds. (Apache Maven, *Configuring for Reproducible Builds*.)

I praktisk tjänsteleverans behöver vi dessutom ett bredare perspektiv. En driftorganisation måste kunna svara på frågor som:

- Vilken Git-version byggdes?
- Vilka frontend- och backendberoenden användes?
- Vilka Docker-images avsågs?
- Vilken Compose-fil hörde till releasen?
- Vilken konfiguration måste mottagaren själv sätta?
- Vilka databasändringar följer med?
- Hur kontrolleras att nedladdade filer inte har förändrats?
- Hur uppgraderas tjänsten från föregående version?

Det här kapitlet handlar om den kedjan från **källa** till **identifierbar leverans**.

## Reproducerbarhet har flera nivåer

Det är användbart att skilja på tre nivåer.

### 1. Återskapningsbar leverans

En annan person kan checka ut rätt källkod, följa instruktionerna och bygga en fungerande tjänst med samma avsedda komponentversioner.

### 2. Deterministisk dependency resolution

Byggverktygen installerar samma beroendeträd varje gång. Ett exempel är en incheckad `package-lock.json` tillsammans med `npm ci`.

### 3. Bitreproducerbar artefakt

Två oberoende byggen av samma källkod ger exakt samma binära resultat och därmed samma checksumma.

De tre nivåerna hänger ihop men är inte samma sak.

TaskBoard ligger i nuläget närmast nivå 1, men inte fullt ut. Referensimplementationen har explicit valda huvudversioner, en verifierad byggkedja och en definierad Compose-struktur. Samtidigt finns flera öppningar där externa beroenden kan förändras mellan två byggtillfällen.

Det är därför viktigt att inte säga "reproducerbar" bara för att projektet råkar bygga två gånger i rad.

## Releaseversionen ska börja i Git

En leverans behöver en entydig identitet.

För ett Git-baserat projekt är den naturliga grunden en release-tag, exempelvis:

```text
v1.2.0
```

Taggen pekar på en specifik commit. Därmed kan vi koppla ihop:

```text
release v1.2.0
       |
       v
Git-commit
       |
       +-- källkod
       +-- Dockerfiles
       +-- docker-compose.yml
       +-- Flyway-migrationer
       +-- README / driftinstruktioner
       +-- CI-workflows
```

Versionsnumret ska alltså inte finnas som en fristående sanningskälla som människor måste hålla synkron manuellt på flera ställen om det kan undvikas.

TaskBoards `package.json` och `pom.xml` innehåller i dag båda versionen `0.1.0`. De fungerar som projektmetadata, men en framtida leveranspolicy bör definiera vilken källa som är kanonisk när en release faktiskt skapas. För en distribuerad tjänst är Git-taggen ett starkt val eftersom den samtidigt identifierar hela repositoryt: frontend, backend, databas och leveransfiler.

Det betyder inte att interna paketversioner är oviktiga. Det betyder att releaseprocessen bör härleda eller kontrollera dem mot den version som faktiskt publiceras.

## Samma `package.json` betyder inte automatiskt samma frontendberoenden

TaskBoards frontend anger flera exakta huvudberoenden:

```json
{
  "react": "19.2.7",
  "react-dom": "19.2.7",
  "typescript": "6.0.3",
  "vite": "8.2.1"
}
```

Det ser strikt ut, men alla beroenden är inte låsta på samma sätt. Exempelvis används versionsintervall för typerna:

```json
"@types/react": "^19.0.0"
```

Dessutom har även de explicit angivna paketen transitiva beroenden.

TaskBoard har nu en incheckad `package-lock.json`. Både Dockerfile och CI använder därför en fryst installation:

```bash
npm ci
```

npm beskriver `package-lock.json` som representationen av det exakta dependency tree som installerades och avsett att checkas in i källkodsförrådet. `npm ci` kräver en lockfil och gör en fryst installation: om `package.json` och lockfilen inte stämmer överens avbryts installationen i stället för att lockfilen uppdateras. (npm Docs, *package-lock.json*; *npm ci*.)

Den införda kedjan kan beskrivas så här:

```text
package.json
     +
package-lock.json
     |
     v
npm ci
```

Det gör inte hela Docker-imagen bitreproducerbar, men det eliminerar en stor källa till dependency drift.

I referensimplementationen är detta nu ett verifierat kodsteg: lockfilen genererades av npm i GitHub Actions, checkades in och används av både CI och frontendens Docker-build.

## Maven låser mycket – men inte allt av sig självt

Backend använder Maven och Quarkus BOM. Det ger en tydlig och kontrollerad modell för Java- och Quarkusberoenden. Java-versionen är satt till 21 och Quarkus-plattformen till 3.33.3.1.

Men också här måste man skilja mellan "versionsstyrd" och "bitreproducerbar".

Maven beskriver reproducerbara builds som ett särskilt mål. För Maven 3-baserade byggen behöver plugins och output konfigureras för reproducerbart resultat, bland annat genom `project.build.outputTimestamp` och reproducerbara pluginversioner. Maven påpekar också att samma majorversion av JDK och samma byggmiljö spelar roll. (Apache Maven, *Configuring for Reproducible Builds*.)

TaskBoard har inte gjort den här hårdningen ännu.

Det betyder att följande påstående är rimligt:

> TaskBoard har en kontrollerad Maven-build med explicit Quarkus- och Java-version.

Men detta vore för starkt:

> TaskBoards backend-JAR är redan verifierat bitreproducerbar.

Om bitreproducerbarhet blir ett leveranskrav ska den testas explicit, exempelvis genom två oberoende builds och artefaktjämförelse.

## Docker-taggar är praktiska men föränderliga

TaskBoard använder i dag versionerade image-taggar, till exempel:

```dockerfile
FROM nginx:1.30.4-alpine
```

och:

```yaml
image: postgres:18.4-alpine
```

Det är mycket bättre än generella taggar som `latest`, eftersom versionsavsikten är tydlig.

Men en tagg är fortfarande ett namn som ett registry kan låta peka på ett annat image-manifest senare. Docker skiljer därför mellan taggar och **digests**. En digest är en innehållsidentifierare och kan användas för att dra exakt samma imageversion igen. Docker beskriver pull by digest som ett sätt att pinna en image till en specifik version. (Docker Docs, *docker image pull*.)

En strikt referens kan se ut ungefär så här:

```text
postgres:18.4-alpine@sha256:<digest>
```

Då får vi både ett mänskligt läsbart versionsnamn och en exakt innehållsidentitet.

### Men digest-låsning har ett pris

När en image låses till digest kommer den inte automatiskt att följa med om leverantören publicerar en ny image under samma tagg, exempelvis med säkerhetsuppdateringar. Docker påpekar uttryckligen denna konsekvens. (Docker Docs, *docker image pull*.)

Digest-policy måste därför kombineras med en uppdateringsprocess:

```text
ny upstream-image
      |
      v
kontrollera ändring
      |
      v
bygg + test
      |
      v
uppdatera digest
      |
      v
ny release
```

Det är en bättre modell än både "allt flyter automatiskt" och "vi låser för evigt".

## En rimlig digest-policy för TaskBoard

För TaskBoard rekommenderar vi följande målbild:

1. **Utveckling:** använd tydliga versions-taggar för läsbarhet och enkel uppgradering.
2. **Release:** registrera de image-digests som faktiskt användes och verifierades.
3. **Drift:** kör publicerade TaskBoard-images och tredjepartsimages med releasekopplade, verifierade digests när kravbilden motiverar det.
4. **Uppdatering:** byt digest endast genom en ny bygg/test/release-cykel.

Det löser det öppna beslut som följt med från tidigare kapitel: en produktionsinriktad release bör kunna identifiera exakt vilka image-manifest som verifierades, även om den läsbara dokumentationen fortsatt visar versions-taggar.

Referenskoden ändras inte i detta kapitel. Policyn definieras först; automatiseringen kan införas i ett separat utvecklingssteg.

## Byggda TaskBoard-images behöver egna versionsidentiteter

Compose-filen bygger just nu frontend och backend lokalt:

```yaml
backend:
  build:
    context: ./backend

web:
  build:
    context: ./frontend
```

Det är utmärkt för bokens referensflöde och CI-smoke-test. Men en extern mottagare ska inte nödvändigtvis behöva Maven, Node, npm och hela källkodsmiljön för att starta en redan godkänd release.

En produktionsleverans kan i stället publicera färdigbyggda images:

```text
registry.example/taskboard-web:1.2.0
registry.example/taskboard-backend:1.2.0
```

och helst dessutom registrera deras digests.

Då skiljs två aktiviteter tydligt åt:

```text
BUILD
källkod -> verifierade images

DEPLOY
verifierade images + Compose + konfiguration -> körande tjänst
```

Det ger en viktig organisatorisk egenskap: den artefakt som testades kan vara samma artefakt som driftsätts.

Om driftmiljön i stället bygger om från källkod finns alltid en extra fråga: blev det nya bygget verkligen identiskt med det som godkändes?

## Konfiguration ska inte kräva en ny image

Kapitel 11 skiljde mellan applikation och runtime-konfiguration. Den principen blir ännu viktigare i leveranssteget.

TaskBoards databasnamn, användarnamn, lösenord och publicerade port matas in via Compose-/miljökonfiguration. Det gör att samma image kan användas i flera miljöer.

En bra leverans innehåller därför:

- images eller exakta image-referenser,
- `docker-compose.yml` eller motsvarande deploymentdefinition,
- `.env.example` utan riktiga hemligheter,
- dokumentation av obligatoriska konfigurationsvärden,
- instruktioner för hemlighetshantering i målmiljön.

Den bör **inte** kräva att någon bygger en särskild backend-image bara för att databasen heter något annat hos mottagaren.

Konfiguration ska vara data för deploymenten, inte en ny specialkompilering.

## Compose-filen är en del av releaseartefakten

Det räcker inte att versionssätta frontend och backend var för sig.

TaskBoard fungerar som helhet därför att Compose-filen beskriver:

- PostgreSQL-version,
- service-namn,
- nätverkssamband,
- environment mappings,
- healthchecks,
- startberoenden,
- persistent volume,
- publicerad webbport.

Om två organisationer kör samma backend-image men olika Compose-definitioner kan de i praktiken köra två olika system.

Därför ska deploymentdefinitionen kopplas till samma release som applikationskoden.

För TaskBoard betyder det att en leveransversion bör identifiera ett sammanhållet paket:

```text
TaskBoard v1.2.0
  |
  +-- web image + digest
  +-- backend image + digest
  +-- PostgreSQL image + digest
  +-- docker-compose.yml
  +-- .env.example
  +-- migrations/versioner
  +-- installationsinstruktion
  +-- uppgraderingsinstruktion
  +-- release notes
  +-- checksums / manifest
```

Det är helheten som är releasen.

## Checksummor svarar på frågan "är detta samma fil?"

Bokens egen GitHub Actions-release bygger redan EPUB och PDF och skapar `SHA256SUMS.txt`. Samma princip är användbar för tjänsteleveranser.

En SHA-256-checksumma kan användas för att kontrollera att en fil är exakt samma byteföljd som den som checksumman skapades för.

Det är användbart för exempelvis:

```text
docker-compose.yml
installationspaket.zip
release-manifest.json
SQL-/bootstrapfiler
```

Checksumman ger däremot inte automatiskt avsändarautenticitet. Om en angripare kan byta både filen och checksummefilen behövs ytterligare skydd, exempelvis signerade releases, attestering eller en betrodd distributionskanal.

Det är alltså viktigt att skilja på:

- **integritetskontroll** – är filen oförändrad?
- **proveniens/autenticitet** – kommer den från den bygg- och releasekedja vi litar på?

## GitHub Actions är också ett dependency tree

CI-workflowen innehåller själv beroenden:

```yaml
uses: actions/checkout@v5
uses: actions/setup-node@v6
uses: actions/setup-java@v5
```

Versions-taggarna är läsbara och praktiska. De är däremot inte maximalt immutabla.

GitHubs säkerhetsdokumentation rekommenderar fullständig commit-SHA när en action ska pinnas till en oföränderlig revision och beskriver full-length SHA som det säkraste sättet att använda en action som immutable release. (GitHub Docs, *Secure use reference*.)

För en hårdare leveranskedja kan alltså även Actions-dependencies låsas:

```yaml
uses: actions/checkout@<full-commit-sha>
```

Detta är ytterligare ett exempel på samma princip som Docker-digests: vi byter ett bekvämt rörligt namn mot en exakt innehålls-/revisionsidentitet.

Även här krävs en underhållsprocess. Ett pinnat SHA uppdaterar inte sig självt när en säkerhetsfix publiceras.

## Release notes ska beskriva förändring, inte bara version

En mottagare behöver veta mer än att versionen heter `1.2.0`.

Bra release notes för en tjänst bör minst svara på:

- Vad har ändrats för användaren?
- Finns en databas-/Flyway-migration?
- Krävs nya eller ändrade konfigurationsvärden?
- Har någon image eller plattformsversion ändrats?
- Finns kända begränsningar?
- Kan man rulla tillbaka efter migrationen?
- Vilken tidigare version stöds som uppgraderingsväg?

Detta är särskilt viktigt när schemaevolution ingår. En release som innehåller `V7__...sql` är inte bara "ny backendkod". Den förändrar även databasens tillstånd.

Release notes blir därmed en del av den tekniska driftsättningsinformationen.

## Installationsinstruktionen ska börja efter utvecklingsmiljön

En utvecklar-README beskriver ofta hur man installerar Node, kör Maven och bygger projektet. En leveransinstruktion för drift har ett annat perspektiv.

Mottagaren ska kunna börja ungefär här:

```text
1. Installera/ha Docker Engine + Compose enligt stödd nivå.
2. Hämta releasepaketet eller deploymentdefinitionen.
3. Verifiera checksumma/signatur/proveniens.
4. Skapa runtime-konfiguration och secrets.
5. Hämta exakt angivna images.
6. Starta tjänsten.
7. Kontrollera health/readiness.
8. Kör ett definierat funktionsprov.
9. Dokumentera installerad releaseversion.
```

Det är en betydligt bättre överlämning än:

> Klona repot och kör det som utvecklaren gjorde.

Källkod ska finnas och byggprocessen ska vara dokumenterad. Men drift ska inte vara beroende av en enskild utvecklingsmaskins tillstånd.

## Uppgraderingsinstruktionen är en separat artefakt

Installation och uppgradering är inte samma operation.

En uppgradering måste ta hänsyn till befintlig data och föregående systemtillstånd. För TaskBoard bör instruktionen exempelvis ange:

1. stödd källversion,
2. backupkrav före uppgradering,
3. nya image-referenser,
4. eventuella nya konfigurationsvärden,
5. vilka Flyway-migrationer som körs,
6. hur tjänstens hälsa verifieras efteråt,
7. rollback-begränsningar.

Om en migration inte är bakåtkompatibel måste det framgå innan operatören trycker på knappen.

Det är därför kapitel 15 och 16 hör nära ihop: driftbarhet definierar hur vi hanterar förändring, medan den reproducerbara leveransen definierar exakt **vilken** förändring vi introducerar.

## Ett release-manifest knyter ihop helheten

När antalet artefakter växer är ett maskinläsbart manifest användbart. TaskBoards releaseworkflow skapar därför `release-manifest.json` som en del av varje `taskboard-v<SemVer>`-release.

Ett förenklat utdrag ur den faktiska modellen ser ut så här:

```json
{
  "schemaVersion": 1,
  "release": "1.2.0",
  "tag": "taskboard-v1.2.0",
  "gitCommit": "<40-teckens Git-SHA>",
  "images": {
    "web": "ghcr.io/example/taskboard-web@sha256:<digest>",
    "backend": "ghcr.io/example/taskboard-backend@sha256:<digest>",
    "postgres": "postgres@sha256:<digest>"
  },
  "verification": {
    "smokePath": "Nginx -> Quarkus -> PostgreSQL"
  }
}
```

Den verkliga filen innehåller dessutom bland annat GitHub Actions-run-id, verktygsversioner och SHA-256-checksummor för centrala käll- och leveransfiler. Bundle-generatorn validerar att de tre image-referenserna använder SHA-256-digests innan paketet skapas.

Poängen är att releasen blir maskinellt läsbar och granskningsbar. Människan kan läsa release notes; automation kan läsa manifestet.

## Reproducerbarhet är också en supply-chain-fråga

Ju fler externa byggsteg en tjänst har, desto fler saker måste identifieras och verifieras.

TaskBoards kedja innehåller bland annat:

```text
GitHub Actions
Node/npm
npm-paket
Maven
Maven Central-artefakter
Docker Build
Node base image
Nginx base image
Maven/JDK base image
JRE base image
PostgreSQL image
```

Det betyder inte att varje liten tjänst måste införa maximal supply-chain-teknik från dag ett. Men leveransmodellen bör göra beroendena synliga.

En bra mognadstrappa är:

```text
versions-taggar
      |
      v
lockfiler + frysta installationer
      |
      v
image-digests
      |
      v
checksummor
      |
      v
signering / attestering / proveniens
      |
      v
oberoende reproducerbarhetskontroll där det krävs
```

Varje steg minskar ett annat slags osäkerhet.

## TaskBoards nuläge och målbild

Vi kan nu sammanfatta referensimplementationen utan att överdriva.

### Det som redan finns

- explicit valda huvudversioner,
- Git-versionsstyrd källkod,
- deterministisk kapitel-/projektintegritet för bokprojektet,
- verifierad GitHub Actions-build och runtime-verifierad TaskBoard-releasekedja,
- incheckad npm-genererad `package-lock.json` och `npm ci` i både CI och frontendens Docker-build,
- frontend- och backend-Dockerfiles,
- full-SHA-pinning av de externa Actions som används i TaskBoards CI- och releaseworkflow,
- Compose-definition i samma repository,
- `.env.example`,
- Flyway-migrationer i källkod,
- frontend-/backendtester och full-stack smoke test,
- en separat TaskBoard-releasekedja på taggar `taskboard-v<SemVer>`,
- web- och backend-images som smoke-testas före publicering till GHCR,
- releasekopplade registry-digests för web, backend och PostgreSQL,
- `docker-compose.release.yml` som kör publicerade images utan lokal rebuild,
- maskinläsbart `release-manifest.json` med Git commit, Actions-run, image-digests och källchecksummor,
- SHA-256-checksummor för TaskBoards releasepaket samt bokens PDF/EPUB-release.

### Det som fortfarande saknas för en starkare tjänsteleverans

- explicit testad Maven-reproducerbarhet,
- signerad eller attesterad releaseproveniens,
- automatiskt genererad SBOM om kravbilden kräver det,
- fullt testad uppgraderingsguide från en tidigare skarp TaskBoard-release,
- produktionshärdning som autentisering, TLS, secrets-hantering, backup/restore och observability enligt kapitel 11 och 15.

Det är inte brister som gör referensprojektet oanvändbart. De visar vilken gräns vi har nått: från **verifierad referensimplementation** till **formaliserad distributionsprodukt**.

## TaskBoards konkreta releasekedja

Referensimplementationen har nu gjort målbilden i det här kapitlet konkret. Bokens vanliga `v*`-taggar är fortsatt reserverade för EPUB/PDF, medan TaskBoard använder en egen releaseidentitet:

```text
taskboard-v1.0.0
```

När en sådan tagg körs bygger releaseworkflowen frontend och backend, kör samma typer av test som den kanoniska CI:n och bygger sedan Docker-images **en gång**. Compose startar därefter tjänsten med `--no-build`, så smoke-testet kör exakt de imageobjekt som senare taggas och pushas till GHCR. Först efter godkänt smoke test publiceras images.

Efter push läses registry-digests ut för web och backend. PostgreSQL-imagen som faktiskt användes i smoke-testet får på motsvarande sätt sin digest registrerad. Dessa tre immutable referenser skrivs till releasepaketets `release.env`. `docker-compose.release.yml` innehåller inga `build:`-sektioner, vilket betyder att mottagaren inte gör en ny applikationsbuild vid installationen.

`create_release_bundle.py` producerar samtidigt ett maskinläsbart `release-manifest.json` med bland annat:

- SemVer och TaskBoard-taggen,
- repository och full Git commit,
- GitHub Actions-run-id,
- exakta image-referenser med SHA-256-digest,
- Node- och Java-version,
- vilka test-/verifieringssteg releasen gått igenom,
- SHA-256 för `package-lock.json`, Dockerfiles och Compose-definitionerna.

Releasepaketet innehåller dessutom `SHA256SUMS.txt` och en separat installationsinstruktion. Releasekedjan har också körts igenom i GitHub Actions med lyckad GHCR-publicering, digestinsamling, bundle-skapande och GitHub Release, så detta är inte längre bara en statiskt validerad workflowdefinition. Resultatet är fortfarande inte en garanti för bitidentisk rebuild av varje komponent, men det ger en runtime-verifierad och spårbar överlämning där mottagaren kan identifiera **vilken källa, vilka images och vilken deploymentdefinition som hör ihop**.

## Definition of done för en leverans

När TaskBoard någon gång ska lämnas över som en riktig version kan följande fungera som kontrollista:

- releasen har en unik Git-tag,
- taggen pekar på verifierad källkod,
- dependency resolution är låst på avsedd nivå,
- CI bygger och testar från ren miljö,
- de artefakter som testas är de artefakter som publiceras,
- alla images har versionsreferens och dokumenterad digest,
- Compose/deploymentdefinitionen hör till samma release,
- runtime-konfiguration är dokumenterad men hemligheter distribueras inte i källkod,
- databasmigrationer och kompatibilitet framgår,
- checksummor och/eller starkare proveniens finns,
- installationsinstruktion är testad,
- uppgraderingsinstruktion är testad från stödd föregående version,
- mottagaren kan identifiera exakt vad som körs efter installationen.

När de punkterna är uppfyllda har vi gått längre än "det går att bygga".

Vi har en leverans som går att identifiera, verifiera, återinstallera och förvalta.

Och det är först då som frasen **från kod till körbar tjänst** får sin fulla innebörd: inte bara att koden kan köras, utan att den körbara tjänsten kan överlämnas med en spårbar kedja tillbaka till sin källa.
