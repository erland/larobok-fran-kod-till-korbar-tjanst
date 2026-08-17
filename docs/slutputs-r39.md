# Slutputs inför publicering – revision 39

## Syfte

Revisionen gör en sista redaktionell och publiceringsmässig genomgång efter den tekniska slutsynkningen i revision 38. Referensimplementationens beteende ändras inte.

## Genomförda korrigeringar

- Bokmetadata uppdaterad till version 1.0 och datum 2026-08-17.
- Kapitel 16 beskriver nu `release-manifest.json` som faktisk del av den verifierade releasekedjan och visar ett förenklat utdrag som följer den verkliga JSON-modellen.
- Kapitel 17 skiljer mellan en redan verifierad teknisk release och de krav som återstår inför verklig produktionssättning.
- Några språkliga sammansättningar och anglicismer har putsats utan att ändra teknisk innebörd.
- Källpolicyn har uppdaterats så att digest-strategin beskrivs som implementerad, inte framtida.
- Publiceringskontroll av centrala tidskänsliga versionsval gjord 2026-08-17 mot officiella källor för React, Quarkus och PostgreSQL.
- Källförteckningen kompletterad med dessa publiceringstidskällor.
- Faktakontroll och kvalitetschecklista markerar vad som nu är klart respektive vad som återstår som visuell exportkontroll/omslagsbeslut.

## Avsiktligt kvar inför export

- EPUB/PDF behöver fortfarande byggas och visuellt granskas.
- Omslagsbild är ett separat öppet publiceringsbeslut.
- Produktionshärdning av TaskBoard (auth, TLS, secrets, backup/restore, observability och eventuell supply-chain-attestering) ligger fortsatt utanför referensmålet.
