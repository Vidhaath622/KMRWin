#!/usr/bin/env python3
"""Exports FastAPI OpenAPI schema to `shared/openapi.json` for Frontend & Peer-AGY sync."""

from __future__ import annotations

import json
import pathlib
import sys

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402


def main() -> None:
    shared_dir = BACKEND_ROOT.parent / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    target = shared_dir / "openapi.json"
    schema = app.openapi()
    target.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Exported OpenAPI schema ({len(schema.get('paths', {}))} paths) -> {target}")


if __name__ == "__main__":
    main()
