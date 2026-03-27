"""
合并数据：
- 18条深度版建筑（buildings.js）保持isFeatured=true
- 285条爬取数据作为普通建筑
- 去重（名称相同则保留深度版）
- 修复乱码dynasty字段
- 输出 src/data/buildings_full.json
"""

import json
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 深度版18条（直接从buildings.js提取关键字段）
featured = [
    {"id":"b1","name":"阿房宫","type":"皇宫","dynasty":"秦","period":"先秦两汉","province":"陕西","city":"西安","lat":34.271101,"lng":108.822496,"isFeatured":True},
    {"id":"b2","name":"未央宫","type":"皇宫","dynasty":"汉","period":"先秦两汉","province":"陕西","city":"西安","lat":34.304562,"lng":108.857417,"isFeatured":True},
    {"id":"b3","name":"汉代干栏式民居","type":"民居","dynasty":"汉","period":"先秦两汉","province":"广西","city":"贵港","lat":23.114501,"lng":109.594809,"isFeatured":True},
    {"id":"b4","name":"南越王宫署遗址","type":"官府","dynasty":"汉","period":"先秦两汉","province":"广东","city":"广州","lat":23.129433,"lng":113.264592,"isFeatured":True},
    {"id":"b5","name":"赵州桥","type":"桥梁","dynasty":"隋","period":"魏晋隋唐","province":"河北","city":"赵县","lat":37.720247,"lng":114.763275,"isFeatured":True},
    {"id":"b6","name":"大明宫","type":"皇宫","dynasty":"唐","period":"魏晋隋唐","province":"陕西","city":"西安","lat":34.342656,"lng":108.935344,"isFeatured":True},
    {"id":"b7","name":"隋唐洛阳城官署","type":"官府","dynasty":"隋唐","period":"魏晋隋唐","province":"河南","city":"洛阳","lat":34.682137,"lng":112.466805,"isFeatured":True},
    {"id":"b8","name":"交河故城民居","type":"民居","dynasty":"唐","period":"魏晋隋唐","province":"新疆","city":"吐鲁番","lat":42.952301,"lng":89.062488,"isFeatured":True},
    {"id":"b9","name":"安平桥","type":"桥梁","dynasty":"宋","period":"宋辽金元","province":"福建","city":"晋江","lat":24.784472,"lng":118.547508,"isFeatured":True},
    {"id":"b10","name":"卢沟桥","type":"桥梁","dynasty":"金","period":"宋辽金元","province":"北京","city":"北京","lat":39.848959,"lng":116.212675,"isFeatured":True},
    {"id":"b11","name":"开封府","type":"官府","dynasty":"宋","period":"宋辽金元","province":"河南","city":"开封","lat":34.790491,"lng":114.341037,"isFeatured":True},
    {"id":"b12","name":"徽派民居","type":"民居","dynasty":"宋","period":"宋辽金元","province":"安徽","city":"黄山","lat":30.005235,"lng":117.985008,"isFeatured":True},
    {"id":"b13","name":"故宫","type":"皇宫","dynasty":"明清","period":"明清","province":"北京","city":"北京","lat":39.916348,"lng":116.390803,"isFeatured":True},
    {"id":"b14","name":"南京明故宫","type":"皇宫","dynasty":"明","period":"明清","province":"江苏","city":"南京","lat":32.041589,"lng":118.813177,"isFeatured":True},
    {"id":"b15","name":"乔家大院","type":"民居","dynasty":"清","period":"明清","province":"山西","city":"晋中","lat":37.365732,"lng":112.322749,"isFeatured":True},
    {"id":"b16","name":"西递/宏村","type":"民居","dynasty":"明清","period":"明清","province":"安徽","city":"黄山","lat":29.905498,"lng":117.991607,"isFeatured":True},
    {"id":"b17","name":"直隶总督署","type":"官府","dynasty":"清","period":"明清","province":"河北","city":"保定","lat":38.859084,"lng":115.491157,"isFeatured":True},
    {"id":"b18","name":"广济桥","type":"桥梁","dynasty":"明","period":"明清","province":"广东","city":"潮州","lat":23.659146,"lng":116.618634,"isFeatured":True},
]

# 读取爬取数据
with open('scripts/scraped_buildings.json', encoding='utf-8') as f:
    scraped = json.load(f)

# 修复乱码dynasty
def fix_dynasty(val):
    if not val:
        return ''
    try:
        fixed = val.encode('latin-1').decode('utf-8')
        return fixed
    except:
        return val

# 过滤1911年后的建筑
def is_after_1911(dynasty):
    if not dynasty:
        return False
    import re
    years = re.findall(r'\d{4}', dynasty)
    for y in years:
        if int(y) > 1911:
            return True
    return False

# 朝代→时期映射
DYNASTY_PERIOD = {
    '先秦两汉': ['周', '秦', '汉', '春秋', '战国', '商', '夏', '西周', '东周', '西汉', '东汉', '新'],
    '魏晋隋唐': ['魏', '晋', '隋', '唐', '南北朝', '三国', '西晋', '东晋', '北魏', '南朝', '北朝', '五代'],
    '宋辽金元': ['宋', '辽', '金', '元', '北宋', '南宋', '西夏'],
    '明清': ['明', '清'],
}

def map_period(dynasty):
    if not dynasty:
        return ''
    for period, dynasties in DYNASTY_PERIOD.items():
        for d in dynasties:
            if d in dynasty:
                return period
    return ''

# 深度版名称集合（用于去重）
featured_names = {b['name'] for b in featured}

# 处理爬取数据
processed = []
skipped_year = 0
for i, b in enumerate(scraped):
    if b['name'] in featured_names:
        continue
    dynasty = fix_dynasty(b.get('dynasty', ''))
    # 过滤1911年后
    if is_after_1911(dynasty):
        skipped_year += 1
        continue
    period = b.get('period', '') or map_period(dynasty)
    processed.append({
        'id': f'scraped_{i}',
        'name': b['name'],
        'type': b['type'],
        'dynasty': dynasty,
        'period': period,
        'province': b['province'],
        'city': b['city'],
        'lat': b['lat'],
        'lng': b['lng'],
        'batch': b.get('batch', ''),
        'isFeatured': False,
        'description': b.get('description', ''),
        'features': [],
        'imageUrl': '',
        'relatedWorks': [],
        'relatedPersons': [],
    })

# 合并
all_buildings = featured + processed

print(f"深度版: {len(featured)} 条")
print(f"普通版: {len(processed)} 条")
print(f"总计: {len(all_buildings)} 条")

# 省份覆盖
provinces = set(b['province'] for b in all_buildings if b['province'])
print(f"覆盖省份: {len(provinces)} 个")
print(sorted(provinces))

# 类型分布
type_count = {}
for b in all_buildings:
    type_count[b['type']] = type_count.get(b['type'], 0) + 1
print("\n类型分布:")
for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}条")

with open('src/data/buildings_full.json', 'w', encoding='utf-8') as f:
    json.dump(all_buildings, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 src/data/buildings_full.json")
