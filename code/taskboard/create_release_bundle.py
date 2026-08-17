#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIGEST_REF = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[+-][0-9A-Za-z.-]+)?$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require_digest_ref(name: str, value: str) -> None:
    if not DIGEST_REF.fullmatch(value):
        raise ValueError(f"{name} måste vara en immutable image-referens med sha256-digest: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Skapa ett spårbart TaskBoard-releasepaket.")
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--web-image", required=True)
    parser.add_argument("--backend-image", required=True)
    parser.add_argument("--postgres-image", required=True)
    parser.add_argument("--node-version", required=True)
    parser.add_argument("--java-version", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    if not SEMVER.fullmatch(args.release_version):
        raise ValueError(f"Ogiltig releaseversion: {args.release_version}")
    if args.tag != f"taskboard-v{args.release_version}":
        raise ValueError(f"Taggen {args.tag!r} matchar inte releaseversionen {args.release_version!r}")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise ValueError("commit måste vara en fullständig 40-teckens Git-SHA")
    for name, value in [
        ("web-image", args.web_image),
        ("backend-image", args.backend_image),
        ("postgres-image", args.postgres_image),
    ]:
        require_digest_ref(name, value)

    output = Path(args.output_dir).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    shutil.copy2(ROOT / "docker-compose.release.yml", output / "docker-compose.release.yml")
    shutil.copy2(ROOT / "RELEASE.md", output / "README.md")

    release_env = output / "release.env"
    release_env.write_text(
        "\n".join(
            [
                f"TASKBOARD_WEB_IMAGE={args.web_image}",
                f"TASKBOARD_BACKEND_IMAGE={args.backend_image}",
                f"TASKBOARD_POSTGRES_IMAGE={args.postgres_image}",
                "TASKBOARD_PORT=8080",
                "POSTGRES_DB=taskboard",
                "POSTGRES_USER=taskboard",
                "POSTGRES_PASSWORD=CHANGE_ME_BEFORE_DEPLOYMENT",
                "",
            ]
        ),
        encoding="utf-8",
    )

    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    manifest = {
        "schemaVersion": 1,
        "release": args.release_version,
        "tag": args.tag,
        "repository": args.repository,
        "gitCommit": args.commit,
        "githubActionsRunId": str(args.run_id),
        "generatedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "images": {
            "web": args.web_image,
            "backend": args.backend_image,
            "postgres": args.postgres_image,
        },
        "toolchain": {
            "node": args.node_version,
            "java": args.java_version,
            "frontendPackageVersion": package.get("version"),
        },
        "verification": {
            "frontend": "npm ci --no-audit --no-fund && npm run test && npm run build",
            "backend": "mvn -B --no-transfer-progress verify",
            "compose": "docker compose up -d --wait --wait-timeout 120",
            "smokePath": "Nginx -> Quarkus -> PostgreSQL",
        },
        "sourceChecksums": {
            "frontend/package-lock.json": sha256(ROOT / "frontend/package-lock.json"),
            "frontend/Dockerfile": sha256(ROOT / "frontend/Dockerfile"),
            "backend/Dockerfile": sha256(ROOT / "backend/Dockerfile"),
            "docker-compose.yml": sha256(ROOT / "docker-compose.yml"),
            "docker-compose.release.yml": sha256(ROOT / "docker-compose.release.yml"),
        },
    }

    manifest_path = output / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_targets = [
        output / "README.md",
        output / "docker-compose.release.yml",
        output / "release.env",
        manifest_path,
    ]
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_targets),
        encoding="utf-8",
    )

    print(f"OK: releasepaket skapat i {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
