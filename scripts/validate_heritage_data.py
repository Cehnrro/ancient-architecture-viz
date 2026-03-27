from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "data"

PERIODS = ["先秦两汉", "魏晋隋唐", "宋辽金元", "明清"]
TYPES = ["皇宫", "官府", "民居", "桥梁"]
EDGE_TYPES = {"mentor", "student", "collab", "school"}
CRAFT_BUILDING_TYPES = {"设计", "主持营建", "监造", "修缮", "都城规划关联", "文献记述关联"}
WORK_CRAFT_TYPES = {"AUTHOR", "EDIT", "QUOTE", "PRACTICE", "INSTITUTION", "URBAN"}
WORK_BUILDING_TYPES = {"DESIGN", "BUILD", "SUPERVISE", "REPAIR", "DOC", "PRACTICE", "INSTITUTION", "URBAN"}
MIN_WORKS = 15
MIN_CRAFTSMEN = 25
MAX_INFERRED_RATIO = 0.3

REQUIRED_WORK_FIELDS = {
    "id",
    "title",
    "period",
    "primaryType",
    "keywords",
    "relatedCraftsmen",
    "relatedBuildings",
    "sourceRefs",
    "confidence",
}
REQUIRED_CRAFT_FIELDS = {
    "id",
    "name",
    "period",
    "primaryType",
    "mentorIds",
    "studentIds",
    "relatedWorks",
    "relatedBuildings",
    "schoolTags",
    "sourceRefs",
    "confidence",
}
REQUIRED_EDGE_FIELDS = {
    "source",
    "target",
    "relationType",
    "evidenceRef",
    "isInferred",
}
REQUIRED_CBR_FIELDS = {
    "id",
    "craftId",
    "buildingId",
    "relationType",
    "evidenceRef",
    "evidenceTitle",
    "evidenceUrl",
    "isCrossPeriod",
}
REQUIRED_WCR_FIELDS = {
    "id",
    "workId",
    "craftId",
    "relationType",
    "evidenceRef",
    "evidenceTitle",
    "evidenceUrl",
    "isCrossPeriod",
}
REQUIRED_WBR_FIELDS = {
    "id",
    "workId",
    "buildingId",
    "relationType",
    "evidenceRef",
    "evidenceTitle",
    "evidenceUrl",
    "isCrossPeriod",
}


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


def load_lineage(path: Path):
    text = path.read_text(encoding="utf-8")
    start = text.find("export const lineageEdges = ")
    end = text.find("\n\nexport const lineageRelationTypes")
    if start < 0 or end < 0:
        raise ValueError("lineage.js format invalid")
    payload = text[start + len("export const lineageEdges = ") : end].strip()
    return json.loads(payload)


def coverage_check(items, label):
    periods = {i.get("period") for i in items}
    types = {i.get("primaryType") for i in items}
    missing_periods = [p for p in PERIODS if p not in periods]
    missing_types = [t for t in TYPES if t not in types]

    ok = True
    if missing_periods:
        print(f"[FAIL] {label} missing periods: {missing_periods}")
        ok = False
    else:
        print(f"[PASS] {label} period coverage complete")

    if missing_types:
        print(f"[FAIL] {label} missing primary types: {missing_types}")
        ok = False
    else:
        print(f"[PASS] {label} type coverage complete")
    return ok


def required_fields_check(items, fields, label):
    missing = []
    for item in items:
        for field in fields:
            if field not in item or item[field] is None:
                missing.append((item.get("id", "?"), field))
    if missing:
        print(f"[FAIL] {label} missing required fields: {len(missing)}")
        for row in missing[:20]:
            print("  ", row)
        return False
    print(f"[PASS] {label} required fields complete")
    return True


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

    edges = load_lineage(DATA_DIR / "lineage.js")
    craft_building_relations = load_js_array(DATA_DIR / "craft_building_relations.js", "craftBuildingRelations")
    work_craft_relations = load_js_array(DATA_DIR / "work_craft_relations.js", "workCraftRelations")
    work_building_relations = load_js_array(DATA_DIR / "work_building_relations.js", "workBuildingRelations")

    building_ids = {b["id"] for b in buildings_full}
    building_map = {b["id"]: b for b in buildings_full}

    ok = True

    if len(works) < MIN_WORKS:
        print(f"[FAIL] works count {len(works)} < {MIN_WORKS}")
        ok = False
    else:
        print(f"[PASS] works count {len(works)}")

    if len(craftsmen) < MIN_CRAFTSMEN:
        print(f"[FAIL] craftsmen count {len(craftsmen)} < {MIN_CRAFTSMEN}")
        ok = False
    else:
        print(f"[PASS] craftsmen count {len(craftsmen)}")

    ok = required_fields_check(works, REQUIRED_WORK_FIELDS, "works") and ok
    ok = required_fields_check(craftsmen, REQUIRED_CRAFT_FIELDS, "craftsmen") and ok
    ok = required_fields_check(edges, REQUIRED_EDGE_FIELDS, "lineage edges") and ok
    ok = required_fields_check(craft_building_relations, REQUIRED_CBR_FIELDS, "craft-building relations") and ok
    ok = required_fields_check(work_craft_relations, REQUIRED_WCR_FIELDS, "work-craft relations") and ok
    ok = required_fields_check(work_building_relations, REQUIRED_WBR_FIELDS, "work-building relations") and ok

    ok = coverage_check(works, "works") and ok
    ok = coverage_check(craftsmen, "craftsmen") and ok

    work_ids = {w["id"] for w in works}
    craft_ids = {c["id"] for c in craftsmen}
    work_period = {w["id"]: w["period"] for w in works}
    craft_period = {c["id"]: c["period"] for c in craftsmen}

    errors = []

    for rel in craft_building_relations:
        if rel["craftId"] not in craft_ids:
            errors.append(("cbr-craft", rel["id"], rel["craftId"]))
        if rel["buildingId"] not in building_ids:
            errors.append(("cbr-building", rel["id"], rel["buildingId"]))
        if rel["relationType"] not in CRAFT_BUILDING_TYPES:
            errors.append(("cbr-relationType", rel["id"], rel["relationType"]))
        if not str(rel.get("evidenceUrl", "")).startswith("http"):
            errors.append(("cbr-evidenceUrl", rel["id"], rel.get("evidenceUrl")))
        expected = craft_period.get(rel["craftId"]) != building_map.get(rel["buildingId"], {}).get("period")
        if bool(rel.get("isCrossPeriod")) != bool(expected):
            errors.append(("cbr-isCrossPeriod", rel["id"], rel.get("isCrossPeriod")))

    for rel in work_craft_relations:
        if rel["workId"] not in work_ids:
            errors.append(("wcr-work", rel["id"], rel["workId"]))
        if rel["craftId"] not in craft_ids:
            errors.append(("wcr-craft", rel["id"], rel["craftId"]))
        if rel["relationType"] not in WORK_CRAFT_TYPES:
            errors.append(("wcr-relationType", rel["id"], rel["relationType"]))
        if not str(rel.get("evidenceUrl", "")).startswith("http"):
            errors.append(("wcr-evidenceUrl", rel["id"], rel.get("evidenceUrl")))
        expected = work_period.get(rel["workId"]) != craft_period.get(rel["craftId"])
        if bool(rel.get("isCrossPeriod")) != bool(expected):
            errors.append(("wcr-isCrossPeriod", rel["id"], rel.get("isCrossPeriod")))

    for rel in work_building_relations:
        if rel["workId"] not in work_ids:
            errors.append(("wbr-work", rel["id"], rel["workId"]))
        if rel["buildingId"] not in building_ids:
            errors.append(("wbr-building", rel["id"], rel["buildingId"]))
        if rel["relationType"] not in WORK_BUILDING_TYPES:
            errors.append(("wbr-relationType", rel["id"], rel["relationType"]))
        if not str(rel.get("evidenceUrl", "")).startswith("http"):
            errors.append(("wbr-evidenceUrl", rel["id"], rel.get("evidenceUrl")))
        expected = work_period.get(rel["workId"]) != building_map.get(rel["buildingId"], {}).get("period")
        if bool(rel.get("isCrossPeriod")) != bool(expected):
            errors.append(("wbr-isCrossPeriod", rel["id"], rel.get("isCrossPeriod")))

    derived_work_crafts = defaultdict(list)
    derived_craft_works = defaultdict(list)
    for rel in work_craft_relations:
        derived_work_crafts[rel["workId"]].append(rel["craftId"])
        derived_craft_works[rel["craftId"]].append(rel["workId"])

    derived_work_buildings = defaultdict(list)
    for rel in work_building_relations:
        derived_work_buildings[rel["workId"]].append(rel["buildingId"])

    derived_craft_buildings = defaultdict(list)
    for rel in craft_building_relations:
        derived_craft_buildings[rel["craftId"]].append(rel["buildingId"])

    for w in works:
        expected_crafts = dedupe_preserve(derived_work_crafts.get(w["id"], []))
        expected_buildings = dedupe_preserve(derived_work_buildings.get(w["id"], []))
        if dedupe_preserve(w.get("relatedCraftsmen", [])) != expected_crafts:
            errors.append(("works-relatedCraftsmen-not-derived", w["id"], ""))
        if dedupe_preserve(w.get("relatedBuildings", [])) != expected_buildings:
            errors.append(("works-relatedBuildings-not-derived", w["id"], ""))

    for c in craftsmen:
        expected_works = dedupe_preserve(derived_craft_works.get(c["id"], []))
        expected_buildings = dedupe_preserve(derived_craft_buildings.get(c["id"], []))
        if dedupe_preserve(c.get("relatedWorks", [])) != expected_works:
            errors.append(("crafts-relatedWorks-not-derived", c["id"], ""))
        if dedupe_preserve(c.get("relatedBuildings", [])) != expected_buildings:
            errors.append(("crafts-relatedBuildings-not-derived", c["id"], ""))

    for e in edges:
        if e["source"] not in craft_ids:
            errors.append(("edge-source", e["source"], ""))
        if e["target"] not in craft_ids:
            errors.append(("edge-target", e["target"], ""))
        if e.get("relationType") not in EDGE_TYPES:
            errors.append(("edge-relationType", e.get("source", "?"), e.get("relationType")))
        if not str(e.get("evidenceRef", "")).strip():
            errors.append(("edge-evidenceRef", e.get("source", "?"), e.get("target", "?")))

    if errors:
        print(f"[FAIL] invalid/dangling/inconsistent records: {len(errors)}")
        for err in errors[:60]:
            print("  ", err)
        ok = False
    else:
        print("[PASS] no dangling references and derived consistency ok")

    inferred = [e for e in edges if e.get("isInferred")]
    ratio = len(inferred) / len(edges) if edges else 0
    if ratio > MAX_INFERRED_RATIO:
        print(f"[FAIL] inferred ratio {ratio:.2%} > {MAX_INFERRED_RATIO:.0%}")
        ok = False
    else:
        print(f"[PASS] inferred ratio {ratio:.2%}")

    conf_count = defaultdict(int)
    for item in works + craftsmen:
        conf_count[item.get("confidence", "?")] += 1
    print("[INFO] confidence distribution", dict(conf_count))

    print("[INFO] work-craft relation count", len(work_craft_relations))
    print("[INFO] work-building relation count", len(work_building_relations))
    print("[INFO] craft-building relation count", len(craft_building_relations))
    print("[INFO] work-craft cross-period", sum(1 for r in work_craft_relations if r.get("isCrossPeriod")))
    print("[INFO] work-building cross-period", sum(1 for r in work_building_relations if r.get("isCrossPeriod")))
    print("[INFO] empty works", sum(1 for w in works if not w.get("relatedCraftsmen") and not w.get("relatedBuildings")))
    print("[INFO] empty craftsmen", sum(1 for c in craftsmen if not c.get("relatedWorks") and not c.get("relatedBuildings")))

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
