# TaskBoard releasepaket

Releasepaketet är avsett för körning av de images som byggdes, smoke-testades och publicerades av TaskBoards releaseworkflow. Images anges med registry-digests i `release.env`.

## Start

1. Kontrollera `release-manifest.json` och `SHA256SUMS.txt`.
2. Kopiera `release.env` till en lokal fil och byt `POSTGRES_PASSWORD=CHANGE_ME_BEFORE_DEPLOYMENT` till ett riktigt hemligt värde.
3. Logga in mot `ghcr.io` om paketens synlighet kräver det.
4. Starta tjänsten:

```bash
docker compose --env-file release.env -f docker-compose.release.yml up -d --wait
```

Öppna därefter `http://localhost:8080`, eller den port som anges med `TASKBOARD_PORT`.

## Stoppa

```bash
docker compose --env-file release.env -f docker-compose.release.yml down
```

Lägg endast till `-v` om även den persistenta PostgreSQL-volymen avsiktligt ska tas bort.

## Verifiera paketets filer

På en miljö med `sha256sum`:

```bash
sha256sum -c SHA256SUMS.txt
```

Manifestet innehåller releaseversion, Git commit, GitHub Actions-run, image-referenser med digest samt checksummor för centrala käll- och leveransfiler.
