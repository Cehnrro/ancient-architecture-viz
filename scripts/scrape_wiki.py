"""
爬取维基百科全国重点文物保护单位列表（第一批～第八批）
筛选古建筑类别，排除庙宇/宝塔，输出结构化JSON
"""

import requests
import json
import time
import re
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

WIKI_URLS = [
    ("第一批", "https://zh.wikipedia.org/wiki/第一批全国重点文物保护单位"),
    ("第二批", "https://zh.wikipedia.org/wiki/第二批全国重点文物保护单位"),
    ("第三批", "https://zh.wikipedia.org/wiki/第三批全国重点文物保护单位"),
    ("第四批", "https://zh.wikipedia.org/wiki/第四批全国重点文物保护单位"),
    ("第五批", "https://zh.wikipedia.org/wiki/第五批全国重点文物保护单位"),
    ("第六批", "https://zh.wikipedia.org/wiki/第六批全国重点文物保护单位"),
    ("第七批", "https://zh.wikipedia.org/wiki/第七批全国重点文物保护单位"),
    ("第八批", "https://zh.wikipedia.org/wiki/第八批全国重点文物保护单位"),
]

PROVINCES = [
    '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
    '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
    '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
    '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆',
]

# 排除关键词
EXCLUDE = ['寺', '庙', '塔', '教堂', '清真', '喇嘛', '佛', '观音', '菩萨', '神祠', '道观', '祠', '阁', '亭']

# 类型判断关键词
TYPE_MAP = {
    '皇宫': ['宫', '故宫', '皇宫', '行宫', '离宫', '王府', '皇城'],
    '官府': ['府', '衙', '署', '官署', '总督', '巡抚', '县衙', '城楼', '城墙', '城址', '城门', '关城', '古城'],
    '民居': ['民居', '大院', '村落', '古村', '宅', '庄园', '会馆', '书院', '老街', '古镇', '民宅'],
    '桥': ['桥'],
}

def guess_type(name):
    if '桥' in name:
        return '桥梁'
    for t, keywords in TYPE_MAP.items():
        for kw in keywords:
            if kw in name:
                return t
    return None

def should_exclude(name):
    for kw in EXCLUDE:
        if kw in name:
            # 白名单：含排除词但实际是建筑的
            whitelist = ['城楼', '城墙', '城门', '书院', '会馆']
            for w in whitelist:
                if w in name:
                    return False
            return True
    return False

def extract_province(texts):
    for t in texts:
        for p in PROVINCES:
            if p in t:
                return p
    return ''

def scrape_batch(batch_name, url):
    results = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        tables = soup.find_all('table', class_='wikitable')
        for table in tables:
            # 判断这个表格是否是古建筑相关
            table_text = table.get_text()
            if '古建筑' not in table_text:
                continue

            rows = table.find_all('tr')
            current_province = ''

            for row in rows:
                cols = row.find_all(['td', 'th'])
                if not cols:
                    continue

                texts = [re.sub(r'\[.*?\]|\n', '', c.get_text()).strip() for c in cols]
                row_text = ' '.join(texts)

                # 更新当前省份
                for p in PROVINCES:
                    if p in row_text and len(texts[0]) <= 4:
                        current_province = p
                        break

                # 跳过非古建筑行
                if '古建筑' not in row_text:
                    continue

                # 提取名称（通常在前两列）
                name = ''
                for t in texts[:3]:
                    if t and len(t) > 1 and '古建筑' not in t and t not in PROVINCES:
                        name = t
                        break

                if not name or len(name) < 2:
                    continue

                name = re.sub(r'\(.*?\)|（.*?）', '', name).strip()

                if should_exclude(name):
                    continue

                btype = guess_type(name)
                if not btype:
                    continue

                province = extract_province(texts) or current_province

                # 尝试提取朝代信息
                dynasty = ''
                dynasty_keywords = ['秦', '汉', '魏', '晋', '隋', '唐', '宋', '辽', '金', '元', '明', '清']
                for t in texts:
                    for d in dynasty_keywords:
                        if d in t and len(t) <= 6:
                            dynasty = t
                            break
                    if dynasty:
                        break

                results.append({
                    'name': name,
                    'type': btype,
                    'province': province,
                    'city': '',
                    'dynasty': dynasty,
                    'period': '',
                    'lat': None,
                    'lng': None,
                    'batch': batch_name,
                    'isFeatured': False,
                    'description': '',
                    'features': [],
                    'imageUrl': '',
                })

        print(f"  {batch_name}: {len(results)} 条")
    except Exception as e:
        print(f"  {batch_name} 失败: {e}")

    return results

# 朝代→时期映射
def map_period(dynasty):
    if not dynasty:
        return ''
    if any(d in dynasty for d in ['秦', '汉', '周', '春秋', '战国']):
        return '先秦两汉'
    if any(d in dynasty for d in ['魏', '晋', '南北朝', '隋', '唐']):
        return '魏晋隋唐'
    if any(d in dynasty for d in ['宋', '辽', '金', '元']):
        return '宋辽金元'
    if any(d in dynasty for d in ['明', '清']):
        return '明清'
    return ''

all_buildings = []
for batch_name, url in WIKI_URLS:
    print(f"爬取 {batch_name}...")
    data = scrape_batch(batch_name, url)
    all_buildings.extend(data)
    time.sleep(1.5)

# 补充时期字段
for b in all_buildings:
    if not b['period']:
        b['period'] = map_period(b['dynasty'])

# 去重（按名称）
seen = set()
unique = []
for b in all_buildings:
    if b['name'] not in seen:
        seen.add(b['name'])
        unique.append(b)

# 统计
print(f"\n总计: {len(unique)} 条（去重后）")
type_count = {}
province_count = {}
for b in unique:
    type_count[b['type']] = type_count.get(b['type'], 0) + 1
    p = b['province'] or '未知'
    province_count[p] = province_count.get(p, 0) + 1

print("\n类型分布:")
for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}条")

print("\n省份分布（前10）:")
for p, c in sorted(province_count.items(), key=lambda x: -x[1])[:10]:
    print(f"  {p}: {c}条")

with open('scripts/scraped_buildings.json', 'w', encoding='utf-8') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 scripts/scraped_buildings.json")
