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
    "frontend/vitest.config.ts",
    "frontend/src/App.test.tsx",
    "frontend/src/test/setup.ts",
    "frontend/nginx.conf",
    "frontend/Dockerfile",
    "frontend/src/App.tsx",
    "frontend/src/api.ts",
    "backend/pom.xml",
    "backend/Dockerfile",
    "backend/src/main/resources/application.properties",
    "backend/src/main/resources/db/migration/V1__create_task.sql",
    "backend/src/main/java/se/erland/taskboard/task/TaskResource.java",
    "backend/src/test/java/se/erland/taskboard/task/TaskResourceTest.java",
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
        "vitest": "4.1.10",
        "@testing-library/react": "16.3.2",
        "@testing-library/dom": "10.4.1",
        "@testing-library/user-event": "14.6.1",
        "@testing-library/jest-dom": "7.0.0",
        "jsdom": "30.0.1",
    }
    merged = package.get("dependencies", {}) | package.get("devDependencies", {})
    for dependency, version in expected_frontend.items():
        if merged.get(dependency) != version:
            fail(f"Fel version för {dependency}: {merged.get(dependency)!r}, väntat {version!r}")

    if package.get("scripts", {}).get("test") != "vitest run":
        fail("Frontendens test-script ska vara 'vitest run'")

    frontend_test = (ROOT / "frontend/src/App.test.tsx").read_text()
    for token in [
        "laddar och visar uppgifter från API:t",
        "skapar en uppgift från formuläret",
        "uppdaterar status",
        "visar API-fel",
        "userEvent.setup()",
        "vi.stubGlobal('fetch'",
    ]:
        if token not in frontend_test:
            fail(f"Frontendtestet saknar beteendekontroll: {token}")

    vitest_config = (ROOT / "frontend/vitest.config.ts").read_text()
    for token in ["environment: 'jsdom'", "setupFiles: './src/test/setup.ts'"]:
        if token not in vitest_config:
            fail(f"Vitest-konfigurationen saknar {token}")

    ET.parse(ROOT / "backend/pom.xml")
    pom = (ROOT / "backend/pom.xml").read_text()
    for token in [
        "<quarkus.platform.version>3.33.3.1</quarkus.platform.version>",
        "<maven.compiler.release>21</maven.compiler.release>",
        "<artifactId>quarkus-jdbc-postgresql</artifactId>",
        "<artifactId>quarkus-flyway</artifactId>",
        "<artifactId>flyway-database-postgresql</artifactId>",
        "<artifactId>quarkus-junit5</artifactId>",
        "<artifactId>rest-assured</artifactId>",
    ]:
        if token not in pom:
            fail(f"Backend-POM saknar {token}")


    app_properties = (ROOT / "backend/src/main/resources/application.properties").read_text()
    if "%test.quarkus.datasource.devservices.image-name=docker.io/library/postgres:18.4-alpine" not in app_properties:
        fail("Testprofilen ska låsa PostgreSQL Dev Services till postgres:18.4-alpine")

    backend_test = (ROOT / "backend/src/test/java/se/erland/taskboard/task/TaskResourceTest.java").read_text()
    for token in [
        "@QuarkusTest",
        'post("/api/tasks")',
        'get("/api/tasks")',
        'put("/api/tasks/{id}", id)',
        'delete("/api/tasks/{id}", id)',
        '"priority": "MEDIUM"',
        ".statusCode(400)",
        ".statusCode(404)",
    ]:
        if token not in backend_test:
            fail(f"Backendtestet saknar kontraktskontroll: {token}")


    workflow = (ROOT.parent.parent / ".github/workflows/04-test-reference-implementation.yml").read_text()
    for token in [
        "npm install --no-audit --no-fund",
        "actions/upload-artifact@v7",
        "taskboard-frontend-package-lock",
        "code/taskboard/frontend/package-lock.json",
    ]:
        if token not in workflow:
            fail(f"Referensworkflowen saknar reproducerbarhetsförberedelse: {token}")

    compose = (ROOT / "docker-compose.yml").read_text()
    for token in ["postgres:18.4-alpine", "condition: service_healthy", "taskboard-postgres:/var/lib/postgresql"]:
        if token not in compose:
            fail(f"docker-compose.yml saknar {token}")
    if "taskboard-postgres:/var/lib/postgresql/data" in compose:
        fail("PostgreSQL 18 ska montera den persistenta volymen på /var/lib/postgresql, inte /var/lib/postgresql/data")

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
