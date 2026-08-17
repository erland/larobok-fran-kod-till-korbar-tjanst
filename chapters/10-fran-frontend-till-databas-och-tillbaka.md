# 10. Från frontend till databas och tillbaka

I de föregående kapitlen har vi studerat lagren var för sig. React håller användargränssnittets state. Nginx är den publika ingången. Quarkus tar emot HTTP-anrop och delegerar arbete. JPA mappar Java-objekt till databasen. PostgreSQL lagrar data och Flyway håller schemat reproducerbart.

Nu knyter vi ihop allt.

Vi följer ett konkret användningsfall genom hela TaskBoard: en användare ändrar en uppgifts status från `IN_PROGRESS` till `DONE`.

Det låter som en liten operation. I verkligheten passerar informationen flera kontrakt och flera tekniska gränser:

```text
Användare
   |
   v
React-komponent
   |
   v
TypeScript API-klient
   |
   v
HTTP PUT /api/tasks/{id}
   |
   v
Nginx reverse proxy
   |
   v
Quarkus REST-resurs
   |
   v
Bean Validation
   |
   v
Tjänstelager + transaktion
   |
   v
JPA / Hibernate ORM
   |
   v
PostgreSQL
   |
   v
samma väg tillbaka som JSON-svar
```

Det är här en fullstack-tjänst blir begriplig på riktigt: inte genom att varje teknik kan beskrivas separat, utan genom att samma information kan följas från användarens handling till beständig data och tillbaka igen.

## Klicket i användargränssnittet

I `App.tsx` visas statusen för varje uppgift i en `select`:

```tsx
<select
  aria-label={`Status för ${task.title}`}
  value={task.status}
  onChange={event => void changeStatus(task, event.target.value as TaskStatus)}
>
```

När användaren väljer `Klar` får `changeStatus` värdet `DONE`:

```ts
async function changeStatus(task: Task, status: TaskStatus) {
  try {
    const updated = await taskApi.update(task.id, {
      title: task.title,
      description: task.description,
      priority: task.priority,
      dueDate: task.dueDate,
      status
    })

    setTasks(current =>
      current.map(item => item.id === updated.id ? updated : item)
    )
  } catch (e) {
    setError(e instanceof Error ? e.message : 'Kunde inte uppdatera uppgiften')
  }
}
```

Två saker är värda att notera.

För det första skickar frontenden inte bara den ändrade statusen. TaskBoards nuvarande API använder `PUT` med en `SaveTask`-representation, så även titel, beskrivning, prioritet och förfallodatum skickas tillbaka.

För det andra ändras inte React-state förrän servern har accepterat uppdateringen och returnerat den uppdaterade uppgiften. TaskBoard använder alltså inte optimistic update här. UI:t väntar på backendens svar och ersätter därefter den gamla posten med serverns representation.

Det ger ett enkelt sanningsflöde:

```text
UI skickar önskad ändring
        |
        v
servern gör ändringen
        |
        v
servern returnerar verkligt resultat
        |
        v
UI uppdaterar sitt state
```

För en liten referenstjänst är detta lätt att förstå och lätt att felsöka.

## API-klienten gör JavaScript-objekt till HTTP

`taskApi.update` finns i `api.ts`:

```ts
update: (id: string, task: SaveTask) => request<Task>(`/api/tasks/${id}`, {
  method: 'PUT',
  body: JSON.stringify(task)
})
```

Här sker den första tydliga transformationsgränsen:

```text
TypeScript-objekt
      |
JSON.stringify
      v
JSON-text i HTTP request body
```

Den generella `request`-funktionen lägger också till:

```http
Content-Type: application/json
```

och skickar anropet till en relativ URL:

```text
/api/tasks/<uuid>
```

Det betyder att frontendkoden inte behöver veta om backend kör på port 8080, i en annan container eller på en annan värd internt. Den känner bara till sitt publika API-kontrakt.

I lokal Vite-utveckling kan `/api` proxas av Vites dev-server. I den produktionslika Compose-körningen tas samma URL emot av Nginx. Frontendkoden behöver inte ändras mellan miljöerna.

Det är en konkret fördel med same-origin-modellen som vi såg tidigare.

## Nginx dirigerar, men äger inte verksamhetslogiken

Nginx-konfigurationen innehåller:

```nginx
location /api/ {
    proxy_pass http://backend:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

När webbläsaren anropar exempelvis:

```text
PUT /api/tasks/7d1e...
```

vidarebefordrar Nginx requesten till Compose-tjänsten `backend` på port 8080.

Nginx tolkar inte uppgiftens status. Den vet inte vad `DONE` betyder och känner inte till PostgreSQL-tabellen. Dess ansvar är transport och routing.

Det är ett viktigt arkitekturmönster:

```text
Nginx        transport/routing
Quarkus      API och applikationslogik
PostgreSQL   persistent data
```

När varje lager får ett tydligt ansvar blir fel också lättare att lokalisera.

## Quarkus mappar HTTP till Java

TaskBoards REST-resurs har följande metod:

```java
@PUT
@Path("/{id}")
public TaskResponse update(
        @PathParam("id") UUID id,
        @Valid SaveTaskRequest request) {
    return service.update(id, request);
}
```

När requesten når Quarkus händer flera saker innan tjänstelagret anropas.

Path-parametern konverteras till `UUID`.

JSON-kroppen deserialiseras till:

```java
public record SaveTaskRequest(
        @NotBlank @Size(max = 160) String title,
        @Size(max = 4000) String description,
        TaskStatus status,
        TaskPriority priority,
        LocalDate dueDate) {
}
```

`@Valid` aktiverar Bean Validation på requestobjektet.

En request som saknar giltig titel kan därför stoppas innan `TaskService.update` körs.

Detta är en integrationspunkt som ofta förbises: TypeScript-typen i webbläsaren är inte säkerhetsgränsen. En annan klient kan skicka vilken JSON som helst. Backend måste därför validera det den tar emot.

## Kontraktet innehåller mer än fältnamn

Det är lätt att tänka att API-kontraktet bara är JSON-strukturen:

```json
{
  "title": "Publicera dokumentation",
  "description": null,
  "status": "DONE",
  "priority": "NORMAL",
  "dueDate": null
}
```

Men det verkliga kontraktet innehåller mer:

- HTTP-metod: `PUT`
- URL: `/api/tasks/{id}`
- `{id}` måste kunna tolkas som UUID
- `Content-Type` är JSON
- `title` får inte vara blank
- `title` får vara högst 160 tecken
- `description` får vara högst 4000 tecken
- `status` måste vara ett känt enumvärde
- `priority` måste vara ett känt enumvärde
- svaret ska kunna tolkas som `Task`

Det var just en sådan kontraktsdetalj som tidigare fångades av TaskBoards smoke-test: testet skickade `MEDIUM`, medan backendens verkliga enumvärde var `NORMAL`. HTTP 400 var då ett korrekt svar på ett felaktigt kontrakt.

Den typen av fel visar varför ett end-to-end-test ger ett annat värde än separata byggtester. Frontend kan kompilera och backend kan starta, men integrationen kan ändå vara fel.

## Tjänstelagret skapar transaktionsgränsen

När requesten är accepterad körs:

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

`required(id)` hämtar entiteten genom repositoryt:

```java
private TaskEntity required(UUID id) {
    return repository.find(id).orElseThrow(NotFoundException::new);
}
```

Om uppgiften inte finns avbryts flödet med ett not-found-fel.

Om den finns är `TaskEntity` managed i den aktuella persistence contexten. Koden sätter nya fältvärden men anropar inte någon explicit `update`-metod på repositoryt.

Det fungerar eftersom JPA/Hibernate använder dirty checking. När transaktionen avslutas jämförs den managed entitetens tillstånd och relevanta ändringar skrivs till databasen.

Förenklat:

```text
SELECT task_item ...
        |
        v
managed TaskEntity
        |
Java-fält ändras
        |
        v
transaction commit
        |
        v
UPDATE task_item ...
```

## Databasen är den persistenta sanningen

`TaskEntity` mappar mot tabellen:

```text
task_item
```

Status lagras som sträng eftersom fältet har:

```java
@Enumerated(EnumType.STRING)
```

Så `TaskStatus.DONE` blir databasmässigt värdet:

```text
DONE
```

Samtidigt uppdateras `updated_at` med en UTC-tidpunkt.

Entiteten har också:

```java
@Version
public long version;
```

Det innebär att Hibernate använder en versionskolumn för optimistisk låsning. Vid en faktisk uppdatering kan SQL därför konceptuellt innehålla både radens id och förväntad versionsnivå.

Detta skyddar persistens-lagret mot vissa samtidiga uppdateringar, men TaskBoards HTTP-API exponerar ännu inte versionsfältet till klienten. Webbläsaren har alltså inte ett explicit ETag-/versionsbaserat stale-write-kontrakt. Det är viktigt att hålla isär de två nivåerna.

## Commit först, svar sedan

Tjänstemetoden bygger ett `TaskResponse` från entiteten:

```java
return TaskResponse.from(entity);
```

Quarkus serialiserar därefter svaret till JSON.

Klienten får exempelvis:

```json
{
  "id": "7d1e...",
  "title": "Publicera dokumentation",
  "description": null,
  "status": "DONE",
  "priority": "NORMAL",
  "dueDate": null,
  "createdAt": "2026-08-16T18:00:00Z",
  "updatedAt": "2026-08-16T20:15:00Z"
}
```

Det är detta servergenererade svar som React sedan lägger in i sitt state.

Vi har därmed gått hela vägen:

```text
DONE i select
   |
   v
TaskStatus i TypeScript
   |
   v
"DONE" i JSON
   |
   v
TaskStatus.DONE i Java
   |
   v
TaskEntity.status
   |
   v
'DONE' i PostgreSQL
   |
   v
TaskResponse
   |
   v
"DONE" i JSON
   |
   v
Task.status i React
```

Samma semantiska värde passerar alltså flera representationer.

## Felvägar är en del av integrationsdesignen

En fungerande kedja är bara halva bilden. Vi behöver också förstå vad som händer när något går fel.

### Ogiltig request

Om klienten skickar en blank titel kan Bean Validation stoppa requesten.

```text
Frontend/client
    |
    v
Quarkus validation
    |
    X
HTTP 400
```

TaskBoards `request`-funktion ser att `response.ok` är falskt, läser response body som text och kastar ett `Error`.

`changeStatus` eller `createTask` fångar felet och sätter `error` i React-state. UI:t visar sedan felet i:

```tsx
{error && <p className="error" role="alert">{error}</p>}
```

### Okänt id

Om UUID:t är syntaktiskt giltigt men ingen rad finns kastar tjänstelagret `NotFoundException`.

Det är ett annat fel än en ogiltig request: requestens form är korrekt, men resursen finns inte.

### Backend eller databas är otillgänglig

Om backend inte kan nå PostgreSQL går felet längre ned i stacken. Frontendens API-klient behöver inte känna till JDBC eller SQL för att uppfatta resultatet som ett misslyckat HTTP-anrop.

Det är ett exempel på varför lagergränser är användbara. Varje lager översätter problem till sitt eget kontrakt.

## Create, list och delete följer samma princip

Samma integrationsmodell återkommer i övriga operationer.

### Create

```text
React-formulär
   |
POST /api/tasks
   |
SaveTaskRequest
   |
TaskService.create
   |
EntityManager.persist
   |
INSERT i PostgreSQL
   |
201 Created + TaskResponse
   |
React lägger till uppgiften i state
```

Backend skapar bland annat UUID, `createdAt`, `updatedAt` och standardvärden för status/prioritet när de saknas.

### List

```text
GET /api/tasks
   |
TaskResource.list
   |
TaskRepository.list
   |
JPQL
   |
SELECT från PostgreSQL
   |
List<TaskResponse>
   |
JSON-array
   |
setTasks(...)
```

Repositoryt sorterar på `createdAt desc`, vilket gör att den senaste uppgiften visas först.

### Delete

```text
DELETE /api/tasks/{id}
   |
TaskService.delete
   |
EntityManager.remove
   |
DELETE i PostgreSQL
   |
204 No Content
   |
React filtrerar bort posten ur state
```

API-klienten har särskild hantering för 204:

```ts
if (response.status === 204) {
  return undefined as T
}
```

Det visar att även ett svar utan body är en del av kontraktet.

## Ett lager ska inte känna till mer än nödvändigt

När vi följer hela kedjan blir en annan arkitekturprincip tydlig.

React känner inte till SQL.

Nginx känner inte till `TaskStatus`.

REST-resursen känner inte till tabellindex.

Repositoryt känner inte till knappar eller formulär.

PostgreSQL känner inte till React-state.

Det är inte absolut isolering — lagren måste naturligtvis passa ihop — men beroendena går genom definierade kontrakt.

Ett bra sätt att tänka är:

```text
UI-kontrakt
    ↓
HTTP/JSON-kontrakt
    ↓
Java-tjänstekontrakt
    ↓
Persistence-kontrakt
    ↓
Databasschema
```

Ju tydligare varje gräns är, desto lättare blir det att ändra en del utan att resten faller sönder.

## Integrationstester verifierar det som separata tester missar

TaskBoards GitHub Actions-workflow kör först frontendens komponenttester och backendens API-/integrationstester, bygger frontend och backend var för sig, bygger Docker-images och startar sedan hela Compose-stacken.

Smoke-testet anropar därefter tjänsten utifrån via Nginx och verifierar bland annat att en uppgift kan skapas och läsas tillbaka. Testlagren kompletterar alltså varandra: de mindre testerna lokaliserar kontrakts- och beteendefel närmare källan, medan smoke-testet verifierar den deployade kedjan.

Det testar inte varje detalj, men det verifierar en mycket viktig egenskap:

```text
Den deployade kedjan fungerar tillsammans.
```

Det är en annan fråga än:

```text
Kompilerar varje del för sig?
```

Båda behövs.

Ett felaktigt enumvärde, en trasig proxyregel, en felaktig JDBC-URL eller en migrationsmiss kan passera lokala enhetstester men stoppas av ett komplett request-flöde.

## Vad kapitlet visar

När användaren markerar en uppgift som klar händer alltså inte bara "en uppdatering".

Det sker en sekvens av översättningar och ansvarsskiften:

1. React fångar användarens avsikt.
2. TypeScript API-klienten serialiserar requesten till JSON.
3. Nginx dirigerar `/api` till backend.
4. Quarkus mappar HTTP till Java och validerar requesten.
5. Tjänstelagret skapar transaktionsgränsen och tillämpar applikationsregler.
6. JPA/Hibernate arbetar med en managed entitet.
7. PostgreSQL gör förändringen persistent.
8. Backend bygger en response-representation.
9. JSON-svaret går tillbaka genom Nginx.
10. React ersätter den gamla posten med serverns resultat.

Det är den kompletta tjänsten i koncentrerad form.

I nästa kapitel flyttar vi fokus från informationsflödet till **konfiguration och säkerhet**: vilka värden som ska ligga utanför koden, vilka gränser reverse proxy-modellen skapar, och vilka säkerhetsantaganden som är rimliga respektive farliga i en containeriserad webbtjänst.
