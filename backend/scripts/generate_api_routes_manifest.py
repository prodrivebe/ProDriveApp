"""Generate shared/api-routes.json from the FastAPI OpenAPI schema."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from app.config.settings import Settings
from app.main import create_app


def _build_manifest() -> dict[str, object]:
    settings = Settings(
        environment="test",
        jwt_secret_key="test-secret-key-with-32-byte-minimum-length",
        database_url_override="sqlite+pysqlite:///:memory:",
    )
    app = create_app(settings)
    paths = sorted(path for path in app.openapi()["paths"] if path.startswith("/api/v1/"))

    routes: dict[str, dict[str, str]] = {}
    for full_path in paths:
        relative_path = full_path.removeprefix("/api/v1")
        segments = [segment for segment in relative_path.split("/") if segment]
        if not segments:
            continue

        section = re.sub(r"[^a-z0-9_]", "_", segments[0].lower())
        if len(segments) == 1:
            route_name = "root"
        else:
            name_parts = [re.sub(r"[{}]", "", segment) for segment in segments[1:]]
            route_name = "_".join(name_parts) or "root"
            route_name = re.sub(r"[^a-z0-9_]", "_", route_name.lower())

        section_routes = routes.setdefault(section, {})
        base_name = route_name
        counter = 2
        while route_name in section_routes:
            route_name = f"{base_name}_{counter}"
            counter += 1
        section_routes[route_name] = relative_path

    return {"apiV1Prefix": "/api/v1", "routes": routes}


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    default_output = backend_root.parent / "shared" / "api-routes.json"
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else default_output
    manifest = _build_manifest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote manifest with {sum(len(v) for v in manifest['routes'].values())} routes to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
