"""
用Claude API批量生成建筑简介
"""

import json
import time
import sys
from openai import OpenAI

sys.stdout.reconfigure(encoding='utf-8')

# 配置
API_KEY = input("请输入你的API Key: ").strip()
BASE_URL = "https://codeapi.icu/"
MODEL = "claude-opus-4-5"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 读取建筑数据
with open('src/data/buildings_full.json', encoding='utf-8') as f:
    buildings = json.load(f)

# 断点续爬
try:
    with open('scripts/descriptions.json', encoding='utf-8') as f:
        results = json.load(f)
    print(f"已有 {len(results)} 条，继续...")
except:
    results = {}

def generate_desc(name, btype, dynasty, province, city):
    prompt = f"""请为以下中国古代建筑写一段200-250字的专业简介：

建筑名称：{name}
建筑类型：{btype}
朝代：{dynasty}
所在地：{province}{city}

要求：
1. 介绍建筑的历史背景、建造年代、规模特点
2. 说明其建筑艺术价值和历史文化意义
3. 语言简洁专业，适合文化展览
4. 不要使用"据悉"、"相传"等不确定词汇
5. 直接输出简介内容，不要加标题或前缀"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  API错误: {e}")
        return ''

total = len(buildings)
new_count = 0

for i, b in enumerate(buildings):
    name = b['name']
    existing = results.get(name, '')

    # 跳过已有足够长简介的
    if len(existing) > 150:
        continue

    print(f"[{i+1}/{total}] {name} ({b.get('dynasty','')} {b.get('type','')})")
    desc = generate_desc(
        name,
        b.get('type', ''),
        b.get('dynasty', ''),
        b.get('province', ''),
        b.get('city', '')
    )

    if desc:
        results[name] = desc
        print(f"  ✓ {len(desc)}字: {desc[:60]}...")
    else:
        results[name] = existing or b.get('description', '')
        print(f"  - 保留原简介")

    new_count += 1
    if new_count % 10 == 0:
        with open('scripts/descriptions.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  [保存] 共{len(results)}条")

    time.sleep(0.5)

with open('scripts/descriptions.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

good = sum(1 for v in results.values() if len(v) > 150)
print(f"\n完成！共{len(results)}条，有效简介(>150字): {good}条")
