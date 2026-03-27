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

const PERIODS = ['先秦两汉', '魏晋隋唐', '宋辽金元', '明清']
const TYPES = ['皇宫', '官府', '民居', '桥梁']
const typeColors = { '皇宫': '#e8c96d', '官府': '#00d4ff', '民居': '#81c784', '桥梁': '#ff8a65' }
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
watch(hiddenTypes, () => nextTick(updatePie))
watch(pieChart, el => { if (el) nextTick(initPie) })

async function initCCMap() {
  if (!ccMapRef.value || !topProvince.value) return
  if (ccMapInstance) ccMapInstance.dispose()
  ccMapInstance = echarts.init(ccMapRef.value, null, { renderer: 'svg' })
  const geoData = await fetch('/china-provinces.json').then(r => r.json())
  const provinceName = topProvince.value.province
  const feature = geoData.features.find(f =>
    f.properties.name.replace(/省|市|自治区|壮族|回族|维吾尔/g, '').includes(provinceName.replace(/省|市|自治区/g, ''))
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
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c}座 ({d}%)', ...TOOLTIP_STYLE },
      series: [{
        type: 'pie', radius: ['40%', '68%'], center: ['50%', '50%'],
        data: [
          { name: '现存', value: existing, itemStyle: { color: '#c9a84c' } },
          { name: '遗址/已毁', value: ruins, itemStyle: { color: '#00d4ff88' } }
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
        <div class="concentration-card" v-if="topProvince">
          <div class="cc-label">建筑最密集省份</div>
          <div class="cc-province">{{ topProvince.province }}</div>
          <div class="cc-count">共 {{ topProvince.count }} 座古建筑</div>
          <div ref="ccMapRef" class="cc-map" />
          <div class="cc-divider" />
          <div class="cc-list">
            <div v-for="b in topProvince.list" :key="b.name" class="cc-item">
              <span :class="`tag tag-${b.type}`" style="font-size:9px;padding:1px 4px;">{{ b.type }}</span>
              {{ b.name }}
            </div>
          </div>
        </div>
      </div>

      <div class="sidebar">
        <template v-if="!selectedBuilding">
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
                  <div style="font-size:13px;color:#c9a84c;text-align:center;font-family:'Noto Serif SC',serif;margin-bottom:4px;">{{ p }}</div>
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
              <div class="pie-title">着作分布与类型结构</div>
              <div ref="pieChart" class="pie-chart" />
            </div>
            <div class="divider-gold my-4" />
            <div class="hint">点击地图上的建筑查看详情</div>
          </template>
        </template>

        <template v-else>
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
                <img :src="selectedBuilding.imageUrl" :alt="selectedBuilding.name" class="bc-image"
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
        </template>
      </div>
    </div>

    <div class="period-timeline">
      <button
        v-for="p in [{ id: 'all', name: '全部' }, ...periods]"
        :key="p.id || p.name"
        class="period-btn"
        :class="{ active: activePeriod === (p.id === 'all' ? 'all' : p.name) }"
        @click="activePeriod = p.id === 'all' ? 'all' : p.name; selectedBuilding = null"
      >{{ p.name }}</button>
    </div>
  </div>
</template>

<style scoped>
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
  padding: 0 32px;
  height: 56px;
  background: rgba(10,14,26,0.98);
  border-bottom: 1px solid #c9a84c55;
  flex-shrink: 0;
  z-index: 100;
  box-shadow: 0 2px 24px rgba(201,168,76,0.08);
}

.nav-title {
  font-size: 24px;
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
  gap: 32px;
}

.nav-links a {
  color: #8b8680;
  text-decoration: none;
  font-size: 14px;
  letter-spacing: 2px;
  transition: all 0.3s;
  position: relative;
  padding-bottom: 2px;
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
  flex: 7;
  position: relative;
  overflow: hidden;
}

.sidebar {
  flex: 3;
  min-width: 280px;
  max-width: 360px;
  background: linear-gradient(180deg, rgba(12,16,28,0.98) 0%, rgba(10,14,26,0.98) 100%);
  border-left: 1px solid #c9a84c33;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: -4px 0 24px rgba(0,0,0,0.3);
}

.sidebar::-webkit-scrollbar { width: 4px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: #c9a84c44; border-radius: 2px; }

.period-timeline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 24px;
  background: rgba(10,14,26,0.98);
  border-top: 1px solid #c9a84c44;
  flex-shrink: 0;
  box-shadow: 0 -2px 20px rgba(201,168,76,0.06);
}

.period-btn {
  padding: 6px 18px;
  border: 1px solid #c9a84c33;
  background: transparent;
  color: #8b8680;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.25s;
  letter-spacing: 2px;
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
  background: rgba(201,168,76,0.12);
  color: #e8c96d;
  border-color: #c9a84c;
  text-shadow: 0 0 12px #c9a84c88;
  box-shadow: 0 0 16px rgba(201,168,76,0.2), inset 0 0 12px rgba(201,168,76,0.05);
}

.sidebar-period {
  text-align: center;
  padding: 12px 0 8px;
  border-bottom: 1px solid #c9a84c22;
  margin-bottom: 4px;
}
.period-name-label {
  font-size: 22px;
  color: #e8c96d;
  letter-spacing: 4px;
  margin-bottom: 4px;
  text-shadow: 0 0 16px #c9a84c77;
}
.period-sub { font-size: 12px; color: #8b8680; margin-bottom: 6px; letter-spacing: 1px; }
.building-count {
  font-size: 13px; color: #e6d5b8aa;
  display: inline-block;
  padding: 2px 10px;
  border: 1px solid #c9a84c22;
  border-radius: 10px;
  background: rgba(201,168,76,0.04);
}

.overview-btn {
  width: 100%;
  padding: 8px;
  border: 1px solid #c9a84c44;
  background: transparent;
  color: #c9a84c;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.25s;
  letter-spacing: 2px;
  position: relative;
  overflow: hidden;
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
  background: rgba(201,168,76,0.08);
  border-color: #c9a84c77;
  text-shadow: 0 0 8px #c9a84c66;
}

.overview-section { margin-bottom: 8px; }
.overview-title { font-size: 12px; color: #c9a84c99; margin-bottom: 4px; letter-spacing: 1px; }
.overview-chart { width: 100%; height: 140px; }
.overview-chart-tall { width: 100%; height: 220px; }
.overview-chart-stack { width: 100%; height: 160px; }

.ruins-pies {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.ruins-pie-item { width: 100%; height: 100px; }

.type-stats { display: flex; flex-direction: column; gap: 6px; }
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
.type-count { margin-left: auto; font-size: 14px; color: #e6d5b8; font-weight: 600; }
.type-toggle-hint { font-size: 11px; color: #8b8680; }

.pie-wrap { }
.pie-title { font-size: 12px; color: #c9a84c99; margin-bottom: 4px; letter-spacing: 1px; }
.pie-chart { width: 100%; height: 160px; }

.divider-gold { height: 1px; background: linear-gradient(90deg, transparent, #c9a84c44, transparent); }
.my-4 { margin: 8px 0; }
.my-3 { margin: 6px 0; }
.hint { font-size: 12px; color: #8b8680; text-align: center; letter-spacing: 1px; }

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

.building-card { display: flex; flex-direction: column; gap: 8px; }
.bc-type-row { display: flex; align-items: center; gap: 8px; }
.bc-dynasty { font-size: 12px; color: #8b8680; }
.bc-province { font-size: 12px; color: #8b8680; }
.bc-name { font-size: 24px; letter-spacing: 4px; color: #e8c96d; text-shadow: 0 0 20px #c9a84caa, 0 0 40px #c9a84c44; line-height: 1.3; }
.bc-image-wrap { width: 100%; border-radius: 2px; overflow: hidden; border: 1px solid #c9a84c44; box-shadow: 0 4px 20px rgba(0,0,0,0.4), 0 0 0 1px rgba(201,168,76,0.1); }
.bc-image { width: 100%; height: 180px; object-fit: cover; display: block; transition: transform 0.4s; }
.bc-image-wrap:hover .bc-image { transform: scale(1.03); }
.bc-tagline { font-size: 12px; color: #8b8680; line-height: 1.7; font-style: italic; padding: 6px 10px; border-left: 2px solid #c9a84c44; background: rgba(201,168,76,0.03); }
.bc-desc { font-size: 13px; color: #e6d5b8aa; line-height: 1.8; }

.desc-sections { display: flex; flex-direction: column; gap: 8px; }
.desc-section { }
.desc-section-label { font-size: 12px; color: #c9a84c; margin-bottom: 3px; display: flex; align-items: center; gap: 4px; }
.desc-label-icon { font-size: 8px; }
.desc-section-body { font-size: 12px; color: #e6d5b8aa; line-height: 1.7; }

.bc-features { }
.bc-features-title { font-size: 12px; color: #c9a84c99; margin-bottom: 6px; letter-spacing: 1px; }
.bc-feature-item {
  font-size: 12px; color: #e6d5b8aa; padding: 4px 8px;
  border-left: 2px solid #c9a84c44; margin-bottom: 4px;
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
.sp-title { font-size: 12px; color: #c9a84c99; margin-bottom: 6px; letter-spacing: 1px; }
.sp-item {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 8px; cursor: pointer;
  border: 1px solid transparent; border-radius: 2px;
  transition: all 0.2s; font-size: 12px; color: #e6d5b8aa;
}
.sp-item:hover { border-color: #c9a84c33; background: rgba(201,168,76,0.05); color: #e6d5b8; }
.sp-dynasty { font-size: 11px; color: #8b8680; margin-left: auto; }

.concentration-card {
  position: absolute; bottom: 16px; left: 16px; z-index: 500;
  background: rgba(10,14,26,0.95);
  border: 1px solid #c9a84c55;
  border-radius: 4px; padding: 14px 16px;
  min-width: 170px; max-width: 210px;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(201,168,76,0.08);
}
.cc-label { font-size: 11px; color: #8b8680; letter-spacing: 2px; margin-bottom: 6px; text-transform: uppercase; }
.cc-province { font-size: 22px; color: #e8c96d; letter-spacing: 3px; font-weight: 700; text-shadow: 0 0 16px #c9a84c88; }
.cc-count { font-size: 12px; color: #e6d5b8aa; margin-bottom: 8px; }
.cc-map { width: 100%; height: 100px; }
.cc-divider { height: 1px; background: linear-gradient(90deg, transparent, #c9a84c44, transparent); margin: 8px 0; }
.cc-list { display: flex; flex-direction: column; gap: 4px; }
.cc-item { font-size: 12px; color: #e6d5b8aa; display: flex; align-items: center; gap: 4px; }

.tag {
  display: inline-block; padding: 1px 6px; border-radius: 2px;
  font-size: 11px; font-family: 'Noto Serif SC', serif;
}
.tag-皇宫 { background: rgba(232,201,109,0.15); color: #e8c96d; border: 1px solid #e8c96d44; }
.tag-官府 { background: rgba(0,212,255,0.1); color: #00d4ff; border: 1px solid #00d4ff44; }
.tag-民居 { background: rgba(129,199,132,0.1); color: #81c784; border: 1px solid #81c78444; }
.tag-桥梁 { background: rgba(255,138,101,0.1); color: #ff8a65; border: 1px solid #ff8a6544; }

.text-glow-gold { color: #c9a84c; text-shadow: 0 0 10px #c9a84c66; }
</style>
