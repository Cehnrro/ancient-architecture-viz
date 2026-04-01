<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
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
const showMapStoryboard = ref(true)
const showProvinceDetail = ref(false)
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
let ccMapClickHandler = null
let resizeHandler = null

const BASE = import.meta.env.BASE_URL
const assetUrl = (path) => path ? BASE + path.replace(/^\//, '') : ''

// 预加载代表性建筑图片
buildingsData.filter(b => b.isFeatured && b.imageUrl).forEach(b => {
  const img = new Image()
  img.src = assetUrl(b.imageUrl)
})

const PERIODS = ['先秦两汉', '魏晋隋唐', '宋辽金元', '明清']
const TYPES = ['皇宫', '官府', '民居', '桥梁']
const typeColors = { '皇宫': '#e8c96d', '官府': '#00d4ff', '民居': '#81c784', '桥梁': '#ff8a65' }
const overviewTypeColors = { '皇宫': '#d8bb69', '官府': '#2bafc9', '民居': '#77ae79', '桥梁': '#d98b63' }
const periodNodeColors = ['#9a6d2f', '#bb8840', '#d2a256', '#efc96f']
const provinceAccentColors = ['#efc96f', '#ddb160', '#ca964f', '#b57d41', '#8ca7af']
const TOOLTIP_STYLE = {
  backgroundColor: 'rgba(19, 24, 33, 0.96)',
  borderColor: '#c9a84c55',
  borderWidth: 1,
  padding: [10, 14],
  textStyle: { color: '#e6d5b8', fontSize: 12, fontFamily: 'Noto Serif SC' },
  extraCssText: 'box-shadow:0 10px 24px rgba(0,0,0,0.32);'
}

function goldGradient(x2 = 1) {
  return new echarts.graphic.LinearGradient(0, 0, x2, 0, [
    { offset: 0, color: '#7a5a33' },
    { offset: 0.55, color: '#b88743' },
    { offset: 1, color: '#efc96f' }
  ])
}

function deepInkGradient() {
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: 'rgba(201,168,76,0.16)' },
    { offset: 0.45, color: 'rgba(120,88,39,0.12)' },
    { offset: 1, color: 'rgba(12,16,28,0.02)' }
  ])
}

function provinceBarGradient(index) {
  const accent = provinceAccentColors[Math.min(index, provinceAccentColors.length - 1)]
  return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: 'rgba(95, 67, 37, 0.42)' },
    { offset: 0.58, color: accent + 'bb' },
    { offset: 1, color: accent }
  ])
}

function normalizeProvinceName(name = '') {
  return name.replace(/省|市|自治区|壮族|回族|维吾尔/g, '')
}

function distributeLabelPositions(items, minY, maxY) {
  if (!items.length) return []
  const sorted = [...items].sort((a, b) => a.y - b.y)
  const gap = sorted.length === 1 ? 0 : Math.max(20, Math.min(34, (maxY - minY) / (sorted.length - 1)))
  let currentY = minY
  const placed = sorted.map(item => {
    const targetY = Math.max(currentY, Math.min(maxY, item.y))
    currentY = targetY + gap
    return { ...item, targetY }
  })

  for (let i = placed.length - 2; i >= 0; i--) {
    if (placed[i].targetY > placed[i + 1].targetY - gap) {
      placed[i].targetY = placed[i + 1].targetY - gap
    }
  }

  const shift = Math.min(0, minY - placed[0].targetY)
  if (shift) {
    placed.forEach(item => { item.targetY += shift })
  }
  return placed
}

function renderProvinceMapLabels(inst, scatterData) {
  const width = inst.getWidth()
  const height = inst.getHeight()
  const projected = scatterData
    .map(item => {
      const pixel = inst.convertToPixel({ geoIndex: 0 }, item.value)
      if (!Array.isArray(pixel) || pixel.some(v => !Number.isFinite(v))) return null
      return { ...item, x: pixel[0], y: pixel[1] }
    })
    .filter(Boolean)

  if (!projected.length) {
    inst.setOption({ graphic: [] })
    return
  }

  const sortedByX = [...projected].sort((a, b) => a.x - b.x)
  const splitIndex = Math.ceil(sortedByX.length / 2)
  const leftItems = distributeLabelPositions(sortedByX.slice(0, splitIndex), 18, height - 18)
  const rightItems = distributeLabelPositions(sortedByX.slice(splitIndex), 18, height - 18)
  const labelXLeft = 22
  const labelXRight = width - 22
  const elbowLeft = Math.max(42, width * 0.23)
  const elbowRight = Math.min(width - 42, width * 0.77)

  const graphics = []
  const appendSide = (items, side) => {
    items.forEach(item => {
      const labelWidth = Math.max(84, Math.min(128, item.name.length * 15 + 26))
      const labelHeight = 22
      const labelX = side === 'left' ? labelXLeft : labelXRight
      const elbowX = side === 'left' ? elbowLeft : elbowRight
      const textAlign = side === 'left' ? 'left' : 'right'
      const labelGroupX = side === 'left' ? labelX : labelX - labelWidth
      const labelAttachX = side === 'left' ? labelGroupX + labelWidth - 10 : labelGroupX + 10
      const lineStart = [item.x, item.y]
      const lineElbow = [elbowX, item.targetY]
      const lineEnd = [labelAttachX, item.targetY]
      const accentX = side === 'left' ? labelWidth - 3 : 0

      graphics.push(
        {
          type: 'polyline',
          silent: true,
          shape: { points: [lineStart, lineElbow] },
          style: {
            stroke: typeColors[item.type] || '#c9a84c',
            lineWidth: 1.1,
            opacity: 0.34
          }
        },
        {
          type: 'polyline',
          silent: true,
          shape: { points: [lineElbow, lineEnd] },
          style: {
            stroke: 'rgba(201, 168, 76, 0.42)',
            lineWidth: 1.05,
            opacity: 0.78
          }
        },
        {
          type: 'circle',
          silent: true,
          shape: { cx: item.x, cy: item.y, r: 3.8 },
          style: {
            fill: typeColors[item.type] || '#c9a84c',
            stroke: '#f4dcaa',
            lineWidth: 1.1,
            shadowBlur: 8,
            shadowColor: 'rgba(201, 168, 76, 0.24)'
          }
        },
        {
          type: 'circle',
          silent: true,
          shape: { cx: item.x, cy: item.y, r: 8.2 },
          style: {
            fill: 'rgba(201, 168, 76, 0.06)',
            stroke: typeColors[item.type] || '#c9a84c',
            lineWidth: 1,
            opacity: 0.78
          }
        },
        {
          type: 'group',
          x: labelGroupX,
          y: item.targetY - labelHeight / 2,
          cursor: 'pointer',
          onclick: () => openProvinceBuilding(item.raw),
          children: [
            {
              type: 'rect',
              shape: { x: 0, y: 0, width: labelWidth, height: labelHeight, r: 2 },
              style: {
                fill: 'rgba(12, 16, 28, 0.82)',
                stroke: 'rgba(139, 107, 58, 0.38)',
                lineWidth: 1,
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.18)'
              }
            },
            {
              type: 'rect',
              silent: true,
              shape: { x: accentX, y: 4, width: 2, height: labelHeight - 8, r: 1 },
              style: {
                fill: typeColors[item.type] || '#c9a84c',
                opacity: 0.92
              }
            },
            {
              type: 'text',
              style: {
                x: side === 'left' ? 10 : labelWidth - 10,
                y: labelHeight / 2,
                text: item.name,
                fill: '#dcc694',
                font: '13px "Noto Serif SC"',
                textAlign,
                textVerticalAlign: 'middle',
                overflow: 'truncate',
                width: labelWidth - 20
              }
            }
          ]
        }
      )
    })
  }

  appendSide(leftItems, 'left')
  appendSide(rightItems, 'right')
  inst.setOption({ graphic: graphics })
}

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

const mapNarrativeText = computed(() => {
  const allNarratives = {
    all: '从四个关键时期观察古建筑的礼制秩序、地域分布与营造类型如何逐步演进。',
    '先秦两汉': '礼制宫苑与早期官署奠定空间秩序，南北民居与桥梁技术开始显现地域差异。',
    '魏晋隋唐': '都城规划、官署营建与大型桥梁同步成熟，帝国尺度与工程能力显著提升。',
    '宋辽金元': '城市治理、桥梁体系与民居营造持续精进，地方性风格开始清晰分化。',
    '明清': '礼制空间高度定型，官府与民居体系趋于成熟，建筑工艺转向精细化与集成化。'
  }
  return allNarratives[activePeriod.value] || allNarratives.all
})

const mapStoryPanel = computed(() => {
  const mainLabel = activePeriodInfo.value?.label || '总览'
  const mainRange = activePeriodInfo.value?.range || '四个关键时期总览'
  return {
    eyebrow: activePeriod.value === 'all' ? '建筑地图总览' : `${mainLabel} · 建筑地图`,
    title: activePeriod.value === 'all' ? '中国古建筑时空格局' : activePeriod.value,
    range: mainRange,
    text: mapNarrativeText.value
  }
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
  // 支持中文分号分隔的 "标题：内容；" 格式
  const parts = {}
  const segments = desc.split('；').filter(s => s.trim())
  segments.forEach(seg => {
    const idx = seg.indexOf('：')
    if (idx > -1) {
      const key = seg.slice(0, idx).trim()
      const val = seg.slice(idx + 1).trim()
      if (key && val) parts[key] = val
    }
  })
  if (Object.keys(parts).length > 1) return parts
  // 兼容英文冒号竖线格式
  const parts2 = {}
  const segs2 = desc.split('|')
  segs2.forEach(seg => {
    const idx = seg.indexOf(':')
    if (idx > -1) {
      const key = seg.slice(0, idx).trim()
      const val = seg.slice(idx + 1).trim()
      if (key && val) parts2[key] = val
    }
  })
  return Object.keys(parts2).length > 1 ? parts2 : null
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
    tooltip: { trigger: 'item', formatter: '{b}: {c}座 ({d}%)', ...TOOLTIP_STYLE },
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
watch(hiddenTypes, () => {
  nextTick(updatePie)
  if (showOverview.value && activePeriod.value === 'all') nextTick(initStackChart)
})
watch(pieChart, el => { if (el) nextTick(initPie) })

async function initCCMap() {
  if (!ccMapRef.value || !topProvince.value) return
  if (ccMapInstance) ccMapInstance.dispose()
  ccMapInstance = echarts.init(ccMapRef.value, null, { renderer: 'svg' })
  const geoData = await fetch(import.meta.env.BASE_URL + 'china-provinces.json').then(r => r.json())
  const provinceName = topProvince.value.province
  const feature = geoData.features.find(f =>
    normalizeProvinceName(f.properties.name).includes(normalizeProvinceName(provinceName))
  )
  if (!feature) return
  const mapName = 'province_' + provinceName
  echarts.registerMap(mapName, { type: 'FeatureCollection', features: [feature] })
  const scatterData = topProvince.value.list.map(b => ({
    name: b.name,
    value: [b.lng, b.lat],
    type: b.type,
    raw: b
  }))
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
      label: { show: false },
      tooltip: {
        formatter: params => `${params.data.name}<br/>类型：${params.data.type}`,
        ...TOOLTIP_STYLE
      }
    }]
  })

  renderProvinceMapLabels(ccMapInstance, scatterData)

  if (ccMapClickHandler) ccMapInstance.off('click', ccMapClickHandler)
  ccMapClickHandler = params => {
    if (params.componentSubType === 'effectScatter' && params.data?.raw) {
      openProvinceBuilding(params.data.raw)
    }
  }
  ccMapInstance.on('click', ccMapClickHandler)
}

watch([ccMapRef, topProvince], () => nextTick(initCCMap))
watch(showProvinceDetail, val => { if (val) nextTick(initCCMap) })

resizeHandler = () => {
  if (chartInstance) chartInstance.resize()
  if (ccMapInstance && showProvinceDetail.value) {
    ccMapInstance.resize()
    if (topProvince.value) {
      const scatterData = topProvince.value.list.map(b => ({
        name: b.name,
        value: [b.lng, b.lat],
        type: b.type,
        raw: b
      }))
      renderProvinceMapLabels(ccMapInstance, scatterData)
    }
  }
  Object.values(overviewCharts.value).forEach(chart => chart?.resize?.())
  Object.values(ruinsPieInstances).forEach(chart => chart?.resize?.())
}

window.addEventListener('resize', resizeHandler)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  if (ccMapInstance && ccMapClickHandler) ccMapInstance.off('click', ccMapClickHandler)
})

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
  const maxVal = Math.max(...data)
  inst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#c9a84c55', width: 1, type: 'dashed' } },
      formatter: params => {
        const item = params[0]
        return `${item.axisValue}<br/>建筑数量：${item.value} 座`
      },
      ...TOOLTIP_STYLE
    },
    grid: { left: 34, right: 18, top: 26, bottom: 30 },
    xAxis: {
      type: 'category',
      data: PERIODS,
      axisLabel: { color: '#d3ba82', fontSize: 12, fontFamily: 'Noto Serif SC', margin: 12 },
      axisLine: { lineStyle: { color: '#8b6b3a88' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8f897f', fontSize: 11, fontFamily: 'Noto Serif SC' },
      splitNumber: 4,
      splitLine: { lineStyle: { color: '#c9a84c1f', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      data,
      smooth: 0.38,
      symbol: 'circle',
      symbolSize: value => Math.max(8, Math.round((value / maxVal) * 14)),
      lineStyle: { color: goldGradient(), width: 3 },
      itemStyle: {
        color: params => periodNodeColors[params.dataIndex] || '#c9a84c',
        borderColor: '#f1d791',
        borderWidth: 2,
        shadowBlur: 12,
        shadowColor: 'rgba(201,168,76,0.24)'
      },
      areaStyle: { color: deepInkGradient() },
      label: {
        show: true,
        position: 'top',
        offset: [0, -2],
        color: '#e4c978',
        fontSize: 11,
        fontFamily: 'Noto Serif SC',
        formatter: params => (params.value === maxVal ? `${params.value}` : `${params.value}`)
      },
      emphasis: { focus: 'series' }
    }, {
      type: 'effectScatter',
      coordinateSystem: 'cartesian2d',
      z: 4,
      data: data.map((value, index) => [index, value]),
      symbolSize: params => Math.max(10, Math.round((params[1] / maxVal) * 16)),
      rippleEffect: { scale: 2.4, brushType: 'stroke' },
      itemStyle: {
        color: params => periodNodeColors[params.dataIndex] || '#efc96f',
        shadowBlur: 12,
        shadowColor: 'rgba(201,168,76,0.24)'
      },
      tooltip: { show: false }
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
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 15)
  const maxVal = Math.max(...sorted.map(s => s[1]))
  inst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(201,168,76,0.06)' } },
      formatter: params => {
        const row = params.find(item => item.seriesName === 'actual') || params[0]
        return `${row.axisValue}<br/>建筑数量：${row.value} 座`
      },
      ...TOOLTIP_STYLE
    },
    grid: { left: 74, right: 42, top: 14, bottom: 10 },
    xAxis: {
      type: 'value',
      axisLabel: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#c9a84c14' } }
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: sorted.map(s => s[0]),
      axisLabel: { color: '#d1bd93', fontSize: 12, fontFamily: 'Noto Serif SC', margin: 14 },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [{
      name: 'shadow',
      type: 'bar',
      silent: true,
      data: sorted.map(() => maxVal),
      barGap: '-100%',
      barMaxWidth: 14,
      itemStyle: {
        color: 'rgba(201,168,76,0.08)',
        borderRadius: [0, 8, 8, 0]
      },
      z: 1
    }, {
      name: 'actual',
      type: 'bar',
      data: sorted.map((s, index) => ({
        value: s[1],
        itemStyle: {
          color: provinceBarGradient(index),
          borderRadius: [0, 8, 8, 0],
          shadowBlur: index < 3 ? 12 : 4,
          shadowColor: index < 3 ? 'rgba(201,168,76,0.22)' : 'rgba(0,0,0,0.18)'
        }
      })),
      barMaxWidth: 14,
      label: {
        show: true,
        position: 'right',
        distance: 10,
        color: '#e7d2a1',
        fontSize: 11,
        fontFamily: 'Noto Serif SC',
        formatter: params => `${params.value} 座`
      },
      z: 3
    }, {
      type: 'scatter',
      data: sorted.map(([name, value]) => [value, name]),
      symbolSize: params => Math.max(10, Math.round((params[0] / maxVal) * 18)),
      itemStyle: {
        color: '#87a7b0',
        borderColor: '#d4c082',
        borderWidth: 1.2,
        shadowBlur: 10,
        shadowColor: 'rgba(135,167,176,0.24)'
      },
      tooltip: { show: false },
      z: 4
    }]
  })
}

function initStackChart() {
  if (!stackRef.value) return
  if (overviewCharts.value.stack) overviewCharts.value.stack.dispose()
  const inst = echarts.init(stackRef.value, null, { renderer: 'svg' })
  overviewCharts.value.stack = inst
  const visibleTypes = TYPES.filter(t => !hiddenTypes.value.has(t))
  let currentLegendSelected = Object.fromEntries(visibleTypes.map(type => [type, true]))

  function computePeriodTotals(selectedMap = currentLegendSelected) {
    const activeTypes = visibleTypes.filter(type => selectedMap[type] !== false)
    return PERIODS.map(p =>
      buildings.filter(b => b.period === p && activeTypes.includes(b.type)).length
    )
  }

  const series = visibleTypes.map(t => ({
      id: `stack-${t}`,
      name: t, type: 'bar', stack: 'total', barWidth: 28,
      data: PERIODS.map(p => buildings.filter(b => b.period === p && b.type === t).length),
      itemStyle: {
        color: overviewTypeColors[t],
        borderRadius: t === '皇宫' ? [4, 4, 0, 0] : [0, 0, 0, 0],
        borderColor: 'rgba(10,14,26,0.36)',
        borderWidth: 0.6
      },
      emphasis: { focus: 'series' }
    }))

  inst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(201,168,76,0.05)' } },
      formatter: params => {
        const lines = [`${params[0]?.axisValue || ''}`]
        params.forEach(item => {
          if (item.componentSubType === 'bar' && item.value) {
            lines.push(`${item.marker}${item.seriesName}：${item.value} 座`)
          }
        })
        const totals = computePeriodTotals()
        const total = totals[params[0]?.dataIndex ?? 0] || 0
        lines.push(`总计：${total} 座`)
        return lines.join('<br/>')
      },
      ...TOOLTIP_STYLE
    },
    legend: {
      data: visibleTypes,
      selected: currentLegendSelected,
      selectedMode: 'multiple',
      textStyle: { color: '#cbb47f', fontSize: 11, fontFamily: 'Noto Serif SC' },
      top: 0,
      itemWidth: 10,
      itemHeight: 10,
      icon: 'roundRect'
    },
    grid: { left: 36, right: 14, top: 34, bottom: 34 },
    xAxis: {
      type: 'category',
      data: PERIODS,
      axisLabel: { color: '#d0bc8d', fontSize: 12, fontFamily: 'Noto Serif SC', margin: 12 },
      axisLine: { lineStyle: { color: '#8b6b3a66' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8b8680', fontSize: 11, fontFamily: 'Noto Serif SC' },
      splitNumber: 4,
      splitLine: { lineStyle: { color: '#c9a84c18', type: 'dashed' } }
    },
    series: [
      ...series,
      {
        id: 'stack-totals',
        name: '__totals__',
        type: 'line',
        data: computePeriodTotals(),
        smooth: 0.24,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#d8c28d77', width: 1.4, type: 'dashed' },
        itemStyle: { color: '#d8c28d' },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          color: '#dfcca0',
          fontSize: 10,
          fontFamily: 'Noto Serif SC',
          formatter: p => `${p.value}`
        },
        tooltip: { show: false },
        z: 4
      }
    ]
  }, true)

  inst.on('legendselectchanged', params => {
    currentLegendSelected = Object.fromEntries(
      visibleTypes.map(type => [type, params.selected?.[type] !== false])
    )
    inst.setOption({
      series: [{
        id: 'stack-totals',
        data: computePeriodTotals(currentLegendSelected)
      }]
    })
  })
}

function initRuinsPieCharts() {
  const keywords = ['遗址', '旧址', '故城', '遗迹']
  PERIODS.forEach(p => {
    const el = ruinsPieRefs[p]
    if (!el) return
    if (ruinsPieInstances[p]) ruinsPieInstances[p].dispose()
    const inst = echarts.init(el, null, { renderer: 'svg' })
    ruinsPieInstances[p] = inst
    const all = buildings.filter(b => b.period === p)
    const ruins = all.filter(b => keywords.some(k => b.name.includes(k))).length
    const existing = all.length - ruins
    const existingRate = all.length ? Math.round((existing / all.length) * 100) : 0
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}座 ({d}%)',
        ...TOOLTIP_STYLE
      },
      title: {
        text: `${existingRate}%`,
        subtext: '现存比例',
        left: 'center',
        top: '40%',
        textStyle: { color: '#ddc48c', fontSize: 16, fontFamily: 'Noto Serif SC', fontWeight: 600 },
        subtextStyle: { color: '#8f897f', fontSize: 10, fontFamily: 'Noto Serif SC' }
      },
      series: [{
        type: 'pie', radius: ['50%', '72%'], center: ['50%', '55%'],
        data: [
          { name: '现存', value: existing, itemStyle: { color: '#b8954e', borderColor: 'rgba(10,14,26,0.92)', borderWidth: 1 } },
          { name: '遗址/已毁', value: ruins, itemStyle: { color: '#5f6d73', borderColor: 'rgba(10,14,26,0.92)', borderWidth: 1 } }
        ],
        label: {
          show: false
        },
        labelLine: { show: false },
        emphasis: {
          scale: true,
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(201,168,76,0.18)' }
        }
      }]
    })
  })
}

watch(showOverview, val => { if (val) initOverviewCharts() })
watch(activePeriod, val => { if (val === 'all' && showOverview.value) nextTick(initOverviewCharts) })

function onSelectBuilding(building) {
  selectedBuilding.value = building
}

function openProvinceBuilding(building) {
  showProvinceDetail.value = false
  onSelectBuilding(building)
}

function goToDetail(id) {
  router.push('/building/' + id)
}
</script>

<template>
  <div class="explore-page">
    <nav class="top-nav">
      <span class="nav-title text-glow-gold">匠心千年</span>
      <div class="nav-links">
        <router-link to="/explore">建筑地图</router-link>
        <router-link to="/works">文化著作</router-link>
        <router-link to="/lineage">科学家谱系</router-link>
      </div>
    </nav>

    <div class="main-body">
      <div class="map-area">
        <MapView
          :buildings="filteredBuildings"
          :selected-period="activePeriod"
          @select-building="onSelectBuilding"
        />
        <button
          v-if="!selectedBuilding && !showMapStoryboard"
          class="map-story-show-btn"
          @click="showMapStoryboard = true"
        >显示导览</button>
        <div v-if="!selectedBuilding && showMapStoryboard" class="map-storyboard">
          <div class="map-story-header">
            <div class="map-story-eyebrow">{{ mapStoryPanel.eyebrow }}</div>
            <button class="map-story-close" @click="showMapStoryboard = false">隐藏</button>
          </div>
          <div class="map-story-title">{{ mapStoryPanel.title }}</div>
          <div class="map-story-range">{{ mapStoryPanel.range }}</div>
          <div class="map-story-copy">{{ mapStoryPanel.text }}</div>
          <div v-if="topProvince" class="story-province-card">
            <div class="story-province-top">
              <div>
                <div class="story-province-label">建筑最密集省份</div>
                <div class="story-province-name">{{ topProvince.province }}</div>
              </div>
              <div class="story-province-count">{{ topProvince.count }} 处</div>
            </div>
            <div class="story-province-actions">
              <button class="story-province-btn" @click="showProvinceDetail = !showProvinceDetail">
                {{ showProvinceDetail ? '收起省份详情' : '展开省份详情' }}
              </button>
              <span class="story-province-hint">点击条目可查看建筑</span>
            </div>
            <div v-if="showProvinceDetail" class="story-province-detail">
              <div ref="ccMapRef" class="story-province-map" />
              <div class="story-province-list">
                <button
                  v-for="b in topProvince.list"
                  :key="b.name"
                  class="story-province-item"
                  @click="openProvinceBuilding(b)"
                >
                  <span :class="`tag tag-${b.type}`" style="font-size:9px;padding:1px 4px;">{{ b.type }}</span>
                  <span class="story-province-item-name">{{ b.name }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="sidebar">
        <transition name="sidebar-fade" mode="out-in">
        <div v-if="!selectedBuilding" key="list" class="sidebar-inner">
          <div class="sidebar-period">
            <div class="period-name-label">
              {{ activePeriodInfo ? activePeriodInfo.name : '中华上下五千年' }}
            </div>
            <div class="period-sub" v-if="activePeriodInfo">
              {{ activePeriodInfo.label }} · {{ activePeriodInfo.range }}
            </div>
            <div class="building-count">共 {{ filteredBuildings.length }} 处古建筑</div>
          </div>

          <button
            v-if="activePeriod === 'all'"
            class="overview-btn"
            :class="{ active: showOverview }"
            @click="showOverview = !showOverview"
          >{{ showOverview ? '收起总览' : '数据总览' }}</button>

          <template v-if="showOverview && activePeriod === 'all'">
            <div class="overview-section">
              <div class="overview-title">各朝代建筑数量</div>
              <div ref="barRef" class="overview-chart" />
            </div>
            <div class="overview-section">
              <div class="overview-title">建筑最密集省份（前15）</div>
              <div ref="bubbleRef" class="overview-chart overview-chart-tall" />
            </div>
            <div class="overview-section">
              <div class="overview-title">各朝代建筑类型分布</div>
              <div ref="stackRef" class="overview-chart-stack" />
            </div>
            <div class="overview-section">
              <div class="overview-title">各朝代建筑保存状况</div>
              <div class="ruins-pies">
                <div v-for="p in PERIODS" :key="p">
                  <div class="ruins-period-title">{{ p }}</div>
                  <div :ref="el => { if(el) ruinsPieRefs[p] = el }" class="ruins-pie-item" />
                </div>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="type-stats">
              <div
                v-for="type in TYPES"
                :key="type"
                class="type-stat-item"
                :class="{ 'type-hidden': hiddenTypes.has(type) }"
                @click="toggleType(type)"
              >
                <span :class="`tag tag-${type}`">{{ type }}</span>
                <span class="type-count">{{ typeCount(type) }}</span>
                <span class="type-toggle-hint">{{ hiddenTypes.has(type) ? '显示' : '隐藏' }}</span>
              </div>
            </div>
            <div class="pie-wrap">
              <div class="pie-title">建筑分布与类型结构</div>
              <div ref="pieChart" class="pie-chart" />
            </div>
            <div class="divider-gold my-4" />
            <div class="hint">点击地图上的建筑查看详情</div>
          </template>
        </div>

        <div v-else key="detail" class="sidebar-inner">
          <button class="back-to-map" @click="selectedBuilding = null">← 返回地图</button>
          <div class="building-card">
            <div class="bc-type-row">
              <span :class="`tag tag-${selectedBuilding.type}`">{{ selectedBuilding.type }}</span>
              <span class="bc-dynasty">{{ selectedBuilding.dynasty }}</span>
              <span class="bc-province">{{ selectedBuilding.province }}</span>
            </div>
            <div class="bc-name text-glow-gold">{{ selectedBuilding.name }}</div>
            <template v-if="selectedBuilding.isFeatured">
              <div class="bc-image-wrap">
                <img :src="assetUrl(selectedBuilding.imageUrl)" :alt="selectedBuilding.name" class="bc-image"
                  @error="e => e.target.style.display='none'" />
              </div>
              <p class="bc-tagline" v-if="selectedBuilding.tagline">{{ selectedBuilding.tagline }}</p>
            </template>
            <div class="divider-gold my-3" />
            <template v-if="descSections">
              <div class="desc-sections">
                <div v-for="(val, key) in descSections" :key="key" class="desc-section">
                  <div class="desc-section-label"><span class="desc-label-icon">◆</span>{{ key }}</div>
                  <div class="desc-section-body">{{ val }}</div>
                </div>
              </div>
            </template>
            <template v-else>
              <p class="bc-desc">{{ selectedBuilding.description }}</p>
            </template>
            <div class="bc-features" v-if="selectedBuilding.isFeatured && selectedBuilding.features?.length">
              <div class="bc-features-title">建筑特色</div>
              <div v-for="f in selectedBuilding.features" :key="f" class="bc-feature-item">{{ f }}</div>
            </div>
            <button v-if="selectedBuilding.isFeatured" class="detail-btn" @click="goToDetail(selectedBuilding.id)">查看详情 →</button>
            <div class="same-province" v-if="sameProvinceBuildings.length">
              <div class="sp-title">同省其他建筑</div>
              <div v-for="b in sameProvinceBuildings" :key="b.name" class="sp-item" @click="onSelectBuilding(b)">
                <span :class="`tag tag-${b.type}`" style="font-size:9px;padding:1px 4px;">{{ b.type }}</span>
                <span class="sp-name">{{ b.name }}</span>
                <span class="sp-dynasty">{{ b.dynasty }}</span>
              </div>
            </div>
          </div>
        </div>
        </transition>
      </div>
    </div>

    <div class="period-timeline">
      <button
        v-for="p in [...periods, { id: 'all', name: '总览' }]"
        :key="p.id || p.name"
        class="period-btn"
        :class="{ active: activePeriod === (p.id === 'all' ? 'all' : p.name) }"
        @click="activePeriod = p.id === 'all' ? 'all' : p.name; selectedBuilding = null; if(p.id !== 'all') showOverview = false"
      >{{ p.name }}</button>
    </div>
  </div>
</template>

<style scoped>
/* 侧边栏切换过渡 */
.sidebar-fade-enter-active,
.sidebar-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.sidebar-fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.sidebar-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
.sidebar-inner {
  width: 100%;
}

.explore-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0a0e1a;
  color: #e6d5b8;
  font-family: 'Noto Serif SC', serif;
  overflow: hidden;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 56px 0 48px;
  height: 64px;
  background: linear-gradient(180deg, rgba(11, 15, 25, 0.985) 0%, rgba(10, 14, 26, 0.96) 100%);
  border-bottom: 1px solid #8a693655;
  flex-shrink: 0;
  z-index: 100;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
}

.nav-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 6px;
  color: #e8c96d;
  text-shadow: 0 0 20px #c9a84caa, 0 0 40px #c9a84c44;
  position: relative;
}
.nav-title::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, #c9a84c, transparent);
}

.nav-links {
  display: flex;
  gap: 34px;
  margin-right: 32px;
}

.nav-links a {
  color: #a09888;
  text-decoration: none;
  font-size: 15px;
  letter-spacing: 3px;
  transition: all 0.3s;
  position: relative;
  padding: 2px 0 4px;
}
.nav-links a::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  width: 0; height: 1px;
  background: #c9a84c;
  transition: width 0.3s;
}
.nav-links a:hover::after,
.nav-links a.router-link-active::after { width: 100%; }

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #c9a84c;
  text-shadow: 0 0 8px #c9a84c66;
}

.main-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.map-area {
  flex: 2.12;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 16%, rgba(201, 168, 76, 0.08), transparent 26%),
    radial-gradient(circle at 86% 24%, rgba(0, 212, 255, 0.045), transparent 24%),
    linear-gradient(180deg, rgba(8, 12, 20, 0.86), rgba(8, 12, 20, 0.2));
}
.map-area::before,
.map-area::after {
  content: '';
  position: absolute;
  pointer-events: none;
  z-index: 300;
}
.map-area::before {
  inset: 16px;
  border: 1px solid rgba(139, 107, 58, 0.18);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.01);
}
.map-area::after {
  inset: 0;
  background: linear-gradient(180deg, rgba(6, 10, 18, 0.08), transparent 18%, transparent 80%, rgba(6, 10, 18, 0.18));
}

.map-storyboard {
  position: absolute;
  top: 18px;
  left: 18px;
  z-index: 420;
  width: min(420px, calc(100% - 36px));
  padding: 20px 22px 18px;
  border: 1px solid rgba(139, 107, 58, 0.52);
  background:
    linear-gradient(180deg, rgba(15, 20, 31, 0.94), rgba(11, 15, 25, 0.86)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.08), transparent 36%);
  box-shadow: 0 14px 30px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.02);
  backdrop-filter: blur(10px);
  max-height: calc(100% - 36px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 16px;
}

.map-storyboard::-webkit-scrollbar { width: 4px; }
.map-storyboard::-webkit-scrollbar-track { background: transparent; }
.map-storyboard::-webkit-scrollbar-thumb { background: rgba(201, 168, 76, 0.36); border-radius: 2px; }

.map-story-show-btn {
  position: absolute;
  top: 18px;
  left: 18px;
  z-index: 420;
  padding: 8px 14px;
  border: 1px solid rgba(139, 107, 58, 0.5);
  background: linear-gradient(180deg, rgba(15, 20, 31, 0.92), rgba(11, 15, 25, 0.84));
  color: #d8c28d;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  letter-spacing: 2px;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(0,0,0,0.24);
}

.map-story-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.map-story-eyebrow {
  font-size: 11px;
  letter-spacing: 3px;
  color: #a69a84;
  margin-bottom: 8px;
}

.map-story-close {
  padding: 5px 10px;
  border: 1px solid rgba(139, 107, 58, 0.42);
  background: rgba(255,255,255,0.015);
  color: #bcae90;
  font-family: 'Noto Serif SC', serif;
  font-size: 12px;
  cursor: pointer;
  letter-spacing: 1px;
}

.map-story-title {
  font-size: 30px;
  line-height: 1.18;
  letter-spacing: 4px;
  color: #ecd08a;
  text-shadow: 0 0 18px rgba(201, 168, 76, 0.18);
}

.map-story-range {
  margin-top: 8px;
  font-size: 13px;
  color: #c2b291;
  letter-spacing: 1px;
}

.map-story-copy {
  margin-top: 14px;
  padding-left: 14px;
  border-left: 2px solid rgba(201, 168, 76, 0.26);
  font-size: 14px;
  line-height: 1.9;
  color: #d4c6aa;
  max-width: 34em;
}

.story-province-card {
  margin-top: 16px;
  padding: 16px 16px 14px;
  border: 1px solid rgba(139, 107, 58, 0.42);
  background:
    linear-gradient(180deg, rgba(20, 26, 38, 0.9), rgba(12, 16, 28, 0.84)),
    radial-gradient(circle at top right, rgba(201,168,76,0.085), transparent 36%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 10px 22px rgba(0,0,0,0.12);
}

.story-province-top {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.story-province-label {
  font-size: 14px;
  letter-spacing: 3px;
  color: #c9b27d;
  margin-bottom: 10px;
  font-weight: 600;
}

.story-province-name {
  font-size: 28px;
  color: #e8c96d;
  letter-spacing: 3px;
  font-weight: 700;
  text-shadow: 0 0 18px #c9a84c66;
}

.story-province-count {
  font-size: 15px;
  color: #e6d5b8b0;
  padding-bottom: 2px;
}

.story-province-actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.story-province-btn {
  padding: 7px 12px;
  border: 1px solid rgba(139, 107, 58, 0.5);
  background: linear-gradient(180deg, rgba(201,168,76,0.08), rgba(255,255,255,0.015));
  color: #e1ca91;
  font-family: 'Noto Serif SC', serif;
  font-size: 12px;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.22s;
}

.story-province-btn:hover {
  border-color: rgba(201, 168, 76, 0.72);
  background: linear-gradient(180deg, rgba(201,168,76,0.14), rgba(255,255,255,0.02));
  text-shadow: 0 0 8px rgba(201, 168, 76, 0.3);
}

.story-province-hint {
  font-size: 11px;
  color: #9d9383;
  letter-spacing: 1px;
}

.story-province-detail {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(139, 107, 58, 0.22);
}

.story-province-map {
  width: 100%;
  height: 156px;
  border: 1px solid rgba(139, 107, 58, 0.24);
  background: rgba(255,255,255,0.01);
}

.story-province-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  padding-bottom: 2px;
}

.story-province-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border: 1px solid rgba(139, 107, 58, 0.24);
  background: linear-gradient(180deg, rgba(255,255,255,0.018), rgba(255,255,255,0.012));
  color: #e6d5b8b5;
  text-align: left;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.22s;
}

.story-province-item:hover {
  border-color: rgba(201, 168, 76, 0.42);
  background: linear-gradient(180deg, rgba(201,168,76,0.06), rgba(255,255,255,0.018));
  color: #e6d5b8;
  transform: translateY(-1px);
}

.story-province-item-name {
  line-height: 1.5;
}

.sidebar {
  flex: 1;
  min-width: 380px;
  max-width: 520px;
  background:
    linear-gradient(180deg, rgba(16, 21, 34, 0.98) 0%, rgba(10, 14, 26, 0.985) 100%),
    radial-gradient(circle at top, rgba(201, 168, 76, 0.06), transparent 34%);
  border-left: 1px solid #8b6b3a44;
  overflow-y: auto;
  padding: 22px 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: -16px 0 32px rgba(0, 0, 0, 0.26);
}

.sidebar::-webkit-scrollbar { width: 4px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: #c9a84c44; border-radius: 2px; }

.period-timeline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  background:
    linear-gradient(180deg, rgba(10,14,26,0.98), rgba(13,18,30,0.98)),
    radial-gradient(circle at center, rgba(201,168,76,0.05), transparent 38%);
  border-top: 1px solid #8b6b3a44;
  flex-shrink: 0;
  box-shadow: 0 -6px 20px rgba(0,0,0,0.18);
}

.period-btn {
  padding: 9px 28px;
  border: 1px solid #8b6b3a3c;
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.005));
  color: #968f83;
  font-family: 'Noto Serif SC', serif;
  font-size: 15px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.25s;
  letter-spacing: 3px;
  position: relative;
  overflow: hidden;
}
.period-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(201,168,76,0.08), transparent);
  opacity: 0;
  transition: opacity 0.25s;
}
.period-btn:hover { color: #c9a84c; border-color: #c9a84c77; }
.period-btn:hover::before { opacity: 1; }
.period-btn.active {
  background: linear-gradient(180deg, rgba(201,168,76,0.14), rgba(201,168,76,0.06));
  color: #e8c96d;
  border-color: #c9a84c;
  text-shadow: 0 0 12px #c9a84c88;
  box-shadow: 0 0 16px rgba(201,168,76,0.2), inset 0 0 12px rgba(201,168,76,0.05);
}

.sidebar-period {
  text-align: center;
  padding: 16px 0 12px;
  border-bottom: 1px solid #8b6b3a2f;
  margin-bottom: 2px;
}
.period-name-label {
  font-size: 28px;
  color: #e8c96d;
  letter-spacing: 5px;
  margin-bottom: 6px;
  text-shadow: 0 0 18px #c9a84c66;
}
.period-sub { font-size: 14px; color: #9c9385; margin-bottom: 10px; letter-spacing: 1px; }
.building-count {
  font-size: 15px; color: #e6d5b8b2;
  display: inline-block;
  padding: 5px 16px;
  border: 1px solid #8b6b3a33;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(201,168,76,0.06), rgba(201,168,76,0.02));
}

.overview-btn {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #8b6b3a55;
  background: linear-gradient(180deg, rgba(201,168,76,0.07), rgba(201,168,76,0.025));
  color: #d3b56e;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.25s;
  letter-spacing: 3px;
  position: relative;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.015);
}
.overview-btn::after {
  content: '';
  position: absolute;
  bottom: 0; left: 50%; right: 50%;
  height: 1px;
  background: #c9a84c;
  transition: all 0.25s;
}
.overview-btn:hover::after, .overview-btn.active::after { left: 0; right: 0; }
.overview-btn:hover, .overview-btn.active {
  background: linear-gradient(180deg, rgba(201,168,76,0.1), rgba(201,168,76,0.035));
  border-color: #c9a84c88;
  text-shadow: 0 0 8px #c9a84c66;
}

.overview-section {
  margin-bottom: 10px;
  padding: 14px 14px 10px;
  border: 1px solid #8b6b3a2d;
  background:
    linear-gradient(180deg, rgba(17, 22, 34, 0.96), rgba(12, 16, 28, 0.92)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.055), transparent 28%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}
.overview-section:nth-of-type(1),
.overview-section:nth-of-type(2) {
  border-color: #9c77403d;
  background:
    linear-gradient(180deg, rgba(18, 24, 37, 0.98), rgba(11, 15, 25, 0.95)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.08), transparent 36%);
}
.overview-title {
  font-size: 14px;
  color: #d2bc8e;
  margin-bottom: 10px;
  letter-spacing: 2px;
  font-family: 'Noto Serif SC', serif;
}
.overview-chart { width: 100%; height: 188px; }
.overview-chart-tall { width: 100%; height: 286px; }
.overview-chart-stack { width: 100%; height: 252px; }

.ruins-pies {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.ruins-period-title {
  font-size: 13px;
  color: #d1bd93;
  text-align: center;
  font-family: 'Noto Serif SC', serif;
  margin-bottom: 6px;
  letter-spacing: 1px;
}
.ruins-pie-item {
  width: 100%;
  height: 144px;
  background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0));
  border: 1px solid rgba(139, 107, 58, 0.22);
}

.type-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid rgba(139, 107, 58, 0.24);
  background:
    linear-gradient(180deg, rgba(17, 22, 34, 0.92), rgba(11, 15, 25, 0.88)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.05), transparent 32%);
}
.type-stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #c9a84c22;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.25s;
  background: rgba(255,255,255,0.02);
  position: relative;
  overflow: hidden;
}
.type-stat-item::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 2px;
  background: #c9a84c;
  opacity: 0;
  transition: opacity 0.25s;
}
.type-stat-item:hover { border-color: #c9a84c55; background: rgba(201,168,76,0.06); }
.type-stat-item:hover::before { opacity: 1; }
.type-stat-item.type-hidden { opacity: 0.35; }
.type-count { margin-left: auto; font-size: 16px; color: #e6d5b8; font-weight: 600; }
.type-toggle-hint { font-size: 13px; color: #8b8680; }

.pie-wrap {
  padding: 12px 12px 10px;
  border: 1px solid rgba(139, 107, 58, 0.24);
  background:
    linear-gradient(180deg, rgba(17, 22, 34, 0.92), rgba(11, 15, 25, 0.88)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.045), transparent 30%);
}
.pie-title { font-size: 14px; color: #d2bc8e; margin-bottom: 8px; letter-spacing: 2px; font-family: 'Noto Serif SC', serif; }
.pie-chart { width: 100%; height: 200px; }

.hint {
  font-size: 14px;
  color: #9d9383;
  text-align: center;
  letter-spacing: 2px;
  padding: 6px 0 2px;
}

.divider-gold { height: 1px; background: linear-gradient(90deg, transparent, #c9a84c44, transparent); }
.my-4 { margin: 8px 0; }
.my-3 { margin: 6px 0; }

.back-to-map {
  background: transparent;
  border: 1px solid #c9a84c44;
  color: #c9a84c;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  padding: 5px 12px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.2s;
}
.back-to-map:hover { background: rgba(201,168,76,0.1); border-color: #c9a84c; }

.building-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  border: 1px solid rgba(139, 107, 58, 0.24);
  background:
    linear-gradient(180deg, rgba(17, 22, 34, 0.92), rgba(11, 15, 25, 0.88)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.045), transparent 30%);
}
.bc-type-row { display: flex; align-items: center; gap: 10px; }
.bc-dynasty { font-size: 14px; color: #8b8680; }
.bc-province { font-size: 14px; color: #8b8680; }
.bc-name { font-size: 28px; letter-spacing: 4px; color: #e8c96d; text-shadow: 0 0 20px #c9a84caa, 0 0 40px #c9a84c44; line-height: 1.3; }
.bc-image-wrap { width: 100%; border-radius: 2px; overflow: hidden; border: 1px solid #c9a84c44; box-shadow: 0 4px 20px rgba(0,0,0,0.4), 0 0 0 1px rgba(201,168,76,0.1); }
.bc-image { width: 100%; height: 200px; object-fit: cover; display: block; transition: transform 0.4s; }
.bc-image-wrap:hover .bc-image { transform: scale(1.03); }
.bc-tagline { font-size: 14px; color: #8b8680; line-height: 1.8; font-style: italic; padding: 8px 12px; border-left: 2px solid #c9a84c44; background: rgba(201,168,76,0.03); }
.bc-desc { font-size: 15px; color: #e6d5b8aa; line-height: 1.9; }

.desc-sections { display: flex; flex-direction: column; gap: 12px; }
.desc-section { }
.desc-section-label { font-size: 14px; color: #c9a84c; margin-bottom: 5px; display: flex; align-items: center; gap: 6px; font-weight: 600; letter-spacing: 1px; }
.desc-label-icon { font-size: 9px; }
.desc-section-body { font-size: 14px; color: #e6d5b8cc; line-height: 1.9; padding-left: 4px; }

.bc-features { }
.bc-features-title { font-size: 14px; color: #c9a84c99; margin-bottom: 8px; letter-spacing: 1px; }
.bc-feature-item {
  font-size: 14px; color: #e6d5b8aa; padding: 6px 10px;
  border-left: 2px solid #c9a84c44; margin-bottom: 6px; line-height: 1.7;
}

.detail-btn {
  width: 100%; padding: 10px;
  background: linear-gradient(135deg, rgba(201,168,76,0.15), rgba(201,168,76,0.05));
  border: 1px solid #c9a84c88;
  color: #e8c96d;
  font-family: 'Noto Serif SC', serif;
  font-size: 14px; cursor: pointer; border-radius: 2px;
  transition: all 0.25s; letter-spacing: 3px;
  text-shadow: 0 0 8px #c9a84c66;
  box-shadow: 0 0 12px rgba(201,168,76,0.1);
}
.detail-btn:hover {
  background: linear-gradient(135deg, rgba(201,168,76,0.25), rgba(201,168,76,0.1));
  border-color: #c9a84c;
  box-shadow: 0 0 20px rgba(201,168,76,0.25);
  text-shadow: 0 0 12px #c9a84caa;
}

.same-province { }
.sp-title { font-size: 14px; color: #c9a84c99; margin-bottom: 8px; letter-spacing: 1px; }
.sp-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; cursor: pointer;
  border: 1px solid transparent; border-radius: 2px;
  transition: all 0.2s; font-size: 14px; color: #e6d5b8aa;
}
.sp-item:hover { border-color: #c9a84c33; background: rgba(201,168,76,0.05); color: #e6d5b8; }
.sp-dynasty { font-size: 12px; color: #8b8680; margin-left: auto; }

.tag {
  display: inline-block; padding: 2px 8px; border-radius: 2px;
  font-size: 13px; font-family: 'Noto Serif SC', serif;
}
.tag-皇宫 { background: rgba(232,201,109,0.15); color: #e8c96d; border: 1px solid #e8c96d44; }
.tag-官府 { background: rgba(0,212,255,0.1); color: #00d4ff; border: 1px solid #00d4ff44; }
.tag-民居 { background: rgba(129,199,132,0.1); color: #81c784; border: 1px solid #81c78444; }
.tag-桥梁 { background: rgba(255,138,101,0.1); color: #ff8a65; border: 1px solid #ff8a6544; }

.text-glow-gold { color: #c9a84c; text-shadow: 0 0 10px #c9a84c66; }

@media (max-width: 1280px) {
  .map-storyboard {
    width: min(370px, calc(100% - 36px));
  }

  .map-story-title {
    font-size: 26px;
  }
}

@media (max-width: 760px) {
  .map-storyboard {
    top: 12px;
    left: 12px;
    width: calc(100% - 24px);
    padding: 16px 16px 14px;
  }

  .map-story-title {
    font-size: 22px;
    letter-spacing: 2px;
  }

  .map-story-copy {
    font-size: 13px;
    line-height: 1.8;
  }

  .story-province-top,
  .story-province-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .story-province-name {
    font-size: 22px;
  }
}
</style>
