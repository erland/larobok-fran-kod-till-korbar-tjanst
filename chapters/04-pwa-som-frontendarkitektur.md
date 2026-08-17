# 4. PWA som frontendarkitektur

En React-applikation blir inte en Progressive Web App bara för att den går att öppna i en mobil webbläsare. PWA-egenskaper uppstår när webbapplikationen kompletteras med sådant som gör att webbläsaren kan behandla den mer som en installerbar applikation: ett web app manifest, en service worker, ikoner och en leveransmiljö som uppfyller webbläsarens säkerhetskrav.

För TaskBoard är PWA inte ett separat tekniklager vid sidan av React. Det är ett antal egenskaper i **frontendens leveransmodell**. React-komponenterna beskriver användargränssnittet. Vite bygger applikationen. `vite-plugin-pwa` genererar manifest och service worker. Nginx levererar de byggda filerna i den produktionslika miljön.

Det gör PWA-frågan relevant långt utanför frontendkoden. När en service worker börjar cacha resurser påverkas också releasebeteende, felsökning och vilka HTTP-cache-regler som är lämpliga. En ny frontendversion kan vara korrekt byggd på servern men ändå inte bli synlig om klienten använder äldre cachade resurser på ett sätt vi inte har tänkt igenom.

Kapitlets kärnfråga är därför inte bara *hur installerar vi en React-app?* utan:

> Hur får vi PWA-egenskaper utan att samtidigt göra tjänstens uppdaterings- och offlinebeteende svårförutsägbart?

TaskBoard väljer en relativt konservativ modell: applikationsskalet kan installeras och precachas, medan affärsdata fortfarande hämtas från backend. Vi bygger alltså inte en offline-first-synkroniseringsmotor. Det är ett medvetet arkitekturbeslut.

## PWA är en uppsättning webbegenskaper

Begreppet PWA beskriver inte ett särskilt JavaScript-ramverk. Samma PWA-principer kan användas oavsett om gränssnittet är byggt med React, Vue eller utan ramverk.

För TaskBoard är fyra delar särskilt viktiga:

1. **Web app manifest** – beskriver hur applikationen ska presenteras när den installeras.
2. **Service worker** – kan fånga nätverksanrop och hantera cache oberoende av React-applikationens vanliga JavaScript-tråd.
3. **Säker leveranskontext** – installerbara PWA:er behöver normalt levereras över HTTPS; localhost och loopbackadresser är undantag för utveckling.
4. **Medveten cache- och uppdateringsstrategi** – avgör vilka resurser som kan användas offline och hur en ny version tas i bruk.

MDN beskriver web app manifestet som den metadatafil som ger webbläsaren information om bland annat namn, ikoner och startbeteende för en installerbar webbapplikation. För installation i en riktig miljö krävs HTTPS, medan `localhost` och `127.0.0.1` kan användas över HTTP i utveckling. (MDN, *Making PWAs installable*)

Det är viktigt att skilja **installationsbarhet** från **offlinekapacitet**. En manifestfil beskriver applikationen för webbläsaren. En service worker kan ge offlinebeteende. De två hör ofta ihop i en PWA, men de löser olika problem.

## TaskBoards PWA-konfiguration

TaskBoards PWA-konfiguration ligger i `frontend/vite.config.ts`. Den relevanta delen är:

```ts
VitePWA({
  registerType: 'autoUpdate',
  includeAssets: ['icon.svg'],
  manifest: {
    name: 'TaskBoard',
    short_name: 'TaskBoard',
    description: 'Bokens referenstjänst för arbetsuppgifter',
    theme_color: '#172033',
    background_color: '#f7f8fb',
    display: 'standalone',
    start_url: '/',
    icons: [
      {
        src: '/icon.svg',
        sizes: 'any',
        type: 'image/svg+xml',
        purpose: 'any maskable'
      }
    ]
  }
})
```

`vite-plugin-pwa` använder den här konfigurationen för att generera web app manifest, service worker och registreringskod när applikationen byggs. Pluginets dokumentation beskriver att standardflödet kan generera manifestet, generera service workern och registrera den i webbläsaren utan att React-komponenterna själva behöver innehålla service-worker-kod. (Vite PWA, *Getting Started*)

Det här är en viktig ansvarsgräns. `App.tsx` behöver inte veta hur PWA-installationen fungerar. Den kan fortsätta fokusera på uppgifter, formulär och API-anrop.

## Manifestet är ett installationskontrakt

Manifestet innehåller metadata som används när webbläsaren och operativsystemet presenterar den installerade applikationen.

TaskBoard sätter bland annat:

```text
name             TaskBoard
short_name       TaskBoard
display          standalone
start_url        /
theme_color      #172033
background_color #f7f8fb
```

`display: 'standalone'` uttrycker att applikationen, när plattformen stöder det, ska startas i en mer app-lik vy utan webbläsarens vanliga navigationsgränssnitt. `start_url: '/'` anger den rekommenderade startpunkten när användaren öppnar den installerade appen. MDN beskriver `start_url` som den URL som ska användas när applikationen startas från exempelvis hemskärm eller applikationslista. (MDN, *start_url*)

Manifestet är däremot inte en garanti för exakt samma användarupplevelse på alla plattformar. Installationsgränssnitt och vilka manifestmedlemmar som används varierar mellan webbläsare och operativsystem.

Det gäller särskilt ikoner. TaskBoards referensimplementation använder i nuläget en SVG med `sizes: 'any'`. Det är praktiskt i ett litet referensprojekt, men för en produktionsleverans som ska ge så förutsägbar installationsupplevelse som möjligt bör vi komplettera med rasterikoner i de storlekar som målplattformarna förväntar sig. MDN anger till exempel 192- och 512-pixelsikoner som krav i Chromium-baserade webbläsare för deras installationskriterier. (MDN, *Making PWAs installable*)

Det är alltså viktigt att skilja på **referensimplementationens minsta fungerande konfiguration** och en fullständig ikonmatris för alla tänkbara målplattformar.

## Service workern ligger mellan webbläsaren och nätverket

En service worker körs separat från applikationens vanliga renderingskod. Den kan reagera på nätverksanrop och svara från cache när det är lämpligt.

Förenklat kan requestvägen därför se ut så här efter att service workern har installerats:

```text
React-applikation
       |
       v
Service worker
   |        |
   |        +--> Cache
   |
   +------------> Nätverk
```

Det här är kraftfullt, men det förändrar också frontendens livscykel. Utan service worker är modellen relativt enkel: användaren laddar den version som webbservern levererar och HTTP-cachen tillåter. Med en service worker finns ytterligare ett lager som kan fortsätta leverera resurser även när servern redan innehåller en ny release.

Därför bör vi aldrig lägga till service worker enbart för att få en installationsikon. Vi måste också förstå hur uppdateringar och cache fungerar.

## Precache av applikationsskalet

I TaskBoard använder vi `vite-plugin-pwa` med dess standardbaserade Workbox-flöde. Vid build genereras en service worker som kan precacha frontendens byggda resurser. Pluginets dokumentation anger att HTML-, CSS- och JavaScript-resurser som standard kan tas med i precache-manifestet. När en resurs ändras får den en ny revision i service workerns precache-information. (Vite PWA, *Service Worker Precache*)

Det passar Vites produktionsbygge väl. Filnamn för JavaScript och CSS innehåller normalt innehållsbaserade hashvärden, till exempel i stil med:

```text
assets/index-D3xY...js
assets/index-C9aB...css
```

När innehållet ändras blir namnet ett annat. Gamla och nya versioner kan därför särskiljas tydligt.

Det ger oss en modell där frontendens **applikationsskal** kan finnas lokalt även när nätverket tillfälligt försvinner.

Men det betyder inte att TaskBoard som helhet fungerar offline.

## TaskBoard är inte offline-first

TaskBoard hämtar uppgifterna via:

```text
/api/tasks
```

Den nuvarande PWA-konfigurationen lägger inte till någon särskild runtime-cache för `/api`. Vi lagrar inte heller uppgifterna i IndexedDB eller någon annan lokal databas och vi har ingen synkroniseringskö för förändringar som görs offline.

Det innebär en medvetet begränsad offline-modell:

```text
Statiskt applikationsskal    kan finnas i service worker-cache
TaskBoard-data               hämtas från backend
Skapa/ändra/radera uppgift   kräver fungerande backendanslutning
Offline-synkronisering       finns inte
```

Om användaren tappar nätverket kan webbläsaren alltså ha tillräckligt med statiska resurser för att visa själva React-applikationen, men anropet för att hämta uppgifter kommer att misslyckas. Frontendens befintliga felhantering visar då ett felmeddelande i stället för att presentera en lokal kopia av data som om den vore aktuell.

Det här är en viktig egenskap, inte en brist som behöver döljas. Offline-first för en skrivbar applikation innebär betydligt mer än att cacha JSON-svar. Vi behöver då ta ställning till exempelvis:

- vad användaren får ändra offline,
- hur lokala ändringar lagras,
- när synkronisering sker,
- hur konflikter hanteras,
- hur användaren ser skillnad på synkroniserade och osynkroniserade data.

För en bok vars huvudmål är att visa en komplett React–Quarkus–PostgreSQL-tjänst skulle den mekaniken dra arkitekturen i en annan riktning. Vi väljer därför online-first för affärsdata och använder PWA-egenskaper främst för installation och robust leverans av frontendresurser.

## `autoUpdate` är ett medvetet releaseval

TaskBoard konfigurerar:

```ts
registerType: 'autoUpdate'
```

I `vite-plugin-pwa` innebär det att service workern konfigureras för att ta den nya versionen i bruk automatiskt när uppdateringsflödet har gått igenom. Pluginets dokumentation beskriver att `autoUpdate` använder `skipWaiting` och `clientsClaim` för att låta den nya service workern aktiveras och ta kontroll över klienter. (Vite PWA, *Automatic reload*)

Det förenklar TaskBoard eftersom applikationen inte innehåller något eget gränssnitt som frågar användaren om en ny version ska installeras.

Trade-offen är att vi ger användaren mindre kontroll över tidpunkten för frontenduppdateringen. I en applikation där användaren kan ha ett långt, osparat arbetsflöde skulle en mer explicit uppdateringsmodell kunna vara bättre. Då kan applikationen visa något i stil med ”En ny version finns – ladda om när du är klar”.

TaskBoard har små, korta interaktioner och sparar ändringar mot backend direkt. Därför är `autoUpdate` ett rimligt val i referensimplementationen.

Poängen är inte att `autoUpdate` alltid är bäst, utan att **uppdateringsstrategin ska väljas utifrån användningsmönstret**.

## HTTPS hör till driftsarkitekturen

Lokalt kan vi testa PWA-beteende via `localhost` eller `127.0.0.1`. En riktig distribuerad installation behöver däremot normalt HTTPS för att service workers och installationsflöden ska fungera som avsett. (MDN, *Making PWAs installable*)

TaskBoards Compose-fil exponerar Nginx över vanlig HTTP:

```text
http://localhost:18080
```

Det är korrekt för den lokala, produktionslika verifieringen i GitHub Actions och för utveckling. Det ska inte tolkas som att en extern produktionsinstallation bör exponeras utan TLS.

I en verklig miljö behöver HTTPS termineras någonstans framför eller i anslutning till Nginx, exempelvis genom en plattformsproxy, ingress, lastbalanserare eller separat reverse proxy.

Det är ytterligare ett exempel på att PWA-egenskaper påverkar mer än React-koden. TLS blir en del av förutsättningarna för frontendens webbläsarfunktioner.

## Cache headers och service worker måste samspela

När service worker används får cache-reglerna för några nyckelresurser extra stor betydelse.

TaskBoards Nginx-konfiguration innehåller i dag en särskild regel för den genererade service workern:

```nginx
location = /sw.js {
    add_header Cache-Control "no-cache";
    try_files $uri =404;
}
```

Syftet är att webbläsaren ska kunna kontrollera om service worker-scriptet har förändrats i stället för att låta en långlivad HTTP-cache fördröja uppdateringskontrollen. Service worker-livscykeln innehåller sin egen uppdateringsmekanik, och vi vill inte lägga en aggressiv servercache framför själva scriptet.

Samtidigt har TaskBoard ännu ingen explicit specialregel för `index.html`. Den levereras via den generella SPA-regeln:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

Det fungerar i referensimplementationen, men inför en skarp produktionsleverans bör cachepolicyn för HTML-dokumentet vara ett uttryckligt beslut. Hashade JS- och CSS-assets lämpar sig normalt väl för lång cache eftersom deras URL ändras när innehållet ändras. Ett stabilt dokumentnamn som `index.html` bör däremot inte få en cachepolicy som gör att klienten under lång tid blir kvar på en äldre referens till frontendens assets.

En vanlig princip är därför:

```text
Hashade assets   lång cache, eftersom URL ändras vid nytt innehåll
index.html       kort eller omvaliderad cache
sw.js            omvalideras så att ny service worker upptäcks
```

Den exakta Nginx-konfigurationen återkommer vi till när frontendimagen och leveransmodellen behandlas mer detaljerat. Här räcker det att konstatera att PWA-cache och HTTP-cache måste designas tillsammans.

## PWA:n ändrar inte API-arkitekturen

Det är lätt att tänka att en installerad PWA behöver en annan backendmodell än webbsidan. Så är det inte i TaskBoard.

När den installerade applikationen är online använder den fortfarande samma origin och samma relativa API-anrop:

```text
Installerad TaskBoard
        |
        | /api/tasks
        v
      Nginx
        |
        v
     Quarkus
        |
        v
   PostgreSQL
```

Manifest och service worker förändrar alltså inte API-kontraktet. Det är samma frontendbundle och samma backend. Det är en av styrkorna med PWA-modellen: installationen behöver inte skapa ett separat distributionsspår med en egen klientimplementation.

Det betyder också att same-origin-modellen från kapitel 2 fortsätter att gälla. Frontendkoden behöver inte veta om användaren öppnade TaskBoard i en vanlig webbläsarflik eller från en installerad appikon.

## Vad vi medvetet inte bygger

Referensimplementationen innehåller inte:

- push-notiser,
- bakgrundssynkronisering av TaskBoard-data,
- lokal affärsdatalagring för offlinebruk,
- konfliktlösning mellan lokala och serverbaserade ändringar,
- ett eget installationsflöde med `beforeinstallprompt`,
- ett eget uppdateringsdialogflöde.

Det är avsiktligt. Varje sådan funktion kan vara relevant i en viss produkt, men de behövs inte för att demonstrera den PWA-arkitektur boken vill åt.

En bra teknikstack är inte den som aktiverar flest funktioner. Den är den som gör de valda egenskaperna tydliga och begripliga.

## En användbar mental modell

Vi kan sammanfatta TaskBoards frontendleverans i fyra lager:

```text
React + TypeScript
        |
        v
Vite-produktionsbuild
        |
        v
PWA-manifest + service worker
        |
        v
Nginx + HTTPS i riktig driftsmiljö
```

React ansvarar för användarupplevelsen. Vite producerar statiska artefakter. PWA-lagret lägger till installation, service worker och cachebeteende. Nginx och den omgivande infrastrukturen ansvarar för att resurserna faktiskt levereras med rätt routing, cacheegenskaper och säker transport.

Det är först när de lagren fungerar tillsammans som frontenddelen är mer än en utvecklingsserver.

## Kapitlets viktigaste slutsatser

TaskBoards PWA-upplägg är medvetet litet men arkitektoniskt viktigt:

- Manifestet beskriver hur TaskBoard kan presenteras som installerbar applikation.
- Service workern genereras av `vite-plugin-pwa` och precachar frontendresurser.
- `registerType: 'autoUpdate'` ger ett automatiskt uppdateringsflöde som passar den lilla referensapplikationen.
- Affärsdata under `/api` runtime-cachas inte, så TaskBoard är online-first även om applikationsskalet kan finnas offline.
- HTTPS är en del av den riktiga driftsmiljön även om localhost kan användas över HTTP vid utveckling och CI.
- Cache headers för `sw.js`, HTML och hashade assets är en del av releasearkitekturen, inte bara en prestandaoptimering.
- PWA-installationen ändrar inte frontendens API-kontrakt eller same-origin-modell.

Nästa kapitel går innanför PWA-skalet och tittar på själva React- och TypeScript-implementationen: hur TaskBoard delar upp UI, state, formulär, API-lager och felhantering utan att låta transportdetaljer spridas genom komponenterna.
