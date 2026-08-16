"""Shared API route manifest used to keep backend and frontend paths aligned."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTES_MANIFEST_PATH = REPO_ROOT / "shared" / "api-routes.json"


@lru_cache
def load_api_routes_manifest() -> dict[str, Any]:
    """Load the shared API route manifest from the repository root."""
    with ROUTES_MANIFEST_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def api_v1_prefix() -> str:
    """Return the canonical API v1 prefix."""
    prefix = load_api_routes_manifest()["apiV1Prefix"]
    if not isinstance(prefix, str) or not prefix.startswith("/"):
        raise ValueError("apiV1Prefix must be an absolute path.")
    return prefix.rstrip("/")


def route_path(section: str, name: str) -> str:
    """Return a relative route path from the shared manifest."""
    routes = load_api_routes_manifest()["routes"]
    section_routes = routes[section]
    path = section_routes[name]
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError(f"Route {section}.{name} must be an absolute path.")
    return path


def full_api_path(section: str, name: str, *, prefix: str | None = None) -> str:
    """Build the full API path including the version prefix."""
    resolved_prefix = (prefix or api_v1_prefix()).rstrip("/")
    return f"{resolved_prefix}{route_path(section, name)}"


def iter_manifest_paths(*, prefix: str | None = None) -> list[tuple[str, str]]:
    """Return (manifest key, full path) pairs for all declared routes."""
    resolved_prefix = prefix or api_v1_prefix()
    manifest = load_api_routes_manifest()
    pairs: list[tuple[str, str]] = []
    for section, section_routes in manifest["routes"].items():
        if not isinstance(section_routes, dict):
            continue
        for name in section_routes:
            pairs.append((f"{section}.{name}", full_api_path(section, name, prefix=resolved_prefix))])
    return pairs
