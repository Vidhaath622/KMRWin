#!/bin/zsh
# Double-click to run the read-only citizen-lookup test (does not add snapshots to the demo database).
# Stop the demo first: DuckDB allows only one process to open the database file.
cd "$(dirname "$0")/../backend"
uv run pytest -q -k citizen_lookup 2>&1 | tee .pytest_cache/last_run.txt
