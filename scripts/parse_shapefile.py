"""
解析国家重点文物保护单位Shapefile数据
筛选古建筑类别（民居/官府/皇宫/桥梁），排除庙宇/宝塔
坐标直接从文件读取（WGS84），无需调用API
输出：scripts/scraped_buildings.json
"""

import shapefile
import json
import re

EXCLUDE = ['寺', '庙', '塔', '教堂', '清真', '喇嘛', '佛', '观音', '菩萨', '神祠', '道观', '庵', '阁', '亭', '碑', '陵', '墓', '窟', '洞']
WHITELIST = ['城楼', '城墙', '城门', '书院', '会馆', '鼓楼', '钟楼', '牌楼']

TYPE_MAP = {
    '皇宫': ['宫', '故宫', '皇宫', '行宫', '离宫', '王府', '皇城', '御'],
    '官府': ['府', '衙', '署', '官署', '总督', '巡抚', '县衙', '城楼', '城墙', '城址', '城门', '关城', '古城', '鼓楼', '钟楼', '牌楼', '城堡'],
    '民居': ['民居', '大院', '村落', '古村', '宅', '庄园', '会馆', '书院', '老街', '古镇', '民宅', '故居', '住宅', '院落'],
    '桥梁': ['桥'],
}

# 古建筑类别关键词（HISTORICCA/Ntype字段）
ARCH_TYPES = ['古建筑', '近现代重要史迹及代表性建筑']

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

def guess_type(name):
    if '桥' in name:
        return '桥梁'
    for t, keywords in TYPE_MAP.items():
        for kw in keywords:
            if kw in name:
                return t
    return None

def should_exclude(name):
    for w in WHITELIST:
        if w in name:
            return False
    for kw in EXCLUDE:
        if kw in name:
            return True
    return False

def decode_field(val):
    if isinstance(val, bytes):
        for enc in ['utf-8', 'gbk', 'gb2312']:
            try:
                return val.decode(enc).strip()
            except:
                continue
        return ''
    if isinstance(val, str):
        return val.strip()
    return str(val) if val else ''

# 读取Shapefile
sf = shapefile.Reader('scripts/国家重点文物保护单位空间分布.shp', encoding='utf-8')
fields = [f[0] for f in sf.fields[1:]]
print(f"总记录数: {len(sf)}")

results = []
skipped_type = 0
skipped_exclude = 0
skipped_no_type = 0

for shaperec in sf.iterShapeRecords():
    rec = shaperec.record
    data = {}
    for i, f in enumerate(fields):
        data[f] = decode_field(rec[i]) if i < len(rec) else ''

    name = data.get('NAME', '') or data.get('Nname_Norm', '')
    ntype = data.get('Ntype', '') or data.get('HISTORICCA', '')
    province = data.get('Nprovince', '') or data.get('ADMINIST_1', '')
    city = data.get('Nprefectur', '') or data.get('ADMINIST_1', '')
    county = data.get('Ncounty', '')
    brief = data.get('Nbrief', '')
    batch_num = data.get('PERMISSION', '')

    # dynasty直接用utf-8读取
    raw_dynasty = data.get('UNEARTHDYN', '')
    dynasty = raw_dynasty

    # 坐标
    try:
        lng = float(data.get('CENTERLONG', 0))
        lat = float(data.get('CENTERLATI', 0))
    except:
        lng, lat = 0, 0

    if not name:
        continue

    # 排除庙宇宝塔
    if should_exclude(name):
        skipped_exclude += 1
        continue

    # 判断四类建筑
    btype = guess_type(name)
    if not btype:
        skipped_no_type += 1
        continue

    # 清理省份名称
    province = re.sub(r'省|市|自治区|维吾尔|壮族|回族|藏族', '', province).strip()
    if '内蒙古' in province:
        province = '内蒙古'
    elif '新疆' in province:
        province = '新疆'
    elif '西藏' in province:
        province = '西藏'
    elif '广西' in province:
        province = '广西'
    elif '宁夏' in province:
        province = '宁夏'

    # 批次映射
    batch_map = {1: '第一批', 2: '第二批', 3: '第三批', 4: '第四批',
                 5: '第五批', 6: '第六批', 7: '第七批', 8: '第八批'}
    try:
        batch = batch_map.get(int(batch_num), f'第{batch_num}批')
    except:
        batch = ''

    period = map_period(dynasty)

    results.append({
        'name': name,
        'type': btype,
        'province': province,
        'city': city,
        'dynasty': dynasty,
        'period': period,
        'lat': round(lat, 6),
        'lng': round(lng, 6),
        'batch': batch,
        'isFeatured': False,
        'description': brief if brief else '',
        'features': [],
        'imageUrl': '',
    })

print(f"\n解析完成:")
print(f"  保留: {len(results)} 条")
print(f"  跳过（非古建筑）: {skipped_type} 条")
print(f"  跳过（庙宇宝塔）: {skipped_exclude} 条")
print(f"  跳过（无法分类）: {skipped_no_type} 条")

# 类型分布
type_count = {}
province_count = {}
for b in results:
    type_count[b['type']] = type_count.get(b['type'], 0) + 1
    p = b['province'] or '未知'
    province_count[p] = province_count.get(p, 0) + 1

print("\n类型分布:")
for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}条")

print("\n省份分布:")
for p, c in sorted(province_count.items(), key=lambda x: -x[1]):
    print(f"  {p}: {c}条")

with open('scripts/scraped_buildings.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 scripts/scraped_buildings.json")
