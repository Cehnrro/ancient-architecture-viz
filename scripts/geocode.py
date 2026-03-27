"""
批量地理编码脚本
使用百度地图地理编码API，将建筑名称+城市转换为经纬度坐标
输出：src/data/buildings_coords.json
"""

import requests
import json
import time

AK = "JcJEzxpta1YxKvzdB8xPPFeXECRujVFF"

# 18个代表性建筑
buildings = [
    {"id": "b1",  "name": "阿房宫遗址",     "city": "西安"},
    {"id": "b2",  "name": "未央宫遗址",     "city": "西安"},
    {"id": "b3",  "name": "贵港汉代干栏式民居", "city": "贵港"},
    {"id": "b4",  "name": "南越王宫署遗址", "city": "广州"},
    {"id": "b5",  "name": "赵州桥",         "city": "赵县"},
    {"id": "b6",  "name": "大明宫遗址",     "city": "西安"},
    {"id": "b7",  "name": "隋唐洛阳城遗址", "city": "洛阳"},
    {"id": "b8",  "name": "交河故城",       "city": "吐鲁番"},
    {"id": "b9",  "name": "安平桥",         "city": "晋江"},
    {"id": "b10", "name": "卢沟桥",         "city": "北京"},
    {"id": "b11", "name": "开封府",         "city": "开封"},
    {"id": "b12", "name": "宏村",           "city": "黄山"},
    {"id": "b13", "name": "故宫",           "city": "北京"},
    {"id": "b14", "name": "南京明故宫遗址", "city": "南京"},
    {"id": "b15", "name": "乔家大院",       "city": "晋中"},
    {"id": "b16", "name": "西递村",         "city": "黄山"},
    {"id": "b17", "name": "直隶总督署",     "city": "保定"},
    {"id": "b18", "name": "广济桥",         "city": "潮州"},
]

# BD09 → WGS84 坐标转换
import math

def bd09_to_wgs84(bd_lng, bd_lat):
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * math.pi * 3000 / 180)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * math.pi * 3000 / 180)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    # GCJ02 → WGS84
    dlat = transform_lat(gcj_lng - 105.0, gcj_lat - 35.0)
    dlng = transform_lng(gcj_lng - 105.0, gcj_lat - 35.0)
    radlat = gcj_lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - 0.00669342162296594323 * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((6335552.717000426 / (magic * sqrtmagic)) * math.pi)
    dlng = (dlng * 180.0) / (6378245.0 / sqrtmagic * math.cos(radlat) * math.pi)
    return round(gcj_lng - dlng, 6), round(gcj_lat - dlat, 6)

def transform_lat(x, y):
    ret = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0/3.0
    ret += (20.0*math.sin(y*math.pi) + 40.0*math.sin(y/3.0*math.pi)) * 2.0/3.0
    ret += (160.0*math.sin(y/12.0*math.pi) + 320*math.sin(y*math.pi/30.0)) * 2.0/3.0
    return ret

def transform_lng(x, y):
    ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0/3.0
    ret += (20.0*math.sin(x*math.pi) + 40.0*math.sin(x/3.0*math.pi)) * 2.0/3.0
    ret += (150.0*math.sin(x/12.0*math.pi) + 300.0*math.sin(x/30.0*math.pi)) * 2.0/3.0
    return ret

def geocode(name, city):
    url = "https://api.map.baidu.com/geocoding/v3/"
    params = {
        "address": name,
        "city": city,
        "output": "json",
        "ak": AK,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data["status"] == 0:
            loc = data["result"]["location"]
            wgs_lng, wgs_lat = bd09_to_wgs84(loc["lng"], loc["lat"])
            return wgs_lat, wgs_lng
        else:
            print(f"  [失败] {name}: status={data['status']}")
            return None, None
    except Exception as e:
        print(f"  [异常] {name}: {e}")
        return None, None

results = {}
for b in buildings:
    print(f"查询: {b['name']} ({b['city']})")
    lat, lng = geocode(b["name"], b["city"])
    if lat:
        results[b["id"]] = {"lat": lat, "lng": lng}
        print(f"  → lat={lat}, lng={lng}")
    time.sleep(0.3)  # 避免频率限制

# 输出结果
output_path = "scripts/coords_result.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n完成！结果已保存到 {output_path}")
print(f"成功: {len(results)}/{len(buildings)}")
