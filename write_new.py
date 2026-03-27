
script_part = """\
<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import buildingsData from '../data/buildings_full.json'
import { periods } from '../data/buildings.js'
import MapView from '../components/map/MapView.vue'

const router = useRouter()
const buildings = buildingsData
const activePeriod = ref(sessionStorage.getItem('explorePeriod') || 'all')
const selectedBuilding = ref(null)
const hiddenTypes = ref(new Set())
const pieChart = ref(null)
const ccMapRef = ref(null)
const showOverview = ref(false)
const barRef = ref(null)
const bubbleRef = ref(null)
const stackRef = ref(null)
const ruinsPieRefs = {}
const ruinsPieInstances = {}
const overviewCharts = ref({ bar: null, bubble: null, stack: null })
let chartInstance = null
let ccMapInstance = null

const PERIODS = ['\u5148\u79e6\u4e24\u6c49', '\u9b4f\u664b\u968b\u5510', '\u5b8b\u8fbd\u91d1\u5143', '\u660e\u6e05']
const TYPES = ['\u7687\u5bab', '\u5b98\u5e9c', '\u6c11\u5c45', '\u6865\u6881']
const typeColors = { '\u7687\u5bab': '#e8c96d', '\u5b98\u5e9c': '#00d4ff', '\u6c11\u5c45': '#81c784', '\u6865\u6881': '#ff8a65' }
const TOOLTIP_STYLE = { backgroundColor: '#161b22', borderColor: '#c9a84c44', textStyle: { color: '#e6d5b8', fontSize: 12 } }

watch(activePeriod, val => sessionStorage.setItem('explorePeriod', val))

const periodBuildings = computed(() => {
  if (activePeriod.value === 'all') return buildings
  return buildings.filter(b => b.period === activePeriod.value)
})

const filteredBuildings = computed(() => {
  if (hiddenTypes.value.size === 0) return periodBuildings.value
  return periodBuildings.value.filter(b => !hiddenTypes.value.has(b.type))
})

function toggleType(type) {
  const s = new Set(hiddenTypes.value)
  if (s.has(type)) s.delete(type)
  else s.add(type)
  hiddenTypes.value = s
}

function typeCount(type) {
  return periodBuildings.value.filter(b => b.type === type).length
}

const activePeriodInfo = computed(() => {
  return periods.find(p => p.name === activePeriod.value) || null
})

const topProvince = computed(() => {
  const src = periodBuildings.value
  const counts = {}
  src.forEach(b => { counts[b.province] = (counts[b.province] || 0) + 1 })
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
  if (!sorted.length) return null
  const province = sorted[0][0]
  const list = src.filter(b => b.province === province).slice(0, 5)
  return { province, count: sorted[0][1], list }
})

const sameProvinceBuildings = computed(() => {
  if (!selectedBuilding.value) return []
  const others = buildings.filter(b =>
    b.province === selectedBuilding.value.province && b.name !== selectedBuilding.value.name
  )
  const samePeriod = others.filter(b => b.period === selectedBuilding.value.period).slice(0, 3)
  const diffPeriod = others.filter(b => b.period !== selectedBuilding.value.period).slice(0, 3)
  return [...samePeriod, ...diffPeriod]
})

function parseDesc(desc) {
  if (!desc) return null
  const parts = {}
  const segments = desc.split('|')
  segments.forEach(seg => {
    const idx = seg.indexOf(':')
    if (idx > -1) {
      const key = seg.slice(0, idx).trim()
      const val = seg.slice(idx + 1).trim()
      if (key && val) parts[key] = val
    }
  })
  return Object.keys(parts).length > 1 ? parts : null
}

const descSections = computed(() => {
  if (!selectedBuilding.value) return null
  return parseDesc(selectedBuilding.value.description)
})

function initPie() {
  if (!pieChart.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(pieChart.value, null, { renderer: 'svg' })
  updatePie()
}

function updatePie() {
  if (!chartInstance) return
  const data = TYPES
    .filter(t => !hiddenTypes.value.has(t))
    .map(t => ({ name: t, value: typeCount(t), itemStyle: { color: typeColors[t] } }))
    .filter(d => d.value > 0)
  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c}\u5ea7 ({d}%)', ...TOOLTIP_STYLE },
    legend: { show: false },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '50%'], data,
      label: { color: '#c9a84c', fontSize: 12, fontFamily: 'Noto Serif SC' },
      labelLine: { lineStyle: { color: '#c9a84c44' } },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(201,168,76,0.3)' } }
    }]
  })
}

watch(periodBuildings, () => nextTick(updatePie))
watch(hiddenTypes, () => nextTick(updatePie))
watch(pieChart, el => { if (el) nextTick(initPie) })

async function initCCMap() {
  if (!ccMapRef.value || !topProvince.value) return
  if (ccMapInstance) ccMapInstance.dispose()
  ccMapInstance = echarts.init(ccMapRef.value, null, { renderer: 'svg' })
  const geoData = await fetch('/china-provinces.json').then(r => r.json())
  const provinceName = topProvince.value.province
  const feature = geoData.features.find(f =>
    f.properties.name.replace(/\u7701|\u5e02|\u81ea\u6cbb\u533a|\u58ee\u65cf|\u56de\u65cf|\u7ef4\u543e\u5c14/g, '').includes(provinceName.replace(/\u7701|\u5e02|\u81ea\u6cbb\u533a/g, ''))
  )
  if (!feature) return
  const mapName = 'province_' + provinceName
  echarts.registerMap(mapName, { type: 'FeatureCollection', features: [feature] })
  const scatterData = topProvince.value.list.map(b => ({ name: b.name, value: [b.lng, b.lat], type: b.type }))
  ccMapInstance.setOption({
    backgroundColor: 'transparent',
    geo: {
      map: mapName, roam: false,
      itemStyle: { areaColor: 'rgba(201,168,76,0.06)', borderColor: '#c9a84c88', borderWidth: 1.5 },
      emphasis: { itemStyle: { areaColor: 'rgba(201,168,76,0.12)' } }
    },
    series: [{
      type: 'effectScatter', coordinateSystem: 'geo', data: scatterData,
      symbolSize: 9, rippleEffect: { brushType: 'stroke', scale: 2.5 },
      itemStyle: { color: p => typeColors[p.data.type] || '#c9a84c' },
      label: { show: false }
    }]
  })
}

watch([ccMapRef, topProvince], () => nextTick(initCCMap))

function initOverviewCharts() {
  nextTick(() => {
    initBarChart()
    initBubbleChart()
    initStackChart()
    initRuinsPieCharts()
  })
}

function initBarChart() {
  if (!barRef.value) return
  if (overviewCharts.value.bar) overviewCharts.value.bar.dispose()
  const inst = echarts.init(barRef.value, null, { renderer: 'svg' })
  overviewCharts.value.bar = inst
  const data = PERIODS.map(p => buildings.filter(b => b.period === p).length)
  inst.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...TOOLTIP_STYLE },
    grid: { left: 36, right: 10, top: 16, bottom: 36 },
    xAxis: { type: 'category', data: PERIODS, axisLabel: { color: '#c9a84c', fontSize: 12, fontFamily: 'Noto Serif SC' }, axisLine: { lineStyle: { color: '#c9a84c44' } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: '#8b8680', fontSize: 11 }, splitLine: { lineStyle: { color: '#c9a84c22' } } },
    series: [{
      type: 'line', data, smooth: true, symbol: 'circle', symbolSize: 8,
      lineStyle: { color: '#c9a84c', width: 2 },
      itemStyle: { color: '#c9a84c', borderColor: '#e8c96d', borderWidth: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#c9a84c44' }, { offset: 1, color: '#c9a84c05' }] } },
      label: { show: true, position: 'top', color: '#c9a84c', fontSize: 11 }
    }]
  })
}

function initBubbleChart() {
  if (!bubbleRef.value) return
  if (overviewCharts.value.bubble) overviewCharts.value.bubble.dispose()
  const inst = echarts.init(bubbleRef.value, null, { renderer: 'svg' })
  overviewCharts.value.bubble = inst
  const counts = {}
  buildings.forEach(b => { counts[b.province] = (counts[b.province] || 0) + 1 })
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 15).reverse()
  const maxVal = Math.max(...sorted.map(s => s[1]))
  inst.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...TOOLTIP_STYLE },
    grid: { left: 56, right: 40, top: 8, bottom: 8 },
    xAxis: { type: 'value', axisLabel: { color: '#8b8680', fontSize: 11 }, splitLine: { lineStyle: { color: '#c9a84c22' } } },
    yAxis: { type: 'category', data: sorted.map(s => s[0]), axisLabel: { color: '#c9a84c', fontSize: 12, fontFamily: 'Noto Serif SC' }, axisLine: { lineStyle: { color: '#c9a84c44' } }, axisTick: { show: false } },
    series: [{
      type: 'bar',
      data: sorted.map(s => ({
        value: s[1],
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#c9a84c11' }, { offset: s[1] / maxVal, color: '#c9a84c99' }, { offset: 1, color: '#e8c96d' }] } }
      })),
      barMaxWidth: 14,
      label: { show: true, position: 'right', color: '#c9a84c', fontSize: 11 }
    }]
  })
}

function initStackChart() {
  if (!stackRef.value) return
  if (overviewCharts.value.stack) overviewCharts.value.stack.dispose()
  const inst = echarts.init(stackRef.value, null, { renderer: 'svg' })
  overviewCharts.value.stack = inst
  const series = TYPES.map(t => ({
    name: t, type: 'bar', stack: 'total',
    data: PERIODS.map(p => buildings.filter(b => b.period === p && b.type === t).length),
    itemStyle: { color: typeColors[t] }
  }))
  inst.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...TOOLTIP_STYLE },
    legend: { data: TYPES, textStyle: { color: '#c9a84c', fontSize: 11 }, top: 0, itemWidth: 12, itemHeight: 8 },
    grid: { left: 36, right: 10, top: 28, bottom: 36 },
    xAxis: { type: 'category', data: PERIODS, axisLabel: { color: '#c9a84c', fontSize: 12, fontFamily: 'Noto Serif SC' }, axisLine: { lineStyle: { color: '#c9a84c44' } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: '#8b8680', fontSize: 11 }, splitLine: { lineStyle: { color: '#c9a84c22' } } },
    series
  })
}

function initRuinsPieCharts() {
  const keywords = ['\u9057\u5740', '\u65e7\u5740', '\u6545\u57ce', '\u9057\u8ff9']
  PERIODS.forEach(p => {
    const el = ruinsPieRefs[p]
    if (!el) return
    if (ruinsPieInstances[p]) ruinsPieInstances[p].dispose()
    const inst = echarts.init(el, null, { renderer: 'svg' })
    ruinsPieInstances[p] = inst
    const all = buildings.filter(b => b.period === p)
    const ruins = all.filter(b => keywords.some(k => b.name.includes(k))).length
    const existing = all.length - ruins
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c}\u5ea7 ({d}%)', ...TOOLTIP_STYLE },
      series: [{
        type: 'pie', radius: ['40%', '68%'], center: ['50%', '50%'],
        data: [
          { name: '\u73b0\u5b58', value: existing, itemStyle: { color: '#c9a84c' } },
          { name: '\u9057\u5740/\u5df2\u6bc1', value: ruins, itemStyle: { color: '#00d4ff88' } }
        ],
        label: { color: '#c9a84c', fontSize: 12, fontFamily: 'Noto Serif SC' },
        labelLine: { lineStyle: { color: '#c9a84c44' } }
      }]
    })
  })
}

watch(showOverview, val => { if (val) initOverviewCharts() })
watch(activePeriod, val => { if (val === 'all' && showOverview.value) nextTick(initOverviewCharts) })

function onSelectBuilding(building) {
  selectedBuilding.value = building
}

function goToDetail(id) {
  router.push('/building/' + id)
}
</script>
"""

with open(r'D:/jishe/ancient-architecture-viz/src/views/ExploreView_new.vue', 'w', encoding='utf-8') as f:
    f.write(script_part)

print('script written, lines:', script_part.count('\n'))
