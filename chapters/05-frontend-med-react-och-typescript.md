# 5. Frontend med React och TypeScript

I förra kapitlet betraktade vi frontend som en PWA: en uppsättning byggda webbresurser med manifest, service worker och en tydlig leveransmodell. Nu går vi innanför det skalet och tittar på själva applikationskoden.

TaskBoard-frontenden är avsiktligt liten. Den har ingen klientrouter, inget globalt state-bibliotek och ingen katalog med dussintals komponenter. I stället består kärnan av två filer:

```text
src/
├── App.tsx
├── api.ts
├── main.tsx
└── styles.css
```

Det gör implementationen användbar som referens. Vi kan se var gränserna faktiskt går utan att de döljs av ramverkslager som applikationen ännu inte behöver.

Kapitlets viktigaste fråga är därför inte hur man skriver JSX. Den är hur vi håller ett litet React-gränssnitt begripligt när det kommunicerar med ett riktigt HTTP-API och samtidigt förbereder strukturen för att kunna växa.

## React är presentations- och interaktionslagret

TaskBoards `main.tsx` gör tre saker:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { registerSW } from 'virtual:pwa-register'
import { App } from './App'
import './styles.css'

registerSW({ immediate: true })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

Den registrerar service workern, skapar React-roten och renderar `App`. PWA-registreringen är en leveransfråga som vi behandlade i kapitel 4. React-trädet börjar i praktiken vid `App`.

Det finns en viktig arkitektonisk poäng här: React behöver inte veta något om Docker, Nginx, PostgreSQL eller hur backend paketeras. Frontendens gräns mot resten av systemet är HTTP-API:t.

Det betyder inte att frontend är oberoende av backendens kontrakt. Tvärtom. Den är beroende av URL:er, JSON-form, tillåtna status- och prioritetsvärden och HTTP-statuskoder. Men dessa beroenden samlas i TypeScript-typer och API-lagret i stället för att spridas genom JSX-koden.

## TypeScript gör kontraktet synligt

I `api.ts` definieras de centrala transporttyperna:

```ts
export type TaskStatus = 'OPEN' | 'IN_PROGRESS' | 'DONE'
export type TaskPriority = 'LOW' | 'NORMAL' | 'HIGH'

export interface Task {
  id: string
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  dueDate: string | null
  createdAt: string
  updatedAt: string
}
```

`TaskStatus` och `TaskPriority` är unioner av strängliteraler. TypeScript kan därför stoppa värden som inte ingår i kontraktet redan vid kompilering. Det är just den sortens enkla typgräns som hade fångat den felaktiga prioriteten `MEDIUM` om den hade skrivits i TypeScript-koden i stället för i ett separat Python-baserat smoke test.

TypeScripts objekt- och unionstyper är särskilt användbara här eftersom de gör API-kontraktets form explicit utan att införa en runtime-klasshierarki. (TypeScript, *Everyday Types*.)

Det är dock viktigt att förstå begränsningen: TypeScript verifierar koden när den byggs, inte JSON-svaret när det kommer över nätverket. Följande rad:

```ts
return response.json() as Promise<T>
```

är ett typantagande. Den gör inte runtime-validering av JSON. Om backend plötsligt skulle svara med en annan struktur kan TypeScript inte rädda en redan byggd klient.

I en större eller mer externt exponerad klient kan det därför vara motiverat att validera inkommande data vid runtime, exempelvis med ett schema- eller valideringsbibliotek. För TaskBoard skulle det lägga mer mekanik än nytta. Backend och frontend utvecklas tillsammans i samma repo och kontraktet verifieras dessutom i den sammanhängande CI-kedjan.

## Läsmodell och skrivmodell är inte identiska

`Task` representerar en uppgift som backend har returnerat. När frontend ska skapa eller uppdatera en uppgift används däremot `SaveTask`:

```ts
export interface SaveTask {
  title: string
  description?: string | null
  status?: TaskStatus
  priority?: TaskPriority
  dueDate?: string | null
}
```

Skillnaden är viktig. Frontend ska inte skicka `id`, `createdAt` eller `updatedAt` som om klienten ägde dessa fält. De skapas och förvaltas av backend.

Detta är en liten variant av ett generellt mönster: modellen vi läser behöver inte vara samma modell som vi skriver. Om man återanvänder en enda stor typ för alla operationer blir det lätt otydligt vilka fält som faktiskt är klientens ansvar.

TaskBoard kallar skrivtypen `SaveTask`. I en större kodbas kan separata typer som `CreateTaskRequest` och `UpdateTaskRequest` vara tydligare om operationerna börjar skilja sig åt.

## Ett litet API-lager håller transportdetaljer borta från UI:t

Kärnan i `api.ts` är den generiska funktionen `request`:

```ts
async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers
    }
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `HTTP ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
```

Fetch API:t gör inte automatiskt ett HTTP-svar med exempelvis 400 eller 500 till ett avvisat Promise. Klienten måste kontrollera responsens status, vilket här görs via `response.ok`. (MDN, *Using the Fetch API*.)

Därefter exponeras ett litet domännära API:

```ts
export const taskApi = {
  list: () => request<Task[]>('/api/tasks'),
  create: (task: SaveTask) => request<Task>('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(task)
  }),
  update: (id: string, task: SaveTask) => request<Task>(`/api/tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(task)
  }),
  remove: (id: string) => request<void>(`/api/tasks/${id}`, { method: 'DELETE' })
}
```

`App.tsx` behöver därmed inte bygga fetch-options, tolka HTTP-status eller repetera API-sökvägar. Komponenten kan uttrycka sin avsikt som `taskApi.list()`, `taskApi.create(...)` och `taskApi.remove(...)`.

Det här är en tillräcklig abstraktion för referensapplikationen. Vi behöver inte ett generiskt repository-lager i frontend bara för symmetrins skull.

## Relativa API-URL:er är en arkitekturdetalj

Alla anrop använder relativa sökvägar:

```text
/api/tasks
```

Det var ett medvetet val redan i kapitel 2. I den produktionslika miljön tar Nginx emot samma origin som levererar frontend och proxar `/api` till backend. Vid lokal Vite-utveckling proxas samma `/api` i stället till `http://localhost:8080`.

Frontendkoden behöver alltså inte ha:

```ts
const apiBase = 'http://localhost:8080'
```

eller miljöspecifika backendadresser inbyggda i bundlen.

Detta är ett bra exempel på hur ett beslut i driftarkitekturen förenklar applikationskoden. Same-origin-modellen är inte bara en Nginx-detalj; den gör själva klienten mer portabel.

## State: serverdata och formulärdata i samma komponent

`App` håller fem statevärden:

```ts
const [tasks, setTasks] = useState<Task[]>([])
const [title, setTitle] = useState('')
const [priority, setPriority] = useState<TaskPriority>('NORMAL')
const [error, setError] = useState<string | null>(null)
const [loading, setLoading] = useState(true)
```

De representerar två typer av information.

Den första gruppen är data som speglar servern:

- `tasks`,
- `loading`,
- `error`.

Den andra gruppen är lokal interaktionsdata:

- `title`,
- `priority`.

I en stor applikation kan det vara klokt att skilja server-state från UI-state tydligare, kanske med en särskild datacache eller egna hooks. TaskBoard behöver inte det ännu. Fem lokala statevariabler är fortfarande lättare att förstå än ett extra state-ramverk.

React beskriver `useState` som mekanismen för information som komponenten behöver komma ihåg mellan renderingar. Det passar exakt här: ett nytt statevärde leder till en ny render där listan eller formuläret återspeglar den aktuella informationen. (React, *useState*.)

## Initial laddning är synkronisering med ett externt system

När komponenten monteras hämtar den uppgifter:

```ts
useEffect(() => {
  void reload()
}, [])
```

`reload` anropar i sin tur API:t och uppdaterar state:

```ts
async function reload() {
  try {
    setError(null)
    setTasks(await taskApi.list())
  } catch (e) {
    setError(e instanceof Error ? e.message : 'Kunde inte hämta uppgifter')
  } finally {
    setLoading(false)
  }
}
```

React beskriver Effects som ett sätt att synkronisera en komponent med ett externt system. Ett HTTP-API är just ett sådant externt system. (React, *useEffect*.)

Det är också värt att notera vad `useEffect` inte används till här. Vi härleder inte UI-state från annat UI-state i en Effect, och vi använder inte Effects som ett generellt flödesverktyg. Användarinitierade operationer ligger i event handlers.

Det håller livscykeln begriplig:

```text
komponenten visas
      |
      v
useEffect -> reload -> GET /api/tasks

användaren klickar
      |
      v
event handler -> API-operation -> stateuppdatering
```

## Strict Mode och utvecklingskörning

`main.tsx` renderar applikationen i `StrictMode`. I utveckling kan React därför göra en extra setup/cleanup-cykel för Effects för att hitta problem med sidoeffekter. Reacts dokumentation beskriver detta som en utvecklingskontroll; det är inte samma beteende som en produktionsrendering. (React, *useEffect*.)

TaskBoards initiala GET är idempotent och klarar den typen av extra utvecklingskörning. Det är en viktig egenskap. Ett Effect som exempelvis skapade en ny uppgift vid mount hade varit betydligt mer problematiskt.

Det ger en generell regel: sidoeffekter som körs av komponentlivscykeln bör tåla den livscykel som ramverket faktiskt använder. Muterande affärsoperationer hör normalt hemma bakom explicita användarhändelser eller ett noggrant designat synkroniseringsflöde.

## Skapa: formulärstate blir ett API-anrop

Formuläret är kontrollerat av React:

```tsx
<input
  aria-label="Titel"
  value={title}
  onChange={event => setTitle(event.target.value)}
  placeholder="Vad behöver göras?"
  maxLength={160}
/>
```

När formuläret skickas stoppas browserns vanliga submit-navigation:

```ts
async function createTask(event: FormEvent) {
  event.preventDefault()
  if (!title.trim()) return

  try {
    const created = await taskApi.create({ title: title.trim(), priority })
    setTasks(current => [created, ...current])
    setTitle('')
    setPriority('NORMAL')
  } catch (e) {
    setError(e instanceof Error ? e.message : 'Kunde inte skapa uppgiften')
  }
}
```

När backend svarar med den skapade uppgiften läggs just det servergenererade objektet in i listan. Frontend hittar alltså inte själv på `id` eller tidsstämplar för att sedan försöka synkronisera dem.

Stateuppdateringen använder funktionsformen:

```ts
setTasks(current => [created, ...current])
```

Det är rätt mönster när nästa värde beror på föregående state. React kan då ge updater-funktionen det aktuella statevärdet även när flera uppdateringar köas. (React, *useState*.)

## Uppdatera utan att ladda om hela listan

När status ändras skickar klienten en `PUT` med uppgiftens nuvarande skrivbara fält och den nya statusen. Backend returnerar den uppdaterade uppgiften:

```ts
const updated = await taskApi.update(task.id, {
  title: task.title,
  description: task.description,
  priority: task.priority,
  dueDate: task.dueDate,
  status
})
```

Listan uppdateras sedan lokalt:

```ts
setTasks(current =>
  current.map(item => item.id === updated.id ? updated : item)
)
```

Det undviker ett extra GET-anrop efter varje statusändring, men låter ändå backend vara sanningskälla för det objekt som sparats.

Detta ska inte förväxlas med en avancerad optimistic update. UI:t ändras först när API-anropet har lyckats. En verkligt optimistisk modell skulle kunna uppdatera state före svaret och rulla tillbaka vid fel. Det kan ge snabbare upplevd respons, men kräver mer fel- och konfliktlogik än TaskBoard behöver.

## Ta bort och spegla serverresultatet

Radering följer samma princip:

```ts
await taskApi.remove(task.id)
setTasks(current => current.filter(item => item.id !== task.id))
```

API-lagret känner till att backend svarar med HTTP 204 och returnerar därför inget JSON-objekt. Först efter lyckat svar filtreras uppgiften bort ur state.

Återigen prioriterar referensimplementationen begriplighet framför maximal upplevd snabbhet.

## Felhantering: en enkel men synlig modell

Alla operationer fångar fel och skriver ett meddelande till samma `error`-state. I renderingen visas det som:

```tsx
{error && <p className="error" role="alert">{error}</p>}
```

`role="alert"` gör att felet inte bara blir visuell text utan också får en semantisk roll för hjälpmedel.

Den nuvarande modellen är medvetet enkel. Den skiljer inte på:

- nätverksfel,
- valideringsfel,
- 404,
- konflikt,
- internt serverfel.

Dessutom använder `request` backendens response body direkt som felmeddelande om den finns. För en intern referenstjänst är det tillräckligt, men i en större produkt bör API:t ha ett stabilt felkontrakt och frontend översätta det till användaranpassade meddelanden. Interna undantagsdetaljer ska inte bli UI-text.

Detta återkommer vi till när hela requestkedjan behandlas i kapitel 10.

## Loading är inte samma sak som mutationstillstånd

`loading` används för den initiala listladdningen:

```tsx
{loading ? <p>Laddar…</p> : tasks.length === 0 ? ... }
```

Skapa, uppdatera och radera har däremot inga separata `saving`- eller `deleting`-tillstånd. Det innebär bland annat att knapparna inte spärras medan ett anrop pågår.

Det är en rimlig förenkling för en liten referensimplementation, men också en tydlig expansionspunkt. När UI:t blir mer produktionsnära bör vi kunna svara på frågor som:

- Kan användaren skicka samma formulär två gånger snabbt?
- Ska statuskontrollen inaktiveras under sparning?
- Hur visar vi att just en uppgift håller på att raderas?
- Vad händer om två operationer mot samma uppgift pågår samtidigt?

Att göra dessa tillstånd explicita är ofta viktigare än att introducera fler komponenter tidigt.

## Ingen router – ännu

TaskBoards nuvarande frontend har medvetet bara en sammanhållen vy. Alla uppgifter visas och hanteras i `App`; det finns ännu ingen separat detaljvy eller redigeringsroute.

Det är viktigt att boken är trogen referenskoden. Vi ska därför inte beskriva en React Router-konfiguration som inte finns.

Om TaskBoard senare får exempelvis:

```text
/tasks
/tasks/:id
/settings
```

blir en klientrouter naturlig. Då får URL:en en tydligare roll som navigerbart UI-state. Men att lägga in routing i förväg skulle öka antalet begrepp utan att lösa ett aktuellt problem.

Samma princip gäller komponentuppdelning.

## När bör `App.tsx` delas upp?

I dag innehåller `App` både formuläret och listan. Det är fortfarande överblickbart. När ansvaren börjar växa kan en naturlig utveckling vara:

```text
App
├── TaskCreateForm
└── TaskList
    └── TaskListItem
```

API-logiken kan samtidigt kapslas i hooks om flera komponenter behöver samma dataflöde:

```text
useTasks()
useCreateTask()
```

Men komponenter och hooks bör brytas ut därför att de skapar en tydligare ansvarsfördelning, inte därför att en fil passerar ett godtyckligt antal rader.

För referensprojektet är gränsen mellan `App.tsx` och `api.ts` viktigare än en finfördelning av JSX. UI-koden vet vad användaren vill göra; API-koden vet hur HTTP-kontraktet ser ut.

## Transportmodell och UI-modell kan växa isär

TaskBoard visar i dag backendens `Task` nästan direkt. Det fungerar eftersom UI:t är litet och datamodellen enkel.

I en större applikation kan det finnas goda skäl att skapa en separat UI-modell. Exempelvis kan ett datum från API:t vara en ISO-sträng medan en datumväljare arbetar med ett annat format. Eller så kanske flera backendfält kombineras till ett presentationsvärde.

Den viktiga principen är att inte låta transportformatet bli ett oavsiktligt globalt domänspråk i hela frontendkoden.

I TaskBoard är separationen redan påbörjad genom att transporten är samlad i `api.ts`. Det gör det möjligt att införa mapping senare utan att byta HTTP-anrop i varje komponent.

## Frontendens kontrakt mot backend

Vi kan nu sammanfatta gränsen mellan frontend och backend:

```text
React-komponent
     |
     | Task / SaveTask
     v
   taskApi
     |
     | HTTP + JSON
     v
  /api/tasks
```

React behöver inte känna till JPA-entiteten. TypeScript-typen behöver inte känna till PostgreSQL-tabellen. API-lagret behöver inte känna till Nginx mer än att `/api` fungerar från klientens origin.

Det är denna kedja som gör stacken utbytbar i rätt riktning. Backend kan ändra sin interna persistensimplementation utan att React påverkas, så länge HTTP-kontraktet består. Frontend kan delas upp i fler komponenter utan att databasen påverkas.

Gränserna är viktigare än antalet bibliotek.

## Vad referensimplementationen medvetet saknar

TaskBoard-frontenden innehåller ännu inte:

- klientrouting,
- global state-store,
- datafetching-/cachebibliotek,
- runtime-validering av JSON,
- separata create/update-DTO:er,
- optimistic updates,
- fältvis valideringspresentation,
- mutationstillstånd per operation,
- automatiserade frontendtester.

Det är inte en lista över brister som måste åtgärdas innan applikationen får köras. Det är en lista över mekanismer som ska tillkomma först när deras nytta motiverar deras kostnad.

Den kompletta tjänsten bygger, startar och klarar ett end-to-end-smoke test redan med denna frontend. Det ger oss ett fungerande minimum att resonera vidare från.

## Kapitlets viktigaste slutsatser

TaskBoard visar en liten men tydlig React/TypeScript-arkitektur:

- `App.tsx` äger den nuvarande UI-kompositionen och lokalt state.
- `api.ts` samlar transporttyper, URL:er, fetch-anrop och grundläggande HTTP-felhantering.
- Strängliteral-unioner gör backendens status- och prioritetsvärden synliga i TypeScript.
- Läsmodellen `Task` skiljs från skrivmodellen `SaveTask`.
- Relativa `/api`-URL:er gör samma frontendkod användbar bakom Vites utvecklingsproxy och Nginx i körmiljön.
- `useEffect` används för initial synkronisering med API:t, medan muterande operationer ligger i event handlers.
- Serverns svar används för att uppdatera lokalt state efter lyckade create- och update-operationer.
- Nuvarande fel- och loadingmodell är avsiktligt enkel och har tydliga expansionspunkter.
- Router, global state och fler abstraktionslager införs inte förrän applikationen faktiskt behöver dem.

Frontendgränsen är därmed etablerad. I nästa kapitel går vi över `/api` och tittar på den andra sidan av kontraktet: hur Quarkus tar emot HTTP-anropen, validerar dem och organiserar backendlogiken utan att göra en erfaren Java-utvecklare beroende av onödig ramverksmagi.
