from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "data"
DOCS_DIR = ROOT / "docs" / "heritage-pack"

CRAFT_BUILDING_TYPES = {"设计", "主持营建", "监造", "修缮", "都城规划关联", "文献记述关联"}
WORK_CRAFT_TYPES = {"AUTHOR", "EDIT", "QUOTE", "PRACTICE", "INSTITUTION", "URBAN"}
WORK_BUILDING_TYPES = {"DESIGN", "BUILD", "SUPERVISE", "REPAIR", "DOC", "PRACTICE", "INSTITUTION", "URBAN"}


def load_js_array(path: Path, const_name: str):
    text = path.read_text(encoding="utf-8")
    prefix = f"export const {const_name} = "
    idx = text.find(prefix)
    if idx < 0:
        raise ValueError(f"{path} missing export {const_name}")
    payload = text[idx + len(prefix) :].strip()
    if payload.endswith(";"):
        payload = payload[:-1]
    return json.loads(payload)


def write_js_array(path: Path, const_name: str, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(f"export const {const_name} = {text}\n", encoding="utf-8")


def _validate_row(row: dict, required_fields: set[str], row_idx: int, ledger_name: str):
    for key in required_fields:
        if not str(row.get(key, "")).strip():
            raise ValueError(f"{ledger_name} row {row_idx} missing field: {key}")


def load_craft_building_ledger(path: Path):
    required = {"craftId", "buildingId", "relationType", "evidenceRef", "evidenceTitle", "evidenceUrl"}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    cleaned = []
    for idx, row in enumerate(rows, start=1):
        _validate_row(row, required, idx, path.name)
        rel_type = row["relationType"].strip()
        if rel_type not in CRAFT_BUILDING_TYPES:
            raise ValueError(f"{path.name} row {idx} invalid relationType: {rel_type}")
        evidence_url = row["evidenceUrl"].strip()
        if not evidence_url.startswith("http"):
            raise ValueError(f"{path.name} row {idx} invalid evidenceUrl: {evidence_url}")

        cleaned.append(
            {
                "id": row.get("id", "").strip() or f"cbr{idx}",
                "craftId": row["craftId"].strip(),
                "buildingId": row["buildingId"].strip(),
                "relationType": rel_type,
                "evidenceRef": row["evidenceRef"].strip(),
                "evidenceTitle": row["evidenceTitle"].strip(),
                "evidenceUrl": evidence_url,
            }
        )
    return cleaned


def load_work_target_ledger(path: Path, allowed_types: set[str], prefix: str):
    required = {"workId", "targetId", "relationType", "evidenceRef", "evidenceTitle", "evidenceUrl"}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    cleaned = []
    for idx, row in enumerate(rows, start=1):
        _validate_row(row, required, idx, path.name)
        rel_type = row["relationType"].strip()
        if rel_type not in allowed_types:
            raise ValueError(f"{path.name} row {idx} invalid relationType: {rel_type}")
        evidence_url = row["evidenceUrl"].strip()
        if not evidence_url.startswith("http"):
            raise ValueError(f"{path.name} row {idx} invalid evidenceUrl: {evidence_url}")

        cleaned.append(
            {
                "id": row.get("id", "").strip() or f"{prefix}{idx}",
                "workId": row["workId"].strip(),
                "targetId": row["targetId"].strip(),
                "relationType": rel_type,
                "evidenceRef": row["evidenceRef"].strip(),
                "evidenceTitle": row["evidenceTitle"].strip(),
                "evidenceUrl": evidence_url,
            }
        )
    return cleaned


def dedupe_preserve(seq):
    seen = set()
    out = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def main():
    works = load_js_array(DATA_DIR / "works.js", "works")
    craftsmen = load_js_array(DATA_DIR / "craftsmen.js", "craftsmen")
    with (DATA_DIR / "buildings_full.json").open("r", encoding="utf-8") as f:
        buildings_full = json.load(f)

    craft_building_rows = load_craft_building_ledger(DOCS_DIR / "craft_building_relations.csv")
    work_craft_rows = load_work_target_ledger(DOCS_DIR / "work_craft_relations.csv", WORK_CRAFT_TYPES, "wc")
    work_building_rows = load_work_target_ledger(DOCS_DIR / "work_building_relations.csv", WORK_BUILDING_TYPES, "wb")

    work_map = {w["id"]: w for w in works}
    craft_map = {c["id"]: c for c in craftsmen}
    building_map = {b["id"]: b for b in buildings_full}

    craft_building = []
    seen_cbr = set()
    for row in craft_building_rows:
        key = (row["craftId"], row["buildingId"], row["relationType"], row["evidenceRef"])
        if key in seen_cbr:
            continue
        seen_cbr.add(key)

        if row["craftId"] not in craft_map:
            raise ValueError(f"unknown craftId in craft_building_relations: {row['craftId']}")
        if row["buildingId"] not in building_map:
            raise ValueError(f"unknown buildingId in craft_building_relations: {row['buildingId']}")

        craft_period = craft_map[row["craftId"]].get("period")
        building_period = building_map[row["buildingId"]].get("period")
        is_cross = craft_period != building_period

        craft_building.append({**row, "isCrossPeriod": is_cross})

    work_craft = []
    seen_wc = set()
    for row in work_craft_rows:
        craft_id = row["targetId"]
        key = (row["workId"], craft_id, row["relationType"], row["evidenceRef"])
        if key in seen_wc:
            continue
        seen_wc.add(key)

        if row["workId"] not in work_map:
            raise ValueError(f"unknown workId in work_craft_relations: {row['workId']}")
        if craft_id not in craft_map:
            raise ValueError(f"unknown targetId(craftId) in work_craft_relations: {craft_id}")

        work_period = work_map[row["workId"]].get("period")
        craft_period = craft_map[craft_id].get("period")
        is_cross = work_period != craft_period

        work_craft.append(
            {
                "id": row["id"],
                "workId": row["workId"],
                "craftId": craft_id,
                "relationType": row["relationType"],
                "evidenceRef": row["evidenceRef"],
                "evidenceTitle": row["evidenceTitle"],
                "evidenceUrl": row["evidenceUrl"],
                "isCrossPeriod": is_cross,
            }
        )

    work_building = []
    seen_wb = set()
    for row in work_building_rows:
        building_id = row["targetId"]
        key = (row["workId"], building_id, row["relationType"], row["evidenceRef"])
        if key in seen_wb:
            continue
        seen_wb.add(key)

        if row["workId"] not in work_map:
            raise ValueError(f"unknown workId in work_building_relations: {row['workId']}")
        if building_id not in building_map:
            raise ValueError(f"unknown targetId(buildingId) in work_building_relations: {building_id}")

        work_period = work_map[row["workId"]].get("period")
        building_period = building_map[building_id].get("period")
        is_cross = work_period != building_period

        work_building.append(
            {
                "id": row["id"],
                "workId": row["workId"],
                "buildingId": building_id,
                "relationType": row["relationType"],
                "evidenceRef": row["evidenceRef"],
                "evidenceTitle": row["evidenceTitle"],
                "evidenceUrl": row["evidenceUrl"],
                "isCrossPeriod": is_cross,
            }
        )

    work_to_crafts = defaultdict(list)
    craft_to_works = defaultdict(list)
    for rel in work_craft:
        work_to_crafts[rel["workId"]].append(rel["craftId"])
        craft_to_works[rel["craftId"]].append(rel["workId"])

    work_to_buildings = defaultdict(list)
    for rel in work_building:
        work_to_buildings[rel["workId"]].append(rel["buildingId"])

    craft_to_buildings = defaultdict(list)
    for rel in craft_building:
        craft_to_buildings[rel["craftId"]].append(rel["buildingId"])

    for work in works:
        work["relatedCraftsmen"] = dedupe_preserve(work_to_crafts.get(work["id"], []))
        work["relatedBuildings"] = dedupe_preserve(work_to_buildings.get(work["id"], []))

    for craft in craftsmen:
        craft["relatedWorks"] = dedupe_preserve(craft_to_works.get(craft["id"], []))
        craft["relatedBuildings"] = dedupe_preserve(craft_to_buildings.get(craft["id"], []))

    write_js_array(DATA_DIR / "works.js", "works", works)
    write_js_array(DATA_DIR / "craftsmen.js", "craftsmen", craftsmen)
    write_js_array(DATA_DIR / "craft_building_relations.js", "craftBuildingRelations", craft_building)
    write_js_array(DATA_DIR / "work_craft_relations.js", "workCraftRelations", work_craft)
    write_js_array(DATA_DIR / "work_building_relations.js", "workBuildingRelations", work_building)

    print(
        "verified "
        f"works={len(works)}, craftsmen={len(craftsmen)}, "
        f"workCraftRelations={len(work_craft)}, workBuildingRelations={len(work_building)}, "
        f"craftBuildingRelations={len(craft_building)}, "
        f"emptyWorks={sum(1 for w in works if not w.get('relatedCraftsmen') and not w.get('relatedBuildings'))}, "
        f"emptyCrafts={sum(1 for c in craftsmen if not c.get('relatedWorks') and not c.get('relatedBuildings'))}"
    )


if __name__ == "__main__":
    main()
