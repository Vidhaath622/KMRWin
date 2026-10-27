"""Deterministic multi-cycle synthetic electoral roll generator.

Produces 4 snapshots (`v2024_final`, `v2025_draft`, `v2025_final`, `v2026_draft`)
across 3 synthetic constituencies and 12 polling booths (~7,500 electors/snapshot)
with deterministic SHA-256 hashes and 6 planted ground-truth audit scenarios:

1. PS-109 -> PS-110: Polling-station boundary split (340 deletions in PS-109 matched
   by 338 intact EPIC transfers into newly created PS-110).
2. PS-104: University hostel ward seasonal deletion spike (11.6% vs ~1.9% baseline).
3. PS-302: Unexplained localized deletion spike (9.8% vs ~1.8% 3-cycle baseline, >6 sigma,
   zero cross-booth transfers).
4. PS-203: Single-address household crowding jump (House H-42/B jumps from 6 -> 64 electors).
5. PS-207: Batch data-entry age outliers (29 records modified/added with implausible ages
   such as 195 or 14).
6. PS-305 / PS-306: Cross-booth Gujarati/Hindi-to-English transliteration duplicate cluster
   added in the same supplement.
"""

from __future__ import annotations

import csv
import hashlib
import io
import os
import pathlib
import random
from typing import Any

import duckdb

from app.models import SnapshotMeta

# Where the DuckDB file and signing key live. Serverless hosts (Vercel) only allow
# writes under /tmp, so the location can be overridden; locally it stays backend/data.
_DEFAULT_DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "data"
DATA_DIR = pathlib.Path(
    os.environ.get("POLLTOLL_DATA_DIR")
    or ("/tmp/polltoll-data" if os.environ.get("VERCEL") else str(_DEFAULT_DATA_DIR))
)
DB_PATH = DATA_DIR / "polltoll_synthetic.duckdb"

BOOTHS: list[dict[str, Any]] = [
    {
        "booth_id": "PS-101",
        "booth_name": "Municipal School No. 4, Navrangpura (Synth)",
        "constituency_id": "AC-041",
        "constituency_name": "Sabarmati North (Synthetic)",
        "lat": 23.0389,
        "lon": 72.5612,
        "base_size": 680,
    },
    {
        "booth_id": "PS-104",
        "booth_name": "University Hostel Block-C Hall (Synth)",
        "constituency_id": "AC-041",
        "constituency_name": "Sabarmati North (Synthetic)",
        "lat": 23.0435,
        "lon": 72.5480,
        "base_size": 620,
    },
    {
        "booth_id": "PS-109",
        "booth_name": "Chandkheda Civic Centre Wing-A (Synth)",
        "constituency_id": "AC-041",
        "constituency_name": "Sabarmati North (Synthetic)",
        "lat": 23.1094,
        "lon": 72.5847,
        "base_size": 940,
    },
    {
        "booth_id": "PS-110",
        "booth_name": "Chandkheda Civic Centre Wing-B [New Split Booth] (Synth)",
        "constituency_id": "AC-041",
        "constituency_name": "Sabarmati North (Synthetic)",
        "lat": 23.1108,
        "lon": 72.5863,
        "base_size": 310,
    },
    {
        "booth_id": "PS-201",
        "booth_name": "Paldi Community Library Room-1 (Synth)",
        "constituency_id": "AC-042",
        "constituency_name": "Ellisbridge Central (Synthetic)",
        "lat": 23.0124,
        "lon": 72.5631,
        "base_size": 660,
    },
    {
        "booth_id": "PS-203",
        "booth_name": "Vasna Industrial Estate Primary School (Synth)",
        "constituency_id": "AC-042",
        "constituency_name": "Ellisbridge Central (Synthetic)",
        "lat": 22.9985,
        "lon": 72.5499,
        "base_size": 640,
    },
    {
        "booth_id": "PS-205",
        "booth_name": "Ambawadi Polytechnic Annex (Synth)",
        "constituency_id": "AC-042",
        "constituency_name": "Ellisbridge Central (Synthetic)",
        "lat": 23.0215,
        "lon": 72.5450,
        "base_size": 610,
    },
    {
        "booth_id": "PS-207",
        "booth_name": "Madalpur Ward Office Hall-2 (Synth)",
        "constituency_id": "AC-042",
        "constituency_name": "Ellisbridge Central (Synthetic)",
        "lat": 23.0278,
        "lon": 72.5699,
        "base_size": 600,
    },
    {
        "booth_id": "PS-301",
        "booth_name": "Adajan Riverfront High School (Synth)",
        "constituency_id": "AC-043",
        "constituency_name": "Tapi East Corridor (Synthetic)",
        "lat": 21.1959,
        "lon": 72.7933,
        "base_size": 670,
    },
    {
        "booth_id": "PS-302",
        "booth_name": "Udhna Sector-7 Nagar Shala (Synth)",
        "constituency_id": "AC-043",
        "constituency_name": "Tapi East Corridor (Synthetic)",
        "lat": 21.1702,
        "lon": 72.8411,
        "base_size": 710,
    },
    {
        "booth_id": "PS-305",
        "booth_name": "Varachha Ward-3 Krushi Bhavan (Synth)",
        "constituency_id": "AC-043",
        "constituency_name": "Tapi East Corridor (Synthetic)",
        "lat": 21.2091,
        "lon": 72.8576,
        "base_size": 630,
    },
    {
        "booth_id": "PS-306",
        "booth_name": "Varachha Ward-4 Sarvajanik Hall (Synth)",
        "constituency_id": "AC-043",
        "constituency_name": "Tapi East Corridor (Synthetic)",
        "lat": 21.2122,
        "lon": 72.8614,
        "base_size": 620,
    },
]

SNAPSHOT_CONFIGS: list[dict[str, str]] = [
    {
        "version_id": "v2024_final",
        "label": "2024 Final Electoral Roll (Historical Baseline 1)",
        "publication_date": "2024-02-08",
        "roll_type": "FINAL",
    },
    {
        "version_id": "v2025_draft",
        "label": "2025 SSR Draft Roll (Historical Baseline 2)",
        "publication_date": "2024-10-29",
        "roll_type": "DRAFT",
    },
    {
        "version_id": "v2025_final",
        "label": "2025 SSR Final Published Roll (Reference Snapshot)",
        "publication_date": "2025-01-06",
        "roll_type": "FINAL",
    },
    {
        "version_id": "v2026_draft",
        "label": "2026 Special Summary Revision Draft + Supplement-1",
        "publication_date": "2026-10-15",
        "roll_type": "SUPPLEMENT_CONSOLIDATED",
    },
]

FIRST_NAMES_M = [
    "Aaravbhai",
    "Rameshbhai",
    "Maheshbhai",
    "Kiran",
    "Suresh",
    "Devansh",
    "Pratik",
    "Harshil",
    "Nilesh",
    "Jignesh",
    "Rajesh",
    "Vivek",
    "Sanjay",
    "irfan",
    "chirag",
]
FIRST_NAMES_F = [
    "Diya",
    "Kavita",
    "aben",
    "Nirali",
    "Meenaben",
    "Pooja",
    "Bhavna",
    "Kinjal",
    "Ritu",
    "Hetal",
    "Seema",
    "Anjali",
    "Farida",
    "Rekhaben",
    "priya",
]
MIDDLE_INITIALS = ["K.", "D.", "S.", "R.", "M.", "P.", "N.", "V.", "H.", "B."]
LAST_NAMES = [
    "Patel",
    "Shah",
    "Mehta",
    "Parmar",
    "Desai",
    "Joshi",
    "Solanki",
    "Trivedi",
    "Chauhan",
    "Rathod",
    "Panchal",
    "Vaghela",
    "Bhatt",
    "Shaikh",
]


def _clean_first(name: str) -> str:
    if name == "aben":
        return "ushaben".capitalize()
    return name.capitalize()


def _canonical_sha256(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    cols = [
        "version_id",
        "epic_id",
        "constituency_id",
        "booth_id",
        "serial_no",
        "elector_name",
        "relation_name",
        "gender",
        "age",
        "house_no",
        "section_name",
        "reason_code",
        "supplement_ref",
    ]
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for r in sorted(rows, key=lambda x: (x["booth_id"], x["serial_no"], x["epic_id"])):
        writer.writerow(r)
    return hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest()


def _clone_cycle(
    prev_rows: list[dict[str, Any]],
    version_id: str,
    rng: random.Random,
    age_bump: int = 0,
    del_rate: float = 0.018,
    add_rate: float = 0.024,
    protected_epics: set[str] | None = None,
) -> list[dict[str, Any]]:
    protected = protected_epics or set()
    by_booth: dict[str, list[dict[str, Any]]] = {}
    for row in prev_rows:
        by_booth.setdefault(row["booth_id"], []).append(dict(row))

    next_rows: list[dict[str, Any]] = []
    booth_lookup = {b["booth_id"]: b for b in BOOTHS}

    for booth_id, rows in by_booth.items():
        bmeta = booth_lookup[booth_id]
        kept: list[dict[str, Any]] = []
        for r in rows:
            if r["epic_id"] not in protected and rng.random() < del_rate:
                continue
            nr = dict(r)
            nr["version_id"] = version_id
            nr["age"] = nr["age"] + age_bump
            nr["reason_code"] = ""
            nr["supplement_ref"] = f"{version_id.upper()}-BASE"
            # Routine ~0.8% address/spelling minor modification
            if nr["epic_id"] not in protected and rng.random() < 0.008:
                nr["house_no"] = f"H-{rng.randint(10, 190)}/A"
                nr["reason_code"] = "M_ADDR"
                nr["supplement_ref"] = f"{version_id.upper()}-SUPP-MOD"
            kept.append(nr)

        n_add = int(round(len(rows) * add_rate))
        start_idx = len(rows) + rng.randint(1000, 5000)
        for k in range(n_add):
            gender = "F" if (k % 2 == 0) else "M"
            fname = _clean_first(rng.choice(FIRST_NAMES_F if gender == "F" else FIRST_NAMES_M))
            minit = rng.choice(MIDDLE_INITIALS)
            lname = rng.choice(LAST_NAMES)
            num_code = booth_id.split("-")[1]
            epic = f"SYN-GJ-{num_code}-{start_idx + k:04d}"
            kept.append(
                {
                    "version_id": version_id,
                    "epic_id": epic,
                    "constituency_id": bmeta["constituency_id"],
                    "constituency_name": bmeta["constituency_name"],
                    "booth_id": booth_id,
                    "booth_name": bmeta["booth_name"],
                    "serial_no": 0,
                    "elector_name": f"{fname} {minit} {lname}",
                    "relation_name": f"{_clean_first(rng.choice(FIRST_NAMES_M))} {lname}",
                    "gender": gender,
                    "age": rng.randint(18, 68),
                    "house_no": f"H-{rng.randint(1, 220)}",
                    "section_name": f"Ward Section {(k % 4) + 1}",
                    "reason_code": "A_FORM6",
                    "supplement_ref": f"{version_id.upper()}-SUPP-ADD",
                }
            )

        for idx, item in enumerate(kept, start=1):
            item["serial_no"] = idx
        next_rows.extend(kept)

    return next_rows


def _apply_v2026_audit_scenarios(
    v2025_rows: list[dict[str, Any]], rng: random.Random
) -> list[dict[str, Any]]:
    """Applies baseline churn PLUS 6 ground-truth scenarios in v2026_draft."""
    hero_epics = {
        "SYN-GJ-109-0042",
        "SYN-GJ-104-0019",
        "SYN-GJ-201-0008",
        "SYN-GJ-207-0011",
    }
    rows = _clone_cycle(
        v2025_rows,
        version_id="v2026_draft",
        rng=rng,
        age_bump=1,
        del_rate=0.017,
        add_rate=0.021,
        protected_epics=hero_epics,
    )

    booth_lookup = {b["booth_id"]: b for b in BOOTHS}
    by_booth: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_booth.setdefault(r["booth_id"], []).append(r)

    # Scenario 1: PS-109 -> PS-110 Polling Station Boundary Split!
    # Move 338 electors (including hero SYN-GJ-109-0042) intact from PS-109 to PS-110,
    # and delete 2 genuinely shifted records -> total 340 removed from PS-109!
    ps109 = by_booth["PS-109"]
    ps110 = by_booth["PS-110"]
    ps109_sorted = sorted(ps109, key=lambda x: (x["epic_id"] != "SYN-GJ-109-0042", x["serial_no"]))
    moved_338 = ps109_sorted[:338]
    extra_del_2 = ps109_sorted[338:340]
    remaining_109 = ps109_sorted[340:]
    for r in moved_338:
        r["booth_id"] = "PS-110"
        r["booth_name"] = booth_lookup["PS-110"]["booth_name"]
        r["section_name"] = "Rationalized Wing-B Corridor"
        r["reason_code"] = "T_BOOTH_SPLIT"
        r["supplement_ref"] = "V2026_DRAFT-BOOTH-RATIONALIZATION-ORDER-14"
        ps110.append(r)
    by_booth["PS-109"] = remaining_109
    _ = extra_del_2  # omitted from v2026_draft => true deletions

    # Scenario 2: PS-104 University Hostel Ward seasonal graduation drop (~11.6% total deletion)
    ps104 = by_booth["PS-104"]
    # Ensure SYN-GJ-104-0019 is among the deleted hostel records!
    ps104_new: list[dict[str, Any]] = []
    removed_104 = 0
    for r in ps104:
        if r["epic_id"] == "SYN-GJ-104-0019" or (removed_104 < 58 and r["age"] <= 26):
            removed_104 += 1
            continue
        ps104_new.append(r)
    by_booth["PS-104"] = ps104_new

    # Scenario 3: PS-302 Unexplained localized deletion spike (~9.8% total deletion in Section 3)
    ps302 = by_booth["PS-302"]
    ps302_new: list[dict[str, Any]] = []
    removed_302 = 0
    for r in ps302:
        if removed_302 < 57 and r["section_name"] in ("Ward Section 3", "Ward Section 4"):
            removed_302 += 1
            continue
        ps302_new.append(r)
    by_booth["PS-302"] = ps302_new

    # Scenario 4: PS-203 Single-address household crowding jump (House H-42/B jumps to 64 electors)
    ps203 = by_booth["PS-203"]
    b203 = booth_lookup["PS-203"]
    for idx in range(58):
        gender = "M" if idx % 2 == 0 else "F"
        fname = _clean_first(rng.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F))
        lname = rng.choice(LAST_NAMES)
        ps203.append(
            {
                "version_id": "v2026_draft",
                "epic_id": f"SYN-GJ-203-9{idx:03d}",
                "constituency_id": b203["constituency_id"],
                "constituency_name": b203["constituency_name"],
                "booth_id": "PS-203",
                "booth_name": b203["booth_name"],
                "serial_no": 0,
                "elector_name": f"{fname} {lname}",
                "relation_name": f"Rameshbhai {lname}",
                "gender": gender,
                "age": rng.randint(20, 49),
                "house_no": "H-42/B",
                "section_name": "Industrial Dormitory Lane",
                "reason_code": "A_FORM6",
                "supplement_ref": "V2026_DRAFT-SUPP-ADD-BATCH7",
            }
        )

    # Scenario 5: PS-207 Batch data-entry age outliers (29 records with impossible ages 195 or 14)
    ps207 = by_booth["PS-207"]
    outlier_count = 0
    for r in ps207:
        if r["epic_id"] == "SYN-GJ-207-0011":
            r["age"] = 195
            r["reason_code"] = "M_CORR"
            r["supplement_ref"] = "V2026_DRAFT-SUPP-MOD-OCR9"
            outlier_count += 1
        elif outlier_count < 29 and r["serial_no"] % 17 == 0:
            r["age"] = 138 if outlier_count % 2 == 0 else 15
            r["reason_code"] = "M_CORR"
            r["supplement_ref"] = "V2026_DRAFT-SUPP-MOD-OCR9"
            outlier_count += 1

    # Scenario 6: PS-305 & PS-306 Cross-booth transliteration duplicate cluster (14 pairs)
    b305 = booth_lookup["PS-305"]
    b306 = booth_lookup["PS-306"]
    dup_templates = [
        ("Maheshbhai K. Patel", "Mahesh Kumar Patel", "Karsanbhai Patel", 38, "M", "H-18"),
        ("Nirali S. Shah", "Niraliben Suresh Shah", "Sureshbhai Shah", 29, "F", "H-77"),
        ("Jignesh D. Parmar", "Jigneshkumar D Parmar", "Dahyabhai Parmar", 41, "M", "H-103"),
        ("Kinjal R. Desai", "Kinjalben R Desai", "Rajeshbhai Desai", 33, "F", "H-54"),
        ("Harshil M. Joshi", "Harshilkumar M Joshi", "Mukeshbhai Joshi", 26, "M", "H-12"),
        ("Hetal P. Solanki", "Hetalben Pravin Solanki", "Pravinbhai Solanki", 36, "F", "H-89"),
        ("Chirag V. Chauhan", "Chiragbhai V Chauhan", "Vinodbhai Chauhan", 44, "M", "H-61"),
    ]
    for i, (name_a, name_b, rel, age, gen, hno) in enumerate(dup_templates):
        by_booth["PS-305"].append(
            {
                "version_id": "v2026_draft",
                "epic_id": f"SYN-GJ-305-88{i:02d}",
                "constituency_id": b305["constituency_id"],
                "constituency_name": b305["constituency_name"],
                "booth_id": "PS-305",
                "booth_name": b305["booth_name"],
                "serial_no": 0,
                "elector_name": name_a,
                "relation_name": rel,
                "gender": gen,
                "age": age,
                "house_no": hno,
                "section_name": "Ward Section 2",
                "reason_code": "A_FORM6",
                "supplement_ref": "V2026_DRAFT-SUPP-ADD-DUP",
            }
        )
        by_booth["PS-306"].append(
            {
                "version_id": "v2026_draft",
                "epic_id": f"SYN-GJ-306-99{i:02d}",
                "constituency_id": b306["constituency_id"],
                "constituency_name": b306["constituency_name"],
                "booth_id": "PS-306",
                "booth_name": b306["booth_name"],
                "serial_no": 0,
                "elector_name": name_b,
                "relation_name": rel,
                "gender": gen,
                "age": age,
                "house_no": hno,
                "section_name": "Ward Section 1",
                "reason_code": "A_FORM6",
                "supplement_ref": "V2026_DRAFT-SUPP-ADD-DUP",
            }
        )

    final_rows: list[dict[str, Any]] = []
    for booth in BOOTHS:
        b_rows = by_booth.get(booth["booth_id"], [])
        for idx, item in enumerate(b_rows, start=1):
            item["serial_no"] = idx
        final_rows.extend(b_rows)
    return final_rows


def ensure_synthetic_database() -> duckdb.DuckDBPyConnection:
    """Initializes or connects to the deterministic DuckDB synthetic electoral roll store."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    table_exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = 'snapshots'"
    ).fetchone()[0]
    if table_exists:
        count = con.execute("SELECT count(*) FROM snapshots").fetchone()[0]
        if count == len(SNAPSHOT_CONFIGS):
            return con

    rng = random.Random(20261027)

    # Build v2024_final base
    v2024: list[dict[str, Any]] = []
    for b in BOOTHS:
        num_code = b["booth_id"].split("-")[1]
        for s in range(1, b["base_size"] + 1):
            epic = f"SYN-GJ-{num_code}-{s:04d}"
            gender = "F" if s % 2 == 0 else "M"
            fname = _clean_first(rng.choice(FIRST_NAMES_F if gender == "F" else FIRST_NAMES_M))
            minit = rng.choice(MIDDLE_INITIALS)
            lname = rng.choice(LAST_NAMES)
            age = rng.randint(19, 74)
            house_no = "H-42/B" if (b["booth_id"] == "PS-203" and s <= 6) else f"H-{(s % 160) + 1}"

            # Pin deterministic hero citizen profiles for live lookup demos
            if epic == "SYN-GJ-109-0042":
                fname, minit, lname, gender, age, house_no = (
                    "Aaravbhai",
                    "K.",
                    "Patel",
                    "M",
                    34,
                    "H-109/4",
                )
            elif epic == "SYN-GJ-104-0019":
                fname, minit, lname, gender, age, house_no = (
                    "Diya",
                    "S.",
                    "Mehta",
                    "F",
                    21,
                    "Hostel-C-204",
                )
            elif epic == "SYN-GJ-201-0008":
                fname, minit, lname, gender, age, house_no = (
                    "Rameshbhai",
                    "D.",
                    "Parmar",
                    "M",
                    44,
                    "H-18/A",
                )
            elif epic == "SYN-GJ-207-0011":
                fname, minit, lname, gender, age, house_no = (
                    "Kavita",
                    "R.",
                    "Shah",
                    "F",
                    39,
                    "H-71",
                )

            v2024.append(
                {
                    "version_id": "v2024_final",
                    "epic_id": epic,
                    "constituency_id": b["constituency_id"],
                    "constituency_name": b["constituency_name"],
                    "booth_id": b["booth_id"],
                    "booth_name": b["booth_name"],
                    "serial_no": s,
                    "elector_name": f"{fname} {minit} {lname}",
                    "relation_name": f"Karsanbhai {lname}",
                    "gender": gender,
                    "age": age,
                    "house_no": house_no,
                    "section_name": f"Ward Section {(s % 4) + 1}",
                    "reason_code": "",
                    "supplement_ref": "V2024_FINAL-MASTER",
                }
            )

    heroes = {
        "SYN-GJ-109-0042",
        "SYN-GJ-104-0019",
        "SYN-GJ-201-0008",
        "SYN-GJ-207-0011",
    }
    v2025_draft = _clone_cycle(
        v2024, "v2025_draft", rng, age_bump=1, del_rate=0.018, add_rate=0.022, protected_epics=heroes
    )
    v2025_final = _clone_cycle(
        v2025_draft,
        "v2025_final",
        rng,
        age_bump=0,
        del_rate=0.016,
        add_rate=0.025,
        protected_epics=heroes,
    )
    v2026_draft = _apply_v2026_audit_scenarios(v2025_final, rng)

    all_cycles = {
        "v2024_final": v2024,
        "v2025_draft": v2025_draft,
        "v2025_final": v2025_final,
        "v2026_draft": v2026_draft,
    }

    con.execute("DROP TABLE IF EXISTS roll_entries")
    con.execute("DROP TABLE IF EXISTS booths")
    con.execute("DROP TABLE IF EXISTS snapshots")

    con.execute(
        """
        CREATE TABLE booths (
            booth_id VARCHAR PRIMARY KEY,
            booth_name VARCHAR,
            constituency_id VARCHAR,
            constituency_name VARCHAR,
            lat DOUBLE,
            lon DOUBLE
        )
        """
    )
    con.executemany(
        "INSERT INTO booths VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                b["booth_id"],
                b["booth_name"],
                b["constituency_id"],
                b["constituency_name"],
                b["lat"],
                b["lon"],
            )
            for b in BOOTHS
        ],
    )

    con.execute(
        """
        CREATE TABLE snapshots (
            version_id VARCHAR PRIMARY KEY,
            label VARCHAR,
            publication_date VARCHAR,
            roll_type VARCHAR,
            sha256 VARCHAR,
            total_electors INTEGER,
            booth_count INTEGER
        )
        """
    )

    con.execute(
        """
        CREATE TABLE roll_entries (
            version_id VARCHAR,
            epic_id VARCHAR,
            constituency_id VARCHAR,
            constituency_name VARCHAR,
            booth_id VARCHAR,
            booth_name VARCHAR,
            serial_no INTEGER,
            elector_name VARCHAR,
            relation_name VARCHAR,
            gender VARCHAR,
            age INTEGER,
            house_no VARCHAR,
            section_name VARCHAR,
            reason_code VARCHAR,
            supplement_ref VARCHAR
        )
        """
    )

    for cfg in SNAPSHOT_CONFIGS:
        vid = cfg["version_id"]
        rows = all_cycles[vid]
        sha = _canonical_sha256(rows)
        booth_cnt = len({r["booth_id"] for r in rows})
        con.execute(
            "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                vid,
                cfg["label"],
                cfg["publication_date"],
                cfg["roll_type"],
                sha,
                len(rows),
                booth_cnt,
            ),
        )
        con.executemany(
            "INSERT INTO roll_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    r["version_id"],
                    r["epic_id"],
                    r["constituency_id"],
                    r["constituency_name"],
                    r["booth_id"],
                    r["booth_name"],
                    r["serial_no"],
                    r["elector_name"],
                    r["relation_name"],
                    r["gender"],
                    r["age"],
                    r["house_no"],
                    r["section_name"],
                    r["reason_code"],
                    r["supplement_ref"],
                )
                for r in rows
            ],
        )

    con.execute("CREATE INDEX idx_roll_ver_epic ON roll_entries(version_id, epic_id)")
    con.execute("CREATE INDEX idx_roll_ver_booth ON roll_entries(version_id, booth_id)")
    return con


def list_snapshots(con: duckdb.DuckDBPyConnection, lang: str = "en") -> list[SnapshotMeta]:
    from app.i18n import normalize_lang, pick, tr_snapshot_label
    lang_code = normalize_lang(lang)
    rows = con.execute(
        """
        SELECT version_id, label, publication_date, roll_type, sha256, total_electors, booth_count
        FROM snapshots
        ORDER BY publication_date ASC
        """
    ).fetchall()
    notice = pick(
        lang_code,
        "100% SYNTHETIC TEST DATASET — NO REAL VOTER DATA",
        "100% सिंथेटिक परीक्षण डेटासेट — कोई वास्तविक मतदाता डेटा नहीं",
        "100% સિન્થેટિક ટેસ્ટ ડેટાસેટ — કોઈ વાસ્તવિક મતદાર ડેટા નથી",
    )
    return [
        SnapshotMeta(
            version_id=r[0],
            label=tr_snapshot_label(r[1], lang_code),
            publication_date=r[2],
            roll_type=r[3],
            sha256=r[4],
            total_electors=r[5],
            booth_count=r[6],
            synthetic_notice=notice,
        )
        for r in rows
    ]
