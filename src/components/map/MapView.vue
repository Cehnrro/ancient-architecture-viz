<script setup>
import { onMounted, onUnmounted, watch, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  buildings: { type: Array, default: () => [] },
  selectedPeriod: { type: String, default: 'all' },
})

const emit = defineEmits(['select-building'])

const mapContainer = ref(null)
let map = null
let markersLayer = null
let provinceLayer = null

// 建筑类型颜色
const typeColors = {
  '皇宫': '#e8c96d',
  '官府': '#00d4ff',
  '民居': '#81c784',
  '桥梁': '#ff8a65',
}

// 代表性建筑SVG图标（40px，中国传统建筑轮廓风格）
const featuredSVG = {
  '皇宫': (color) => `
    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
      <line x1="20" y1="2" x2="20" y2="7" stroke="${color}" stroke-width="1.5"/>
      <polygon points="4,16 20,6 36,16" fill="${color}" opacity="0.15" stroke="${color}" stroke-width="1.5"/>
      <line x1="2" y1="16" x2="38" y2="16" stroke="${color}" stroke-width="2"/>
      <rect x="5" y="16" width="6" height="12" fill="none" stroke="${color}" stroke-width="1.2"/>
      <rect x="17" y="16" width="6" height="12" fill="none" stroke="${color}" stroke-width="1.2"/>
      <rect x="29" y="16" width="6" height="12" fill="none" stroke="${color}" stroke-width="1.2"/>
      <line x1="2" y1="28" x2="38" y2="28" stroke="${color}" stroke-width="2"/>
      <rect x="14" y="28" width="12" height="8" fill="none" stroke="${color}" stroke-width="1.2"/>
      <line x1="2" y1="36" x2="38" y2="36" stroke="${color}" stroke-width="1.5"/>
    </svg>`,
  '官府': (color) => `
    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="3" width="34" height="34" fill="none" stroke="${color}" stroke-width="1.5" opacity="0.4"/>
      <line x1="20" y1="3" x2="20" y2="8" stroke="${color}" stroke-width="1.5"/>
      <line x1="3" y1="14" x2="37" y2="14" stroke="${color}" stroke-width="1.8"/>
      <line x1="3" y1="8" x2="37" y2="8" stroke="${color}" stroke-width="1.2" opacity="0.6"/>
      <rect x="8" y="14" width="4" height="23" fill="none" stroke="${color}" stroke-width="1.2"/>
      <rect x="28" y="14" width="4" height="23" fill="none" stroke="${color}" stroke-width="1.2"/>
      <rect x="15" y="20" width="10" height="17" fill="${color}" opacity="0.15" stroke="${color}" stroke-width="1.5"/>
      <line x1="20" y1="20" x2="20" y2="37" stroke="${color}" stroke-width="1"/>
      <line x1="3" y1="37" x2="37" y2="37" stroke="${color}" stroke-width="1.8"/>
    </svg>`,
  '民居': (color) => `
    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
      <polygon points="20,4 4,18 36,18" fill="${color}" opacity="0.15" stroke="${color}" stroke-width="1.5"/>
      <rect x="5" y="18" width="30" height="16" fill="none" stroke="${color}" stroke-width="1.5"/>
      <rect x="16" y="24" width="8" height="10" fill="none" stroke="${color}" stroke-width="1.2"/>
      <rect x="8" y="20" width="6" height="6" fill="none" stroke="${color}" stroke-width="1"/>
      <rect x="26" y="20" width="6" height="6" fill="none" stroke="${color}" stroke-width="1"/>
      <line x1="3" y1="34" x2="37" y2="34" stroke="${color}" stroke-width="1.5"/>
    </svg>`,
  '桥梁': (color) => `
    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
      <path d="M2,28 Q20,8 38,28" fill="${color}" opacity="0.1" stroke="${color}" stroke-width="2"/>
      <line x1="2" y1="28" x2="38" y2="28" stroke="${color}" stroke-width="2"/>
      <line x1="2" y1="28" x2="2" y2="36" stroke="${color}" stroke-width="2"/>
      <line x1="38" y1="28" x2="38" y2="36" stroke="${color}" stroke-width="2"/>
      <line x1="11" y1="28" x2="11" y2="20" stroke="${color}" stroke-width="1.2"/>
      <line x1="20" y1="28" x2="20" y2="14" stroke="${color}" stroke-width="1.2"/>
      <line x1="29" y1="28" x2="29" y2="20" stroke="${color}" stroke-width="1.2"/>
      <line x1="2" y1="36" x2="38" y2="36" stroke="${color}" stroke-width="1.5"/>
    </svg>`,
}

function createMarker(building) {
  const color = typeColors[building.type] || '#ffffff'

  let icon
  if (building.isFeatured) {
    // 代表性建筑：大图标+强发光
    const svgFn = featuredSVG[building.type]
    const svgHtml = svgFn ? svgFn(color) : ''
    icon = L.divIcon({
      className: '',
      html: `<div style="
        width:40px;height:40px;
        filter:drop-shadow(0 0 10px ${color}) drop-shadow(0 0 4px ${color});
        cursor:pointer;
      ">${svgHtml}</div>`,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    })
  } else {
    // 普通建筑：小圆点
    icon = L.divIcon({
      className: '',
      html: `<div style="
        width:8px;height:8px;
        border-radius:50%;
        background:${color};
        opacity:0.6;
        box-shadow:0 0 4px ${color}88;
        cursor:pointer;
      "></div>`,
      iconSize: [8, 8],
      iconAnchor: [4, 4],
    })
  }

  const marker = L.marker([building.lat, building.lng], { icon, zIndexOffset: 100 })

  marker.bindTooltip(`
    <div style="
      background: #161b22;
      border: 1px solid ${color}88;
      color: #e6d5b8;
      padding: 8px 12px;
      font-family: 'Noto Serif SC', serif;
      font-size: 12px;
      border-radius: 2px;
      min-width: 120px;
    ">
      <div style="color:${color};font-weight:600;font-size:14px">${building.name}</div>
      <div style="color:#8b8680;margin-top:3px">${building.dynasty} · ${building.type} · ${building.province}</div>
    </div>
  `, {
    className: 'custom-tooltip',
    direction: 'top',
    offset: [0, -8],
  })

  marker.on('click', () => emit('select-building', building))
  return marker
}

function renderMarkers() {
  if (!map) return
  if (markersLayer) markersLayer.clearLayers()
  props.buildings.forEach(b => {
    const marker = createMarker(b)
    markersLayer.addLayer(marker)
  })
}

// 按省份聚合建筑数据
function getBuildingsByProvince() {
  const map = {}
  props.buildings.forEach(b => {
    if (!map[b.province]) map[b.province] = { 皇宫: [], 官府: [], 民居: [], 桥梁: [] }
    if (map[b.province][b.type]) map[b.province][b.type].push(b.name)
  })
  return map
}

function initProvinceLayer(geojson) {
  const buildingsByProvince = getBuildingsByProvince()

  provinceLayer = L.geoJSON(geojson, {
    style: {
      fillColor: '#1a2535',
      fillOpacity: 0.4,
      color: '#c9a84c44',
      weight: 1,
    },
    onEachFeature(feature, layer) {
      const name = feature.properties.name
      const data = buildingsByProvince[name]

      layer.on('mouseover', function(e) {
        this.setStyle({ fillOpacity: 0.65, color: '#c9a84c88', weight: 1.5 })

        if (data) {
          const total = Object.values(data).flat().length
          const rows = Object.entries(data)
            .filter(([, arr]) => arr.length > 0)
            .map(([type, arr]) => `
              <div style="display:flex;justify-content:space-between;gap:16px;margin-top:4px">
                <span style="color:${typeColors[type]}">${type}</span>
                <span style="color:#e6d5b8">${arr.length}处</span>
              </div>
              <div style="color:#8b8680;font-size:11px;margin-top:2px">${arr.slice(0,3).join('、')}${arr.length > 3 ? '…' : ''}</div>
            `).join('')

          layer.bindTooltip(`
            <div style="
              background:#161b22;
              border:1px solid #7a6030;
              color:#e6d5b8;
              padding:10px 14px;
              font-family:'Noto Serif SC',serif;
              font-size:12px;
              border-radius:2px;
              min-width:160px;
            ">
              <div style="color:#e8c96d;font-size:14px;font-weight:600;margin-bottom:6px">${name}</div>
              <div style="color:#8b8680">共 ${total} 处古建筑</div>
              ${rows}
            </div>
          `, { className: 'custom-tooltip', sticky: true }).openTooltip(e.latlng)
        }
      })

      layer.on('mouseout', function() {
        this.setStyle({ fillOpacity: 0.4, color: '#c9a84c44', weight: 1 })
        layer.closeTooltip()
      })
    }
  }).addTo(map)
}

onMounted(async () => {
  map = L.map(mapContainer.value, {
    center: [35.5, 108],
    zoom: 5,
    zoomControl: false,
    attributionControl: false,
    minZoom: 4,
    maxZoom: 12,
  })

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
    maxZoom: 18,
  }).addTo(map)

  L.control.attribution({ position: 'bottomleft' })
    .addAttribution('地图来源：<a href="https://www.tianditu.gov.cn/" target="_blank">国家地理信息公共服务平台天地图</a>')
    .addTo(map)

  L.control.zoom({ position: 'bottomright' }).addTo(map)

  // 加载省份GeoJSON
  try {
    const res = await fetch('/china-provinces.json')
    const geojson = await res.json()
    initProvinceLayer(geojson)
  } catch(e) {
    console.warn('省份数据加载失败', e)
  }

  markersLayer = L.layerGroup().addTo(map)
  renderMarkers()
})

onUnmounted(() => {
  if (map) { map.remove(); map = null }
})

watch(() => props.buildings, () => {
  renderMarkers()
  if (provinceLayer && map) {
    provinceLayer.remove()
    fetch('/china-provinces.json').then(r => r.json()).then(initProvinceLayer)
  }
}, { deep: true })
</script>

<template>
  <div ref="mapContainer" class="map-container" />
</template>

<style>
.map-container {
  width: 100%;
  height: 100%;
}

.leaflet-container {
  background: #0d1117 !important;
}

.custom-tooltip {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.custom-tooltip::before {
  display: none !important;
}

.leaflet-attribution-flag { display: none !important; }

.leaflet-control-attribution {
  background: rgba(13,17,23,0.8) !important;
  color: #8b8680 !important;
  font-size: 10px !important;
  border-top: 1px solid #7a6030 !important;
}

.leaflet-control-attribution a {
  color: #c9a84c !important;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
}
</style>
