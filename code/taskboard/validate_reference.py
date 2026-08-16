#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED = [
    ".env.example",
    "docker-compose.yml",
    "STACK-VERSIONS.md",
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/nginx.conf",
    "frontend/Dockerfile",
    "frontend/src/App.tsx",
    "frontend/src/api.ts",
    "backend/pom.xml",
    "backend/Dockerfile",
    "backend/src/main/resources/application.properties",
    "backend/src/main/resources/db/migration/V1__create_task.sql",
    "backend/src/main/java/se/erland/taskboard/task/TaskResource.java",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    if missing:
        fail("Saknade referensfiler: " + ", ".join(missing))

    package = json.loads((ROOT / "frontend/package.json").read_text())
    expected_frontend = {
        "react": "19.2.7",
        "react-dom": "19.2.7",
        "vite": "8.2.1",
        "typescript": "6.0.3",
        "vite-plugin-pwa": "1.3.0",
    }
    merged = package.get("dependencies", {}) | package.get("devDependencies", {})
    for dependency, version in expected_frontend.items():
        if merged.get(dependency) != version:
            fail(f"Fel version för {dependency}: {merged.get(dependency)!r}, väntat {version!r}")

    ET.parse(ROOT / "backend/pom.xml")
    pom = (ROOT / "backend/pom.xml").read_text()
    for token in [
        "<quarkus.platform.version>3.33.3.1</quarkus.platform.version>",
        "<maven.compiler.release>21</maven.compiler.release>",
        "<artifactId>quarkus-jdbc-postgresql</artifactId>",
        "<artifactId>quarkus-flyway</artifactId>",
        "<artifactId>flyway-database-postgresql</artifactId>",
    ]:
        if token not in pom:
            fail(f"Backend-POM saknar {token}")

    compose = (ROOT / "docker-compose.yml").read_text()
    for token in ["postgres:18.4-alpine", "condition: service_healthy", "taskboard-postgres"]:
        if token not in compose:
            fail(f"docker-compose.yml saknar {token}")

    nginx = (ROOT / "frontend/nginx.conf").read_text()
    for token in ["location /api/", "proxy_pass http://backend:8080", "try_files $uri $uri/ /index.html"]:
        if token not in nginx:
            fail(f"nginx.conf saknar {token}")

    migration = (ROOT / "backend/src/main/resources/db/migration/V1__create_task.sql").read_text()
    if "CREATE TABLE task_item" not in migration:
        fail("Flyway-migrationen skapar inte task_item")

    print("OK: TaskBoard-referensimplementationens statiska kontrakt är konsekvent.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"FEL: {exc}", file=sys.stderr)
        raise SystemExit(1)
