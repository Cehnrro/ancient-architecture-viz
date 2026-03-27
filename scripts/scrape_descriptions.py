"""
用百度搜索结果摘要补充建筑简介
"""

import json
import time
import re
import sys
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

with open('src/data/buildings_full.json', encoding='utf-8') as f:
    buildings = json.load(f)

try:
    with open('scripts/descriptions.json', encoding='utf-8') as f:
        results = json.load(f)
except:
    results = {}

def get_desc(name, province):
    try:
        query = f"{name} {province} 古建筑 简介"
        url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        # 抓取搜索结果摘要
        for sel in ['.c-abstract', '.content-right_8Zs40', '[class*="abstract"]', '[class*="content"]']:
            els = soup.select(sel)
            for el in els:
                text = el.get_text(strip=True)
                text = re.sub(r'\[.*?\]|\d{4}-\d{2}-\d{2}', '', text).strip()
                if len(text) > 80:
                    return text[:500]
        return ''
    except Exception as e:
        print(f"  异常: {e}")
        return ''

total = len(buildings)
new_count = 0

for i, b in enumerate(buildings):
    name = b['name']
    existing = results.get(name, '')

    # 跳过已有足够长简介的
    if len(existing) > 150:
        continue

    print(f"[{i+1}/{total}] {name}")
    desc = get_desc(name, b.get('province', ''))

    if len(desc) > len(existing):
        results[name] = desc
        print(f"  ✓ {len(desc)}字: {desc[:60]}...")
    else:
        if not existing:
            results[name] = b.get('description', '')
        print(f"  - 保留原({len(results.get(name,''))}字)")

    new_count += 1
    if new_count % 10 == 0:
        with open('scripts/descriptions.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  [保存] 共{len(results)}条")

    time.sleep(1.5)

with open('scripts/descriptions.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

good = sum(1 for v in results.values() if len(v) > 150)
print(f"\n完成！共{len(results)}条，有效简介(>150字): {good}条")
