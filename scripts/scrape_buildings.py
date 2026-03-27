"""
爬取全国重点文物保护单位中的古建筑数据
来源：国家文物局 https://www.ncha.gov.cn
筛选：类别为"古建筑"，时间在1911年以前
输出：scripts/scraped_buildings.json
"""

import requests
import json
import time
import re
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 各批次全国重点文物保护单位列表页
BATCH_URLS = [
    # 第一批到第八批古建筑
    "https://www.ncha.gov.cn/col/col2270/index.html",
]

# 备用：直接用维基百科的全国重点文物保护单位列表（结构化更好）
WIKI_URLS = [
    "https://zh.wikipedia.org/wiki/第一批全国重点文物保护单位",
    "https://zh.wikipedia.org/wiki/第二批全国重点文物保护单位",
    "https://zh.wikipedia.org/wiki/第三批全国重点文物保护单位",
    "https://zh.wikipedia.org/wiki/第四批全国重点文物保护单位",
    "https://zh.wikipedia.org/wiki/第五批全国重点文物保护单位",
    "https://zh.wikipedia.org/wiki/第六批全国重点文物保护单位",
    "https://zh.wikipedia.org/wiki/第七批全国重点文物保护单位",
    "https://zh.wikipedia.org/wiki/第八批全国重点文物保护单位",
]

# 排除关键词（庙宇、宝塔、1911年后）
EXCLUDE_KEYWORDS = ['寺', '庙', '塔', '教堂', '清真寺', '喇嘛', '佛', '观音', '菩萨', '神祠', '祠堂']

# 保留关键词（民居、官府、皇宫、桥梁）
TYPE_KEYWORDS = {
    '皇宫': ['宫', '故宫', '皇宫', '行宫', '离宫', '王府'],
    '官府': ['府', '衙', '署', '官署', '总督', '巡抚', '县衙', '城楼', '城墙', '城址'],
    '民居': ['民居', '大院', '村落', '古村', '宅', '庄园', '会馆', '书院'],
    '桥梁': ['桥'],
}

def guess_type(name):
    for t, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return t
    return None

def should_exclude(name):
    for kw in EXCLUDE_KEYWORDS:
        if kw in name:
            return True
    return False

def scrape_wiki_batch(url, batch_name):
    results = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        # 维基百科表格结构：找所有wikitable
        tables = soup.find_all('table', class_='wikitable')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) < 3:
                    continue
                texts = [c.get_text(strip=True) for c in cols]

                # 找包含"古建筑"的行
                row_text = ' '.join(texts)
                if '古建筑' not in row_text:
                    continue

                # 提取名称（通常第1或第2列）
                name = texts[0] if texts[0] else texts[1]
                name = re.sub(r'\[.*?\]', '', name).strip()

                # 提取省份
                province = ''
                for t in texts:
                    provinces = ['北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
                                '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
                                '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
                                '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']
                    for p in provinces:
                        if p in t:
                            province = p
                            break
                    if province:
                        break

                if not name or should_exclude(name):
                    continue

                btype = guess_type(name)
                if not btype:
                    continue

                results.append({
                    'name': name,
                    'type': btype,
                    'province': province,
                    'batch': batch_name,
                    'lat': None,
                    'lng': None,
                })

        print(f"  {batch_name}: 找到 {len(results)} 条古建筑")
    except Exception as e:
        print(f"  {batch_name} 失败: {e}")

    return results

all_buildings = []
batch_names = ['第一批', '第二批', '第三批', '第四批', '第五批', '第六批', '第七批', '第八批']

for url, name in zip(WIKI_URLS, batch_names):
    print(f"爬取 {name}...")
    data = scrape_wiki_batch(url, name)
    all_buildings.extend(data)
    time.sleep(1)

# 去重
seen = set()
unique = []
for b in all_buildings:
    if b['name'] not in seen:
        seen.add(b['name'])
        unique.append(b)

print(f"\n总计: {len(unique)} 条（去重后）")

# 按省份统计
province_count = {}
for b in unique:
    p = b['province'] or '未知'
    province_count[p] = province_count.get(p, 0) + 1

print("\n省份分布:")
for p, c in sorted(province_count.items(), key=lambda x: -x[1]):
    print(f"  {p}: {c}条")

with open('scripts/scraped_buildings.json', 'w', encoding='utf-8') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 scripts/scraped_buildings.json")
