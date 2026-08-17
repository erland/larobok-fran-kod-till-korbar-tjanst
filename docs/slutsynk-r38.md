# Slutlig synkronisering och faktagranskning – revision 38

## Syfte

Denna revision jämför hela bokmanuset med den verifierade TaskBoard-referensimplementationen efter att test- och leveransmodellen färdigställts och releaseworkflowen körts igenom i GitHub Actions.

## Verifierad baslinje

- Referensimplementation: `code/taskboard/`.
- Kanonisk CI: `.github/workflows/04-test-reference-implementation.yml`.
- Releaseworkflow: `.github/workflows/05-release-reference-implementation.yml`.
- Runtime-verifierad releasekörning: GitHub Actions run `32049657728`, job `95445697330`.
- Releasekörningen verifierade frontendtester, backendtester mot PostgreSQL Dev Services, Compose, byggda release-images, full-stack smoke test av exakt de images som sedan publicerades, GHCR-push, digestinsamling, deploymentbundle och GitHub Release.

## Korrigeringar i manuset

1. Inledning och kapitel 1 beskriver nu även frontend- och backendtesterna, inte bara build och full-stack smoke test.
2. Kapitel 3:s förenklade projektträd innehåller nu de centrala test-, lock- och releasefiler som faktiskt finns i referensimplementationen.
3. Kapitel 5 påstod fortfarande att automatiserade frontendtester saknades. Detta var inaktuellt och är korrigerat; den aktuella Vitest/React Testing Library-sviten beskrivs nu som implementerad.
4. Kapitel 10 beskriver nu testlagren före full-stack-smoke-testet och deras olika roller.
5. Kapitel 12:s workflowordning är synkroniserad med faktisk CI: `npm ci`, frontendtest + build, Maven `verify`, Compose och smoke test.
6. Kapitel 13 kopplar image-verifieringen till releaseworkflowens princip att exakt verifierade images publiceras utan rebuild.
7. Kapitel 16 och 17 markerar att releasekedjan inte bara finns i kod utan är runtime-verifierad genom GHCR-publicering och GitHub Release.

## Granskade gränser som fortfarande är avsiktliga

Följande ska fortsatt beskrivas som ej implementerat eller som produktionshärdning utanför bokens referensmål:

- autentisering och auktorisering,
- TLS-terminering och explicit trusted-proxy-policy i TaskBoard-stacken,
- Compose secrets eller annan skarp secrets-hantering,
- automatiserad backup/restore och full observability,
- explicit bitreproducerbar Maven-build,
- attestering/signering och eventuell SBOM,
- horisontell skalning och större plattformsorkestrering.

Dessa avgränsningar motsäger inte den verifierade test-/leveransmodellen.

## Resultat

Efter revisionen finns inga kända påståenden i huvudmanuset som beskriver den tidigare test-/leveransmodellen som aktuell. Boken skiljer fortsatt mellan verifierad referensimplementation och framtida produktionshärdning.
