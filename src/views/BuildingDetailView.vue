<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted, nextTick } from 'vue'
import { buildings } from '../data/buildings.js'
import buildingsFull from '../data/buildings_full.json'
import { works } from '../data/works.js'
import { craftsmen } from '../data/craftsmen.js'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()
const BASE = import.meta.env.BASE_URL
const assetUrl = (path) => path ? BASE + path.replace(/^\//, '') : ''

const building = computed(() => buildings.find(b => b.id === route.params.id))
const relatedWorks = computed(() => works.filter(w => building.value?.relatedWorks?.includes(w.id)))
const relatedPersons = computed(() => craftsmen.filter(c => building.value?.relatedPersons?.includes(c.id)))
const timelineBuildingPool = computed(() => {
  const merged = new Map()
  for (const item of (buildingsFull || [])) {
    if (!item?.id) continue
    merged.set(item.id, { ...item, isFeatured: Boolean(item.isFeatured) })
  }
  for (const item of buildings) {
    if (!item?.id) continue
    const prev = merged.get(item.id) || {}
    merged.set(item.id, { ...prev, ...item, isFeatured: true })
  }
  return Array.from(merged.values())
})

const PERIODS = ['先秦两汉', '魏晋隋唐', '宋辽金元', '明清']
const PERIOD_YEARS = {
  '先秦两汉': '前221-220年',
  '魏晋隋唐': '220-907年',
  '宋辽金元': '907-1368年',
  '明清': '1368-1912年'
}
const TYPE_COLOR = { '皇宫': '#e8c96d', '官府': '#00d4ff', '民居': '#81c784', '桥梁': '#ff8a65' }
const DETAIL_TOOLTIP_STYLE = {
  backgroundColor: 'rgba(19, 24, 33, 0.96)',
  borderWidth: 1,
  padding: [10, 14],
  textStyle: { color: '#e6d5b8', fontSize: 13, fontFamily: 'Noto Serif SC' },
  extraCssText: 'box-shadow:0 10px 24px rgba(0,0,0,0.32);'
}

const timelineRef = ref(null)
let timelineChart = null

function initTimeline() {
  if (!timelineRef.value || !building.value) return
  if (timelineChart) timelineChart.dispose()
  timelineChart = echarts.init(timelineRef.value, null, { renderer: 'svg' })

  const curPeriod = building.value.period
  const curType = building.value.type

  const sameType = timelineBuildingPool.value.filter(b => (
    b.type === curType
    && PERIODS.includes(b.period)
    && typeof b.name === 'string'
    && b.name.trim()
  ))

  const periodGroups = PERIODS.map(p => sameType.filter(b => b.period === p))

  const scatterData = []
  let yMin = 0
  let yMax = 0

  PERIODS.forEach((_, pi) => {
    const group = [...periodGroups[pi]].sort((a, b) => {
      const aCurrent = a.id === building.value.id ? 1 : 0
      const bCurrent = b.id === building.value.id ? 1 : 0
      if (aCurrent !== bCurrent) return bCurrent - aCurrent

      const aFeatured = a.isFeatured ? 1 : 0
      const bFeatured = b.isFeatured ? 1 : 0
      if (aFeatured !== bFeatured) return bFeatured - aFeatured

      return String(a.name || '').localeCompare(String(b.name || ''), 'zh-Hans-CN')
    })

    group.forEach((b, bi) => {
      const isCurrent = b.id === building.value.id
      const isFeatured = Boolean(b.isFeatured)
      const angle = (bi * 137.5) * Math.PI / 180
      const radius = 0.14 * Math.sqrt(bi)
      const xOffset = Math.max(-0.34, Math.min(0.34, radius * Math.cos(angle)))
      const yPos = radius * Math.sin(angle) * 1.85

      yMin = Math.min(yMin, yPos)
      yMax = Math.max(yMax, yPos)

      scatterData.push({
        value: [pi, yPos],
        id: b.id,
        buildingName: b.name,
        isCurrent,
        isFeatured,
        symbolSize: isCurrent ? 17 : isFeatured ? 10 : 6,
        itemStyle: {
          color: isCurrent ? TYPE_COLOR[curType] : isFeatured ? TYPE_COLOR[curType] + 'aa' : TYPE_COLOR[curType] + '55',
          borderColor: TYPE_COLOR[curType],
          borderWidth: isCurrent ? 2 : isFeatured ? 1 : 0.8,
          shadowBlur: isCurrent ? 12 : 0,
          shadowColor: TYPE_COLOR[curType] + '88'
        },
        label: {
          show: isCurrent || isFeatured,
          position: xOffset >= 0 ? 'right' : 'left',
          distance: isCurrent ? 10 : 7,
          color: isCurrent ? TYPE_COLOR[curType] : '#8b8680',
          fontSize: isCurrent ? 14 : 12,
          fontFamily: 'Noto Serif SC',
          formatter: p => p.data.buildingName
        }
      })
    })
  })

  const yPadding = 0.35
  const yAxisMin = Math.min(-1.4, yMin - yPadding)
  const yAxisMax = Math.max(1.4, yMax + yPadding)

  timelineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      borderColor: '#c9a84c44',
      formatter: p => p.data?.buildingName || '',
      ...DETAIL_TOOLTIP_STYLE
    },
    grid: { left: 40, right: 40, top: 40, bottom: 20 },
    xAxis: {
      type: 'category',
      data: PERIODS,
      position: 'top',
      axisLabel: {
        fontSize: 13,
        fontFamily: 'Noto Serif SC',
        rich: {
          cur: { color: TYPE_COLOR[curType], fontSize: 14, fontFamily: 'Noto Serif SC', fontWeight: 'bold', lineHeight: 22 },
          curYear: { color: TYPE_COLOR[curType], fontSize: 10, fontFamily: 'Noto Serif SC', lineHeight: 16, opacity: 0.8 },
          dim: { color: '#8b8680', fontSize: 13, fontFamily: 'Noto Serif SC', lineHeight: 22 },
          dimYear: { color: '#8b8680', fontSize: 10, fontFamily: 'Noto Serif SC', lineHeight: 16, opacity: 0.6 }
        },
        formatter: val => {
          const year = PERIOD_YEARS[val] || ''
          return val === curPeriod
            ? `{cur|${val}}\n{curYear|${year}}`
            : `{dim|${val}}\n{dimYear|${year}}`
        }
      },
      axisLine: { lineStyle: { color: '#c9a84c44' } },
      axisTick: { show: false },
      splitLine: { show: false }
    },
    yAxis: { show: false, min: yAxisMin, max: yAxisMax },
    series: [{
      type: 'scatter',
      data: scatterData,
      symbolSize: p => p.symbolSize || 10,
      itemStyle: { color: p => p.data?.itemStyle?.color },
      emphasis: {
        scale: true,
        label: {
          show: true,
          color: '#e6d5b8',
          fontSize: 12,
          fontFamily: 'Noto Serif SC',
          formatter: p => p.data?.buildingName || ''
        }
      },
      labelLayout: {
        hideOverlap: true,
        moveOverlap: 'shiftY'
      }
    }]
  })
}

const comparisonRef = ref(null)
let comparisonChart = null

function initComparison() {
  if (!comparisonRef.value || !building.value?.comparison) return
  if (comparisonChart) comparisonChart.dispose()
  comparisonChart = echarts.init(comparisonRef.value, null, { renderer: 'svg' })

  const cmp = building.value.comparison
  const color = TYPE_COLOR[building.value.type]

  if (cmp.chartType === 'bar-horizontal') {
    const sorted = [...cmp.peers].sort((a, b) => b.value - a.value)
    comparisonChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis', axisPointer: { type: 'none' },
        borderColor: color + '44',
        formatter: p => `${p[0].name}：${p[0].value} ${cmp.unit}`,
        ...DETAIL_TOOLTIP_STYLE
      },
      grid: { left: 120, right: 60, top: 16, bottom: 16, containLabel: false },
      xAxis: { type: 'value', show: false },
      yAxis: {
        type: 'category',
        data: sorted.map(p => p.name),
        axisLabel: {
          color: p => {
            const peer = sorted.find(x => x.name === p)
            return peer?.isCurrent ? color : peer?.isExternal ? '#8b8680' : color + 'aa'
          },
          fontSize: 13, fontFamily: 'Noto Serif SC',
        },
        axisLine: { show: false }, axisTick: { show: false },
        splitLine: { show: false },
      },
      series: [{
        type: 'bar', data: sorted.map(p => ({
          value: p.value,
          itemStyle: {
            color: p.isCurrent ? color : p.isExternal ? '#4a4a4a' : color + '55',
            borderColor: p.isCurrent ? color : 'transparent',
            borderWidth: p.isCurrent ? 1 : 0,
          }
        })),
        barMaxWidth: 20,
        label: { show: true, position: 'right', color: '#e6d5b8', fontSize: 12,
          formatter: p => `${p.value} ${cmp.unit}` }
      }]
    })
  } else if (cmp.chartType === 'bubble') {
    const peers = cmp.peers
    const maxVal = Math.max(...peers.map(x => x.value))
    const internalColors = ['#c9a84c', '#e8c96d', '#d4956a', '#cd853f', '#b8860b']
    const externalColors = ['#7a9bb5', '#8aacbf', '#6b8fa8', '#5c7d96', '#4a7a9b']
    let internalIdx = 0, externalIdx = 0
    const peerColors = peers.map(p => {
      if (p.isCurrent) return color
      if (p.isExternal) return externalColors[externalIdx++ % externalColors.length]
      return internalColors[internalIdx++ % internalColors.length]
    })
    comparisonChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        borderColor: color + '44',
        formatter: p => `${p.data.name}：${p.data.actualValue} ${cmp.unit}`,
        ...DETAIL_TOOLTIP_STYLE
      },
      grid: { left: 40, right: 40, top: 60, bottom: 48 },
      xAxis: {
        type: 'category',
        data: peers.map(p => p.name),
        axisLabel: { color: '#8b8680', fontSize: 12, fontFamily: 'Noto Serif SC', rotate: 20 },
        axisLine: { lineStyle: { color: '#c9a84c44' } }, axisTick: { show: false },
      },
      yAxis: { show: false, min: 0, max: 1 },
      series: [{
        type: 'scatter',
        data: peers.map((p, i) => ({
          value: [i, 0.5],
          name: p.name,
          actualValue: p.value,
          itemStyle: {
            color: peerColors[i],
            borderColor: peerColors[i],
            borderWidth: p.isCurrent ? 2 : 1,
            opacity: p.isCurrent ? 1 : 0.8,
          },
          label: {
            show: true,
            color: peerColors[i],
          }
        })),
        symbolSize: (val, params) => {
          const v = params.data.actualValue
          return Math.max(16, Math.sqrt(v / maxVal) * 80)
        },
        label: {
          show: true, position: 'top', fontFamily: 'Noto Serif SC', fontSize: 12,
          formatter: p => `${p.data.name}\n${p.data.actualValue}${cmp.unit}`
        },
        labelLayout: { hideOverlap: false }
      }]
    })
  } else if (cmp.chartType === 'radar') {
    const peers = cmp.peers
    // 鍥介鑹茶皟锛屾瘡鏉＄嚎涓嶅悓棰滆壊
    const radarColors = ['#e8c96d', '#81c784', '#ff8a65', '#00d4ff', '#c792ea', '#f48fb1', '#80cbc4', '#ffcc80']
    comparisonChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', borderColor: color + '44', ...DETAIL_TOOLTIP_STYLE },
      legend: {
        data: peers.map(p => p.name), bottom: 0,
        textStyle: { color: '#8b8680', fontSize: 14, fontFamily: 'Noto Serif SC' },
        itemWidth: 12, itemHeight: 12,
      },
      radar: {
        indicator: cmp.radarIndicators,
        center: ['50%', '45%'], radius: '60%',
        axisName: { color: '#8b8680', fontSize: 15, fontFamily: 'Noto Serif SC' },
        splitLine: { lineStyle: { color: '#c9a84c22' } },
        splitArea: { show: false },
        axisLine: { lineStyle: { color: '#c9a84c33' } },
      },
      series: [{
        type: 'radar',
        data: peers.map((p, i) => {
          const c = p.isCurrent ? color : radarColors.filter(r => r !== color)[i % (radarColors.length - 1)]
          return {
            name: p.name,
            value: p.value,
            lineStyle: { color: c, width: p.isCurrent ? 2 : 1.5, opacity: p.isCurrent ? 1 : 0.7 },
            areaStyle: { color: c + (p.isCurrent ? '30' : '10') },
            itemStyle: { color: c },
            symbol: 'circle', symbolSize: p.isCurrent ? 5 : 3,
          }
        })
      }]
    })
  } else if (cmp.chartType === 'gauge') {
    const sorted = [...cmp.peers].sort((a, b) => b.value - a.value)
    comparisonChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis', axisPointer: { type: 'none' },
        borderColor: color + '44',
        formatter: p => `${p[0].name}：${p[0].value} ${cmp.unit}`,
        ...DETAIL_TOOLTIP_STYLE
      },
      grid: { left: 130, right: 80, top: 16, bottom: 16, containLabel: false },
      xAxis: { type: 'value', show: false },
      yAxis: {
        type: 'category',
        data: sorted.map(p => p.name),
        axisLabel: {
          fontSize: 13, fontFamily: 'Noto Serif SC',
          color: (val) => {
            const peer = sorted.find(x => x.name === val)
            return peer?.isCurrent ? color : peer?.isExternal ? '#8b8680' : color + 'aa'
          }
        },
        axisLine: { show: false }, axisTick: { show: false },
      },
      series: [{
        type: 'bar',
        data: sorted.map(p => ({
          value: p.value,
          itemStyle: {
            color: p.isCurrent ? color : p.isExternal ? '#4a4a4a' : color + '55',
            borderColor: p.isCurrent ? color : 'transparent',
            borderWidth: p.isCurrent ? 1 : 0,
          }
        })),
        barMaxWidth: 20,
        label: { show: true, position: 'right', color: '#e6d5b8', fontSize: 12,
          formatter: p => `${p.value} ${cmp.unit}` }
      }]
    })
  }
}

onMounted(() => nextTick(() => { initTimeline(); initComparison() }))
</script>

<template>
  <div class="detail-page" v-if="building">

    <!-- 鈶?椤堕儴鑻遍泟鍖?-->
    <div class="hero" :style="building.imageUrl ? `background-image:url(${assetUrl(building.imageUrl)})` : ''">
      <div class="hero-overlay" />
      <button class="back-btn" @click="router.back()">← 返回</button>
      <div class="hero-content">
        <h1 class="hero-name text-glow-gold">{{ building.name }}</h1>
        <p class="hero-tagline" v-if="building.tagline">{{ building.tagline }}</p>
      </div>
    </div>

    <!-- 鈶?鍩烘湰淇℃伅鏉?-->
    <div class="info-bar">
      <div class="info-item">
        <span class="info-icon">朝</span>
        <span class="info-value">{{ building.dynasty }}</span>
      </div>
      <div class="info-divider" />
      <div class="info-item">
        <span class="info-icon" :style="`color:${TYPE_COLOR[building.type]};border-color:${TYPE_COLOR[building.type]}66`">类</span>
        <span class="info-value" :style="`color:${TYPE_COLOR[building.type]}`">{{ building.type }}</span>
      </div>
      <div class="info-divider" />
      <div class="info-item">
        <span class="info-icon">省</span>
        <span class="info-value">{{ building.province }}</span>
      </div>
      <div class="info-divider" />
      <div class="info-item">
        <span class="info-icon">市</span>
        <span class="info-value">{{ building.city }}</span>
      </div>
      <div class="info-divider" />
      <div class="info-item">
        <span class="info-icon">期</span>
        <span class="info-value">{{ building.period }}</span>
      </div>
    </div>

    <div class="detail-body">

      <!-- 建筑在历史中的位置 -->
      <section class="section">
        <div class="section-title">
          <span class="section-title-bar" />
          建筑在历史中的位置
        </div>
        <p class="description">{{ building.description }}</p>
        <div class="timeline-wrap">
          <div class="timeline-periods">
            <div v-for="p in PERIODS" :key="p" class="timeline-period" :class="{ active: p === building.period }">
              <div class="period-dot" />
              <div class="period-name">{{ p }}</div>
              <div class="period-years">{{ PERIOD_YEARS[p] }}</div>
            </div>
          </div>
          <div ref="timelineRef" class="timeline-chart" />
        </div>
        <div class="siblings-hint" v-if="buildings.filter(b => b.period === building.period && b.type === building.type && b.id !== building.id && b.isFeatured).length">
          <span class="hint-label">同时期同类型建筑：</span>
          <span
            v-for="b in buildings.filter(b => b.period === building.period && b.type === building.type && b.id !== building.id && b.isFeatured)"
            :key="b.id"
            class="sibling-tag"
            :style="`border-color:${TYPE_COLOR[b.type]}44;color:${TYPE_COLOR[b.type]}`"
            @click="router.push(`/building/${b.id}`)"
          >{{ b.name }}</span>
        </div>
      </section>

      <!-- 建筑特色 -->
      <section class="section">
        <div class="section-title">
          <span class="section-title-bar" />
          建筑特色
        </div>
        <div class="features-grid">
          <div
            v-for="(f, i) in (building.featuresDetail || building.features.map(t => ({ title: t, body: '' })))"
            :key="i"
            class="feature-card"
          >
            <div class="feature-index">{{ String(i + 1).padStart(2, '0') }}</div>
            <div class="feature-content">
              <div class="feature-title">{{ f.title }}</div>
              <div class="feature-body" v-if="f.body">{{ f.body }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 横向比较 -->
      <section class="section" v-if="building.comparison">
        <div class="section-title">
          <span class="section-title-bar" />
          横向比较
        </div>
        <p class="comparison-note">{{ building.comparison.note }}</p>
        <div ref="comparisonRef" class="comparison-chart"
          :style="building.comparison.chartType === 'radar' ? 'height:360px' : `height:${Math.max(240, building.comparison.peers.length * 36 + 40)}px`"
        />
        <div class="comparison-legend">
          <span class="legend-item"><span class="legend-dot current" :style="`background:${TYPE_COLOR[building.type]}`" />当前建筑</span>
          <span class="legend-item"><span class="legend-dot internal" :style="`background:${TYPE_COLOR[building.type]}55`" />同系列建筑</span>
          <span class="legend-item"><span class="legend-dot external" />外部参照</span>
        </div>
      </section>

      <!-- 相关著作与工匠 -->
      <section class="section" v-if="building.isFeatured && (relatedWorks.length || relatedPersons.length)">
        <div class="section-title">
          <span class="section-title-bar" />
          相关著作与工匠
        </div>
        <div class="related-grid" v-if="relatedWorks.length">
          <div class="related-sub-title">经典著作</div>
          <div class="related-cards">
            <div class="related-card" v-for="w in relatedWorks" :key="w.id">
              <div class="related-card-title">{{ w.title }}</div>
              <div class="related-card-meta">{{ w.author }} · {{ w.dynasty }} · {{ w.year }}</div>
              <div class="related-card-body">{{ w.significance }}</div>
            </div>
          </div>
        </div>
        <div class="related-grid mt-6" v-if="relatedPersons.length">
          <div class="related-sub-title">代表工匠</div>
          <div class="related-cards">
            <div class="related-card" v-for="c in relatedPersons" :key="c.id">
              <div class="related-card-title">{{ c.name }}</div>
              <div class="related-card-meta">{{ c.dynasty }} · {{ c.title }}</div>
              <div class="related-card-body">{{ c.achievement }}</div>
            </div>
          </div>
        </div>
      </section>

    </div>
  </div>

  <div v-else class="not-found">建筑数据未找到</div>
</template>

<style scoped>
/* 鑻遍泟鍖?*/
.hero {
  position: relative;
  width: 100%;
  height: 460px;
  background: var(--color-ink-light);
  background-size: cover;
  background-position: center;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.hero-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(to bottom, rgba(8,12,18,0.16) 0%, rgba(8,12,18,0.82) 72%, rgba(8,12,18,0.92) 100%),
    radial-gradient(circle at top left, rgba(201, 168, 76, 0.08), transparent 30%);
}
.back-btn {
  position: absolute;
  top: 24px;
  left: 32px;
  background: linear-gradient(180deg, rgba(17,23,33,0.74), rgba(10,14,20,0.6));
  border: 1px solid rgba(122, 96, 48, 0.72);
  color: #c5b79b;
  font-family: 'Noto Serif SC', serif;
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.1em;
  padding: 6px 16px;
  transition: color 0.3s, border-color 0.3s;
  z-index: 10;
}
.back-btn:hover { color: var(--color-gold-light); border-color: var(--color-gold); }
.hero-content {
  position: relative;
  z-index: 2;
  padding: 0 48px 36px;
}
.hero-name {
  font-size: 56px;
  color: var(--color-gold-light);
  letter-spacing: 0.2em;
  font-family: 'Noto Serif SC', serif;
  margin-bottom: 12px;
  text-shadow: 0 0 40px rgba(201,168,76,0.6);
}
.hero-tagline {
  font-size: 15px;
  color: var(--color-text-dim);
  line-height: 1.9;
  max-width: 700px;
  font-family: 'Noto Serif SC', serif;
  letter-spacing: 0.05em;
}

/* 鍩烘湰淇℃伅鏉?*/
.info-bar {
  display: flex;
  align-items: center;
  background:
    linear-gradient(180deg, rgba(16, 22, 32, 0.97), rgba(10,14,20,0.95)),
    radial-gradient(circle at center, rgba(201,168,76,0.05), transparent 45%);
  border-bottom: 1px solid rgba(122, 96, 48, 0.72);
  padding: 0 48px;
}
.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 18px 24px;
}
.info-icon {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(122, 96, 48, 0.78);
  color: var(--color-gold);
  font-size: 12px;
  font-family: 'Noto Serif SC', serif;
  display: flex;
  align-items: center;
  justify-content: center;
}
.info-label {
  font-size: 11px;
  color: var(--color-text-dim);
  letter-spacing: 0.1em;
}
.info-value {
  font-size: 15px;
  color: var(--color-gold-light);
  font-family: 'Noto Serif SC', serif;
  letter-spacing: 0.08em;
}
.info-divider {
  width: 1px;
  height: 32px;
  background: rgba(122, 96, 48, 0.72);
}

/* 涓讳綋 */
.detail-body {
  padding: 52px 48px 64px;
  display: flex;
  flex-direction: column;
  gap: 52px;
  width: min(1460px, 100%);
  margin: 0 auto;
  background:
    linear-gradient(180deg, rgba(10, 14, 20, 1) 0%, rgba(13, 17, 23, 1) 100%),
    radial-gradient(circle at top, rgba(201, 168, 76, 0.035), transparent 30%);
}

.section {
  padding: 0 2px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 21px;
  color: var(--color-gold-light);
  font-family: 'Noto Serif SC', serif;
  letter-spacing: 0.14em;
  margin-bottom: 22px;
  text-shadow: 0 0 14px rgba(201, 168, 76, 0.16);
}
.section-title-bar {
  display: inline-block;
  width: 4px;
  height: 22px;
  background: linear-gradient(180deg, var(--color-gold-light), var(--color-gold));
  box-shadow: 0 0 10px rgba(201, 168, 76, 0.18);
}

.description {
  font-size: 17px;
  line-height: 2;
  color: var(--color-text);
  margin-bottom: 22px;
  max-width: 920px;
  padding: 0 0 0 18px;
  border-left: 2px solid rgba(201, 168, 76, 0.28);
}

/* 鏃堕棿杞?*/
.timeline-wrap {
  background:
    linear-gradient(180deg, rgba(21, 26, 37, 0.9), rgba(12, 16, 28, 0.88)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.055), transparent 34%);
  border: 1px solid rgba(122, 96, 48, 0.75);
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}
.timeline-periods { display: none; }
.timeline-period {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  opacity: 0.4;
  transition: opacity 0.3s;
}
.timeline-period.active { opacity: 1; }
.period-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-gold-dim);
  border: 2px solid var(--color-gold-dim);
}
.timeline-period.active .period-dot {
  background: var(--color-gold);
  border-color: var(--color-gold);
  box-shadow: 0 0 8px var(--color-gold);
}
.period-name {
  font-size: 13px;
  color: var(--color-text-dim);
  font-family: 'Noto Serif SC', serif;
}
.timeline-period.active .period-name { color: var(--color-gold-light); }
.period-years { font-size: 10px; color: var(--color-text-dim); opacity: 0.6; }
.timeline-chart { width: 100%; height: 270px; }

.siblings-hint {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 14px 0;
}
.hint-label { font-size: 12px; color: var(--color-text-dim); }
.sibling-tag {
  font-size: 12px;
  padding: 4px 10px;
  border: 1px solid;
  font-family: 'Noto Serif SC', serif;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.2s;
  background: rgba(255,255,255,0.015);
}
.sibling-tag:hover { opacity: 0.82; transform: translateY(-1px); }

/* 寤虹瓚鐗硅壊 */
.features-grid {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.feature-card {
  display: flex;
  gap: 18px;
  padding: 22px 22px 20px;
  border: 1px solid rgba(122, 96, 48, 0.74);
  background:
    linear-gradient(180deg, rgba(20, 25, 36, 0.82), rgba(14, 19, 30, 0.78)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.05), transparent 32%);
  transition: border-color 0.3s, transform 0.28s, box-shadow 0.28s;
  min-height: 172px;
}
.feature-card:hover {
  border-color: var(--color-gold);
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.16);
}
.feature-index {
  font-size: 38px;
  color: var(--color-gold-dim);
  font-family: 'Noto Serif SC', serif;
  line-height: 1;
  min-width: 54px;
  padding-top: 2px;
}
.feature-content { flex: 1; }
.feature-title {
  font-size: 20px;
  color: var(--color-gold-light);
  font-family: 'Noto Serif SC', serif;
  letter-spacing: 0.08em;
  margin-bottom: 12px;
  line-height: 1.45;
}
.feature-body {
  font-size: 16px;
  color: var(--color-text);
  line-height: 1.92;
}

/* 鐩稿叧钁椾綔宸ュ尃 */
.related-grid {
  padding: 18px 18px 16px;
  border: 1px solid rgba(122, 96, 48, 0.38);
  background:
    linear-gradient(180deg, rgba(17, 22, 34, 0.72), rgba(11, 15, 25, 0.66)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.05), transparent 34%);
}
.related-sub-title {
  font-size: 15px;
  color: var(--color-gold);
  letter-spacing: 0.14em;
  margin-bottom: 14px;
  font-family: 'Noto Serif SC', serif;
}
.related-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.related-card {
  min-width: 0;
  max-width: none;
  padding: 18px 18px 16px;
  border: 1px solid rgba(122, 96, 48, 0.72);
  background:
    linear-gradient(180deg, rgba(20, 25, 36, 0.82), rgba(14, 19, 30, 0.78)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.045), transparent 32%);
  min-height: 148px;
  transition: border-color 0.28s, transform 0.28s, box-shadow 0.28s;
}
.related-card:hover {
  border-color: rgba(201, 168, 76, 0.82);
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.16);
}
.related-card-title {
  font-size: 17px;
  color: var(--color-gold-light);
  font-family: 'Noto Serif SC', serif;
  margin-bottom: 8px;
  line-height: 1.45;
}
.related-card-meta {
  font-size: 12px;
  color: var(--color-text-dim);
  margin-bottom: 10px;
  letter-spacing: 0.04em;
}
.related-card-body {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.82;
}
.mt-6 { margin-top: 24px; }

/* 妯悜姣旇緝 */
.comparison-note {
  font-size: 14px;
  color: var(--color-text-dim);
  line-height: 1.82;
  margin-bottom: 18px;
  font-family: 'Noto Serif SC', serif;
  max-width: 860px;
  padding-left: 14px;
  border-left: 2px solid rgba(201, 168, 76, 0.18);
}
.comparison-chart {
  width: 100%;
  background:
    linear-gradient(180deg, rgba(21, 26, 37, 0.9), rgba(12, 16, 28, 0.88)),
    radial-gradient(circle at top right, rgba(201, 168, 76, 0.055), transparent 34%);
  border: 1px solid rgba(122, 96, 48, 0.75);
  margin-bottom: 12px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}
.comparison-legend {
  display: flex;
  gap: 20px;
  align-items: center;
  padding-left: 2px;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-dim);
  font-family: 'Noto Serif SC', serif;
  padding: 4px 8px;
  border: 1px solid rgba(122, 96, 48, 0.28);
  background: rgba(255,255,255,0.015);
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.legend-dot.external {
  background: #4a4a4a;
}

.not-found {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-dim);
}

@media (max-width: 1100px) {
  .hero {
    height: 420px;
  }

  .hero-name {
    font-size: 46px;
  }

  .info-bar {
    flex-wrap: wrap;
    padding: 0 32px;
  }

  .info-item {
    padding: 14px 18px;
  }

  .info-divider {
    display: none;
  }

  .detail-body {
    padding: 40px 32px 56px;
    gap: 44px;
  }

}

@media (max-width: 720px) {
  .hero {
    height: 360px;
  }

  .back-btn {
    top: 18px;
    left: 18px;
  }

  .hero-content {
    padding: 0 20px 24px;
  }

  .hero-name {
    font-size: 34px;
    letter-spacing: 0.12em;
  }

  .hero-tagline {
    font-size: 14px;
    max-width: none;
  }

  .info-bar {
    padding: 8px 16px;
    gap: 6px 0;
  }

  .info-item {
    width: 50%;
    padding: 10px 8px;
  }

  .detail-body {
    padding: 28px 16px 40px;
    gap: 36px;
  }

  .section-title {
    font-size: 18px;
    letter-spacing: 0.1em;
    margin-bottom: 18px;
  }

  .description,
  .comparison-note {
    font-size: 15px;
    line-height: 1.9;
    padding-left: 12px;
  }

  .timeline-wrap,
  .feature-card,
  .related-grid {
    padding: 16px;
  }

  .timeline-chart {
    height: 250px;
  }

  .related-cards {
    grid-template-columns: 1fr;
  }
}
</style>


