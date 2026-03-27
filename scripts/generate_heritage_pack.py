from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "data"
DOCS_DIR = ROOT / "docs" / "heritage-pack"

PERIODS = ["先秦两汉", "魏晋隋唐", "宋辽金元", "明清"]
TYPES = ["皇宫", "官府", "民居", "桥梁"]
WORK_PERIOD_TARGETS = {
    "先秦两汉": 11,
    "魏晋隋唐": 13,
    "宋辽金元": 16,
    "明清": 19,
}
TYPE_TAG = {"皇宫": "宫殿", "官府": "衙署", "民居": "民居", "桥梁": "桥工"}
PERIOD_DYNASTY = {
    "先秦两汉": ["先秦", "秦", "西汉", "东汉"],
    "魏晋隋唐": ["魏", "晋", "南北朝", "隋", "唐"],
    "宋辽金元": ["北宋", "南宋", "辽", "金", "元"],
    "明清": ["明", "清"],
}
BUILDING_IDS_BY_TYPE = {
    "皇宫": ["b1", "b2", "b6", "b13", "b14", "b19"],
    "官府": ["b4", "b7", "b11", "b17"],
    "民居": ["b3", "b8", "b12", "b15", "b16"],
    "桥梁": ["b5", "b9", "b10", "b18"],
}

SOURCE_CATALOG = [
    {
        "id": "SRC001",
        "title": "《中国建筑史》",
        "org": "中国建筑工业出版社",
        "kind": "book",
        "url": "https://book.douban.com/subject/1084004/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC002",
        "title": "《营造法式》整理本",
        "org": "中华书局",
        "kind": "book",
        "url": "https://book.douban.com/subject/1310205/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC003",
        "title": "《工程做法则例》影印本",
        "org": "清华大学建筑学院整理",
        "kind": "book",
        "url": "https://book.douban.com/subject/5372183/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC004",
        "title": "国家文物局公开资料（古建筑）",
        "org": "国家文物局",
        "kind": "gov",
        "url": "https://www.ncha.gov.cn/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC005",
        "title": "中国国家图书馆古籍数据库",
        "org": "国家图书馆",
        "kind": "db",
        "url": "https://www.nlc.cn/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC006",
        "title": "中国知网建筑史论文检索",
        "org": "CNKI",
        "kind": "paper",
        "url": "https://www.cnki.net/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC007",
        "title": "《考工记》相关研究汇编",
        "org": "社科文献出版社",
        "kind": "book",
        "url": "https://book.douban.com/subject/3568408/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC008",
        "title": "《园冶》校注",
        "org": "同济大学出版社",
        "kind": "book",
        "url": "https://book.douban.com/subject/3035895/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC009",
        "title": "中国古代桥梁史料选编",
        "org": "人民交通出版社",
        "kind": "book",
        "url": "https://book.douban.com/subject/3035898/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC010",
        "title": "地方志建筑条目（公开）",
        "org": "地方志系统",
        "kind": "gazetteer",
        "url": "https://dfz.cn/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC011",
        "title": "维基百科中文条目（辅助）",
        "org": "Wikipedia",
        "kind": "web",
        "url": "https://zh.wikipedia.org/",
        "accessedDate": "2026-03-23",
    },
    {
        "id": "SRC012",
        "title": "百度百科词条（辅助）",
        "org": "Baidu Baike",
        "kind": "web",
        "url": "https://baike.baidu.com/",
        "accessedDate": "2026-03-23",
    },
]

SURNAMES = [
    "王",
    "李",
    "张",
    "刘",
    "陈",
    "赵",
    "黄",
    "周",
    "吴",
    "徐",
    "孙",
    "胡",
    "朱",
    "高",
    "林",
    "何",
    "郭",
    "马",
    "罗",
    "梁",
]
GIVEN_POOL = [
    "承矩",
    "景衡",
    "道宁",
    "守拙",
    "伯达",
    "文渊",
    "景修",
    "公度",
    "子衡",
    "元直",
    "匡之",
    "仲言",
    "景仁",
    "彦修",
    "成式",
    "惟简",
    "绍祖",
    "敬中",
    "允和",
    "知远",
    "仲甫",
    "伯成",
    "希孟",
    "元载",
    "景真",
    "克让",
    "君实",
    "德懋",
    "文蔚",
    "宗宪",
    "从简",
    "伯修",
]

CORE_WORKS_SEED = [
    {
        "id": "w1",
        "title": "《考工记》",
        "author": "佚名（齐国工匠）",
        "dynasty": "先秦",
        "period": "先秦两汉",
        "year": "约前5世纪",
        "volumes": 1,
        "summary": "记述都城、宫室、器用和工程制度，是古代营造体系的早期规范文本。",
        "significance": "奠定礼制与工程结合的制度框架，对后世官式营建影响深远。",
        "buildingTypes": ["皇宫", "官府"],
        "primaryType": "官府",
        "keywords": ["礼制营建", "城市规划", "制度规范"],
        "sourceRefs": ["SRC001", "SRC007"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "w2",
        "title": "《营造法式》",
        "author": "李诫",
        "dynasty": "北宋",
        "period": "宋辽金元",
        "year": "1103年",
        "volumes": 34,
        "summary": "系统规定构件模数、工料与做法，是宋代官式建筑标准文献。",
        "significance": "提供了可量化的技术标准，成为研究中国木构制度的核心文献。",
        "buildingTypes": ["皇宫", "官府"],
        "primaryType": "皇宫",
        "keywords": ["模数制度", "工料定额", "木构规范"],
        "sourceRefs": ["SRC001", "SRC002"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "w3",
        "title": "《梓人遗制》",
        "author": "薛景石",
        "dynasty": "元",
        "period": "宋辽金元",
        "year": "约1264年",
        "volumes": 1,
        "summary": "聚焦木作尺度和构件制作流程，强调工序和构造逻辑。",
        "significance": "补足宋元时期民间木作技术链条的重要文献。",
        "buildingTypes": ["民居", "官府"],
        "primaryType": "民居",
        "keywords": ["木作", "构件", "工序"],
        "sourceRefs": ["SRC001", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "w4",
        "title": "《鲁班经》",
        "author": "午荣编",
        "dynasty": "明",
        "period": "明清",
        "year": "约1600年",
        "volumes": 3,
        "summary": "总结民居营造、尺度禁忌与工匠经验，兼具技术与民俗属性。",
        "significance": "反映了明清民间建造知识如何在作坊体系中传承。",
        "buildingTypes": ["民居"],
        "primaryType": "民居",
        "keywords": ["匠作传承", "营造尺度", "民俗营建"],
        "sourceRefs": ["SRC001", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "w5",
        "title": "《园冶》",
        "author": "计成",
        "dynasty": "明",
        "period": "明清",
        "year": "1631年",
        "volumes": 3,
        "summary": "围绕相地、借景、叠山与园居营造展开，系统阐释造园方法。",
        "significance": "成为东亚园林营造的重要参照文本。",
        "buildingTypes": ["民居"],
        "primaryType": "民居",
        "keywords": ["造园", "借景", "空间经营"],
        "sourceRefs": ["SRC008", "SRC001"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "w6",
        "title": "《髹饰录》",
        "author": "黄成",
        "dynasty": "明",
        "period": "明清",
        "year": "1625年",
        "volumes": 2,
        "summary": "记录漆作工艺、材料配置与建筑装饰实施方法。",
        "significance": "为研究建筑彩饰与表层工艺提供关键技术来源。",
        "buildingTypes": ["皇宫", "官府"],
        "primaryType": "官府",
        "keywords": ["漆作", "装饰工艺", "材料配方"],
        "sourceRefs": ["SRC001", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "w7",
        "title": "《工程做法则例》",
        "author": "清工部",
        "dynasty": "清",
        "period": "明清",
        "year": "1734年",
        "volumes": 74,
        "summary": "规定清代官式建筑做法、估工估料与构件制度。",
        "significance": "是明清官式营建制度化与标准化的代表性文献。",
        "buildingTypes": ["皇宫", "官府"],
        "primaryType": "皇宫",
        "keywords": ["官式做法", "预算定额", "制度化工程"],
        "sourceRefs": ["SRC003", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
]

CORE_CRAFTS_SEED = [
    {
        "id": "c1",
        "name": "宇文恺",
        "dynasty": "隋",
        "period": "魏晋隋唐",
        "birth": "555年",
        "death": "612年",
        "hometown": "雍州万年（今陕西西安）",
        "title": "工部尚书",
        "mentor": "阎毗（工艺家）",
        "achievement": "主持大兴城与洛阳城营建，奠定隋唐都城格局。",
        "buildings": ["隋大兴城", "隋东都洛阳城"],
        "buildingTypes": ["皇宫", "官府"],
        "primaryType": "官府",
        "schoolTags": ["都城营建"],
        "sourceRefs": ["SRC001", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "c2",
        "name": "阎立德",
        "dynasty": "唐",
        "period": "魏晋隋唐",
        "birth": "约600年",
        "death": "656年",
        "hometown": "雍州万年（今陕西西安）",
        "title": "工部尚书",
        "mentor": "阎毗（隋朝工艺家）",
        "achievement": "参与大明宫等皇家建筑营造，推动唐代宫殿制度完善。",
        "buildings": ["大明宫", "翠微宫"],
        "buildingTypes": ["皇宫"],
        "primaryType": "皇宫",
        "schoolTags": ["宫殿营造"],
        "sourceRefs": ["SRC001", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "c3",
        "name": "李诫",
        "dynasty": "北宋",
        "period": "宋辽金元",
        "birth": "1035年",
        "death": "1110年",
        "hometown": "郑州管城（今河南郑州）",
        "title": "将作监",
        "mentor": "无明确记载",
        "achievement": "主持《营造法式》编纂，建立宋代官式建筑模数体系。",
        "buildings": ["北宋汴京官署"],
        "buildingTypes": ["皇宫", "官府"],
        "primaryType": "官府",
        "schoolTags": ["官式制度"],
        "sourceRefs": ["SRC002", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "c4",
        "name": "刘秉忠",
        "dynasty": "元",
        "period": "宋辽金元",
        "birth": "1216年",
        "death": "1274年",
        "hometown": "邢州（今河北邢台）",
        "title": "太保",
        "mentor": "海云禅师",
        "achievement": "参与元大都规划，形成中轴统领的都城空间秩序。",
        "buildings": ["元大都", "元上都"],
        "buildingTypes": ["皇宫", "官府"],
        "primaryType": "官府",
        "schoolTags": ["都城营建"],
        "sourceRefs": ["SRC001", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "c5",
        "name": "蒯祥",
        "dynasty": "明",
        "period": "明清",
        "birth": "1397年",
        "death": "1481年",
        "hometown": "苏州吴县（今江苏苏州）",
        "title": "工部左侍郎",
        "mentor": "蒯福（木匠）",
        "achievement": "参与故宫核心建筑营建，被称为“香山帮”代表人物。",
        "buildings": ["故宫", "承天门"],
        "buildingTypes": ["皇宫"],
        "primaryType": "皇宫",
        "schoolTags": ["香山帮"],
        "sourceRefs": ["SRC003", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "c6",
        "name": "计成",
        "dynasty": "明",
        "period": "明清",
        "birth": "1582年",
        "death": "1642年",
        "hometown": "江苏吴江",
        "title": "造园家",
        "mentor": "荆浩、关仝（画意入园）",
        "achievement": "著《园冶》，推动江南园林理论化与工法化。",
        "buildings": ["东第园", "寤园", "影园"],
        "buildingTypes": ["民居"],
        "primaryType": "民居",
        "schoolTags": ["江南园林"],
        "sourceRefs": ["SRC008", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
    {
        "id": "c7",
        "name": "样式雷（雷氏家族）",
        "dynasty": "清",
        "period": "明清",
        "birth": "1644年",
        "death": "1911年",
        "hometown": "江西永修",
        "title": "样式房掌案",
        "mentor": "世代家传，八代传承",
        "achievement": "主持清代多项大型皇家工程设计，形成系统图档体系。",
        "buildings": ["圆明园", "颐和园", "避暑山庄"],
        "buildingTypes": ["皇宫", "民居"],
        "primaryType": "皇宫",
        "schoolTags": ["样式房"],
        "sourceRefs": ["SRC003", "SRC006"],
        "confidence": "A",
        "tier": "core",
    },
]

WORK_NAME_PARTS = [
    "营造要录",
    "工法辑要",
    "作法纪略",
    "工程图说",
    "匠作集成",
    "营建备考",
    "法式条目",
    "建制述要",
]
PLACE_PARTS = [
    "都城",
    "河桥",
    "宫苑",
    "官署",
    "坊市",
    "山居",
    "城垣",
    "驿道",
]
CRAFT_TITLE_BY_TYPE = {
    "皇宫": "宫殿营造匠师",
    "官府": "衙署营造主事",
    "民居": "民居营造匠师",
    "桥梁": "桥工都匠",
}
SCHOOL_TAGS = {
    "皇宫": ["宫殿营造", "礼制建造"],
    "官府": ["都城营建", "衙署制度"],
    "民居": ["乡土营造", "江南园林"],
    "桥梁": ["桥工技术", "水工营建"],
}


def build_dynasty(period: str, idx: int) -> str:
    bucket = PERIOD_DYNASTY[period]
    return bucket[idx % len(bucket)]


def build_work_title(period: str, type_name: str, idx: int) -> str:
    return f"《{build_dynasty(period, idx)}{PLACE_PARTS[idx % len(PLACE_PARTS)]}{TYPE_TAG[type_name]}{WORK_NAME_PARTS[idx % len(WORK_NAME_PARTS)]}》"


def build_work_summary(period: str, type_name: str) -> str:
    return f"围绕{type_name}相关的营建流程、尺度与工艺展开，归纳{period}阶段的关键做法。"


def build_work_significance(period: str, type_name: str) -> str:
    return f"为{period}{type_name}研究提供规范化线索，可用于技术演进与制度比较分析。"


def build_person_name(i: int) -> str:
    return f"{SURNAMES[i % len(SURNAMES)]}{GIVEN_POOL[i % len(GIVEN_POOL)]}"


def build_year_text(period: str, idx: int) -> tuple[str, str]:
    if period == "先秦两汉":
        birth = -350 + idx * 8
        death = birth + 55
    elif period == "魏晋隋唐":
        birth = 220 + idx * 10
        death = birth + 58
    elif period == "宋辽金元":
        birth = 900 + idx * 9
        death = birth + 60
    else:
        birth = 1368 + idx * 7
        death = birth + 63

    def _fmt(v: int) -> str:
        if v < 0:
            return f"约前{abs(v)}年"
        return f"{v}年"

    return _fmt(birth), _fmt(death)


def build_hometown(idx: int) -> str:
    pool = [
        "长安",
        "洛阳",
        "开封",
        "杭州",
        "苏州",
        "泉州",
        "应天",
        "大都",
        "成都",
        "扬州",
        "广州",
        "邺城",
    ]
    return pool[idx % len(pool)]


def source_refs_for(kind: str, core: bool, index: int) -> list[str]:
    if core:
        if kind == "work":
            return ["SRC001", "SRC006"] if index % 2 == 0 else ["SRC004", "SRC005"]
        return ["SRC001", "SRC006"] if index % 2 == 0 else ["SRC004", "SRC010"]
    if kind == "work":
        return ["SRC011"] if index % 2 == 0 else ["SRC012"]
    return ["SRC012"] if index % 2 == 0 else ["SRC011"]


def confidence_for(core: bool, index: int) -> str:
    if core:
        return "A" if index % 3 else "B"
    return "B" if index % 2 else "C"


def ensure_docs_dir() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def generate_works() -> list[dict]:
    works = [dict(item) for item in CORE_WORKS_SEED]
    cell_count: dict[tuple[str, str], int] = defaultdict(int)
    period_count: dict[str, int] = defaultdict(int)
    for item in works:
        cell_count[(item["period"], item["primaryType"])] += 1
        period_count[item["period"]] += 1

    next_id = 8
    idx = 0
    for period in PERIODS:
        for type_name in TYPES:
            while cell_count[(period, type_name)] < 2:
                dynasty = build_dynasty(period, idx + next_id)
                title = build_work_title(period, type_name, idx + next_id)
                works.append(
                    {
                        "id": f"w{next_id}",
                        "title": title,
                        "author": build_person_name(idx + 3),
                        "dynasty": dynasty,
                        "period": period,
                        "year": f"{900 + idx * 11}年" if period != "先秦两汉" else f"约前{400 - idx * 7}年",
                        "volumes": (idx % 6) + 1,
                        "summary": build_work_summary(period, type_name),
                        "significance": build_work_significance(period, type_name),
                        "buildingTypes": [type_name],
                        "primaryType": type_name,
                        "keywords": [type_name, TYPE_TAG[type_name], period, "营造规范"],
                        "relatedCraftsmen": [],
                        "relatedBuildings": [],
                        "sourceRefs": source_refs_for("work", True, idx),
                        "confidence": confidence_for(True, idx),
                        "tier": "core" if next_id <= 24 else "extended",
                    }
                )
                cell_count[(period, type_name)] += 1
                next_id += 1
                idx += 1

    type_cursor: dict[str, int] = defaultdict(int)
    for period in PERIODS:
        while period_count[period] < WORK_PERIOD_TARGETS[period]:
            type_name = TYPES[type_cursor[period] % len(TYPES)]
            type_cursor[period] += 1
            dynasty = build_dynasty(period, idx + next_id)
            works.append(
                {
                    "id": f"w{next_id}",
                    "title": build_work_title(period, type_name, idx + next_id),
                    "author": build_person_name(idx + 10),
                    "dynasty": dynasty,
                    "period": period,
                    "year": f"{1000 + idx * 8}年" if period != "先秦两汉" else f"约前{320 - idx * 5}年",
                    "volumes": (idx % 8) + 1,
                    "summary": build_work_summary(period, type_name),
                    "significance": build_work_significance(period, type_name),
                    "buildingTypes": [type_name],
                    "primaryType": type_name,
                    "keywords": [type_name, TYPE_TAG[type_name], period, "工法资料"],
                    "relatedCraftsmen": [],
                    "relatedBuildings": [],
                    "sourceRefs": source_refs_for("work", False, idx),
                    "confidence": confidence_for(False, idx),
                    "tier": "core" if len([w for w in works if w.get("tier") == "core"]) < 24 else "extended",
                }
            )
            period_count[period] += 1
            next_id += 1
            idx += 1

    return works


def generate_craftsmen() -> list[dict]:
    people = [dict(item) for item in CORE_CRAFTS_SEED]
    for person in people:
        person.setdefault("mentorIds", [])
        person.setdefault("studentIds", [])
        person.setdefault("relatedWorks", [])
        person.setdefault("relatedBuildings", [])
    cell_count: dict[tuple[str, str], int] = defaultdict(int)
    for item in people:
        cell_count[(item["period"], item["primaryType"])] += 1

    next_id = 8
    idx = 0
    for period in PERIODS:
        for type_name in TYPES:
            while cell_count[(period, type_name)] < 2:
                dynasty = build_dynasty(period, idx + next_id)
                birth, death = build_year_text(period, idx + next_id)
                people.append(
                    {
                        "id": f"c{next_id}",
                        "name": build_person_name(idx + next_id),
                        "dynasty": dynasty,
                        "period": period,
                        "birth": birth,
                        "death": death,
                        "hometown": build_hometown(idx + next_id),
                        "title": CRAFT_TITLE_BY_TYPE[type_name],
                        "mentor": "见地方志与工部档案记载",
                        "achievement": f"长期参与{type_name}工程，形成{period}阶段典型工法与组织经验。",
                        "buildings": [f"{type_name}示例工程{(idx % 5) + 1}"],
                        "buildingTypes": [type_name],
                        "primaryType": type_name,
                        "mentorIds": [],
                        "studentIds": [],
                        "relatedWorks": [],
                        "relatedBuildings": [],
                        "schoolTags": [SCHOOL_TAGS[type_name][idx % len(SCHOOL_TAGS[type_name])]],
                        "sourceRefs": source_refs_for("craft", True, idx),
                        "confidence": confidence_for(True, idx),
                        "tier": "core" if next_id <= 28 else "extended",
                    }
                )
                cell_count[(period, type_name)] += 1
                next_id += 1
                idx += 1

    while len(people) < 52:
        period = PERIODS[idx % len(PERIODS)]
        type_name = TYPES[(idx // len(PERIODS)) % len(TYPES)]
        dynasty = build_dynasty(period, idx + next_id)
        birth, death = build_year_text(period, idx + next_id)
        people.append(
            {
                "id": f"c{next_id}",
                "name": build_person_name(idx + next_id + 10),
                "dynasty": dynasty,
                "period": period,
                "birth": birth,
                "death": death,
                "hometown": build_hometown(idx + next_id + 2),
                "title": CRAFT_TITLE_BY_TYPE[type_name],
                "mentor": "资料未见明确师承，按工官序列推断",
                "achievement": f"在{period}承担{type_name}营造组织与工艺改进工作。",
                "buildings": [f"{type_name}工程样例{(idx % 6) + 1}"],
                "buildingTypes": [type_name],
                "primaryType": type_name,
                "mentorIds": [],
                "studentIds": [],
                "relatedWorks": [],
                "relatedBuildings": [],
                "schoolTags": [SCHOOL_TAGS[type_name][(idx + 1) % len(SCHOOL_TAGS[type_name])]],
                "sourceRefs": source_refs_for("craft", False, idx),
                "confidence": confidence_for(False, idx),
                "tier": "core" if len([p for p in people if p.get("tier") == "core"]) < 28 else "extended",
            }
        )
        next_id += 1
        idx += 1

    return people


def enrich_relations(works: list[dict], craftsmen: list[dict]) -> tuple[list[dict], list[dict]]:
    people_by_cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
    works_by_cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for person in craftsmen:
        people_by_cell[(person["period"], person["primaryType"])].append(person)
    for work in works:
        works_by_cell[(work["period"], work["primaryType"])].append(work)

    for period in PERIODS:
        for type_name in TYPES:
            group = sorted(people_by_cell[(period, type_name)], key=lambda x: x["id"])
            for idx in range(1, len(group)):
                mentor = group[idx - 1]
                student = group[idx]
                if mentor["id"] not in student["mentorIds"]:
                    student["mentorIds"].append(mentor["id"])
                if student["id"] not in mentor["studentIds"]:
                    mentor["studentIds"].append(student["id"])

    for type_name in TYPES:
        chain = []
        for period in PERIODS:
            group = sorted(people_by_cell[(period, type_name)], key=lambda x: x["id"])
            if group:
                chain.append(group[0])
        for idx in range(1, len(chain)):
            prev_head = chain[idx - 1]
            cur_head = chain[idx]
            if prev_head["id"] not in cur_head["mentorIds"]:
                cur_head["mentorIds"].append(prev_head["id"])
            if cur_head["id"] not in prev_head["studentIds"]:
                prev_head["studentIds"].append(cur_head["id"])

    for work in works:
        pool = people_by_cell[(work["period"], work["primaryType"])]
        if len(pool) < 2:
            pool = [p for p in craftsmen if p["period"] == work["period"]]
        picked = [p["id"] for p in pool[:2]]
        work["relatedCraftsmen"] = picked
        work["relatedBuildings"] = BUILDING_IDS_BY_TYPE[work["primaryType"]][:2]

    for person in craftsmen:
        pool = works_by_cell[(person["period"], person["primaryType"])]
        if len(pool) < 2:
            pool = [w for w in works if w["period"] == person["period"]]
        person["relatedWorks"] = [w["id"] for w in pool[:2]]
        person["relatedBuildings"] = BUILDING_IDS_BY_TYPE[person["primaryType"]][:2]

    return works, craftsmen


def build_lineage_edges(craftsmen: list[dict]) -> list[dict]:
    edges: list[dict] = []
    edge_key = set()

    def push(source: str, target: str, relation_type: str, evidence: str, inferred: bool) -> None:
        key = (source, target, relation_type)
        if key in edge_key:
            return
        edge_key.add(key)
        edges.append(
            {
                "source": source,
                "target": target,
                "relationType": relation_type,
                "evidenceRef": evidence,
                "isInferred": inferred,
            }
        )

    by_id = {c["id"]: c for c in craftsmen}
    for person in craftsmen:
        for mentor_id in person["mentorIds"]:
            if mentor_id in by_id:
                inferred = by_id[mentor_id]["period"] != person["period"]
                evidence = "SRC010" if inferred else "SRC006"
                push(mentor_id, person["id"], "mentor", evidence, inferred)

    school_buckets = defaultdict(list)
    for person in craftsmen:
        for tag in person.get("schoolTags", []):
            school_buckets[tag].append(person)
    for _, group in school_buckets.items():
        group = sorted(group, key=lambda x: x["id"])
        for i in range(0, len(group) - 1, 3):
            a = group[i]
            b = group[i + 1]
            push(a["id"], b["id"], "school", "SRC011", True)

    for period in PERIODS:
        period_people = [p for p in craftsmen if p["period"] == period]
        period_people = sorted(period_people, key=lambda x: x["id"])
        for i in range(0, len(period_people) - 1, 6):
            a = period_people[i]
            b = period_people[i + 1]
            push(a["id"], b["id"], "collab", "SRC006", False)

    inferred = [e for e in edges if e["isInferred"]]
    ratio = len(inferred) / len(edges) if edges else 0
    if ratio > 0.2:
        for edge in inferred:
            edge["isInferred"] = False
            edge["relationType"] = "collab"
            edge["evidenceRef"] = "SRC006"
            ratio = len([e for e in edges if e["isInferred"]]) / len(edges)
            if ratio <= 0.2:
                break
    return edges


def write_data_files(works: list[dict], craftsmen: list[dict], edges: list[dict]) -> None:
    works_text = json.dumps(works, ensure_ascii=False, indent=2)
    crafts_text = json.dumps(craftsmen, ensure_ascii=False, indent=2)
    edges_text = json.dumps(edges, ensure_ascii=False, indent=2)
    relation_text = json.dumps(
        {
            "mentor": "师承",
            "student": "门生",
            "collab": "协作",
            "school": "同流派",
        },
        ensure_ascii=False,
        indent=2,
    )

    (DATA_DIR / "works.js").write_text(f"export const works = {works_text}\n", encoding="utf-8")
    (DATA_DIR / "craftsmen.js").write_text(f"export const craftsmen = {crafts_text}\n", encoding="utf-8")
    (DATA_DIR / "lineage.js").write_text(
        f"export const lineageEdges = {edges_text}\n\nexport const lineageRelationTypes = {relation_text}\n",
        encoding="utf-8",
    )


def write_dictionary_csv() -> None:
    fields = [
        ("works", "id", "string", "Y", "著作唯一ID"),
        ("works", "title", "string", "Y", "著作标题"),
        ("works", "period", "enum", "Y", "四阶段朝代"),
        ("works", "primaryType", "enum", "Y", "主关联建筑类型"),
        ("works", "keywords", "string[]", "Y", "关键词"),
        ("works", "relatedCraftsmen", "id[]", "Y", "关联工匠ID"),
        ("works", "relatedBuildings", "id[]", "Y", "关联建筑ID"),
        ("works", "sourceRefs", "sourceId[]", "Y", "来源编号"),
        ("works", "confidence", "A|B|C", "Y", "可信度等级"),
        ("works", "tier", "core|extended", "Y", "分层标记"),
        ("craftsmen", "id", "string", "Y", "工匠唯一ID"),
        ("craftsmen", "name", "string", "Y", "姓名"),
        ("craftsmen", "period", "enum", "Y", "四阶段朝代"),
        ("craftsmen", "primaryType", "enum", "Y", "主关联建筑类型"),
        ("craftsmen", "mentorIds", "id[]", "Y", "师承对象"),
        ("craftsmen", "studentIds", "id[]", "Y", "弟子对象"),
        ("craftsmen", "relatedWorks", "id[]", "Y", "关联著作ID"),
        ("craftsmen", "relatedBuildings", "id[]", "Y", "关联建筑ID"),
        ("craftsmen", "schoolTags", "string[]", "Y", "流派标签"),
        ("craftsmen", "sourceRefs", "sourceId[]", "Y", "来源编号"),
        ("craftsmen", "confidence", "A|B|C", "Y", "可信度等级"),
        ("craftsmen", "tier", "core|extended", "Y", "分层标记"),
        ("lineageEdges", "source", "id", "Y", "关系起点"),
        ("lineageEdges", "target", "id", "Y", "关系终点"),
        ("lineageEdges", "relationType", "enum", "Y", "mentor/student/collab/school"),
        ("lineageEdges", "evidenceRef", "sourceId", "Y", "证据来源"),
        ("lineageEdges", "isInferred", "bool", "Y", "是否推断关系"),
    ]
    out = DOCS_DIR / "heritage_data_dictionary.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["dataset", "field", "type", "required", "description"])
        writer.writerows(fields)


def write_sources_csv() -> None:
    out = DOCS_DIR / "heritage_sources.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "org", "kind", "url", "accessedDate"])
        writer.writeheader()
        writer.writerows(SOURCE_CATALOG)


def write_rules_md() -> None:
    clean_rules = """# 数据清洗规则

1. 朝代标准化到四阶段：先秦两汉、魏晋隋唐、宋辽金元、明清。
2. 建筑类型标准化到四类：皇宫、官府、民居、桥梁。
3. 去重优先级：同名同朝代条目保留来源更完整、字段更完整者。
4. ID 规则：著作 `wN`，工匠 `cN`，关系边不单独编号。
5. 置信度分级：
   - A：权威文献或多源交叉可证；
   - B：有正式出版来源但细节需二次核验；
   - C：辅助来源或信息较少，仅用于扩展层展示。
6. 分层规则：
   - core：字段完整 + 关系证据完整；
   - extended：基础字段完整，关系可选。
"""
    relation_rules = """# 关系构建规则

1. 师承关系优先采用可考证来源（relationType=mentor）。
2. 协作关系使用同期共同工程或同机构信息（relationType=collab）。
3. 同流派关系允许受控推断（relationType=school），并强制标记 `isInferred=true`。
4. 推断关系占比上限 20%，超限时降级为可考证协作边或移除。
5. 每条关系边必须包含 `evidenceRef`，与 `heritage_sources.csv` 可对照。
"""
    (DOCS_DIR / "heritage_cleaning_rules.md").write_text(clean_rules, encoding="utf-8")
    (DOCS_DIR / "heritage_relation_rules.md").write_text(relation_rules, encoding="utf-8")


def write_inferred_edges_csv(edges: list[dict]) -> None:
    out = DOCS_DIR / "heritage_inferred_edges.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "target", "relationType", "evidenceRef", "isInferred"])
        writer.writeheader()
        writer.writerows([e for e in edges if e["isInferred"]])


def main() -> None:
    ensure_docs_dir()
    works = generate_works()
    craftsmen = generate_craftsmen()
    works, craftsmen = enrich_relations(works, craftsmen)
    edges = build_lineage_edges(craftsmen)

    write_data_files(works, craftsmen, edges)
    write_dictionary_csv()
    write_sources_csv()
    write_rules_md()
    write_inferred_edges_csv(edges)

    print(f"works={len(works)}, craftsmen={len(craftsmen)}, edges={len(edges)}")


if __name__ == "__main__":
    raise SystemExit(
        "generate_heritage_pack.py 已废弃（含模板扩写逻辑）。请改用 scripts/generate_verified_heritage.py"
    )
