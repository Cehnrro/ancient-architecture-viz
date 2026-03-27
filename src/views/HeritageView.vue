<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { works as worksData } from '../data/works.js'
import { craftsmen as craftsmenData } from '../data/craftsmen.js'
import { buildings as featuredBuildings } from '../data/buildings.js'
import buildingsFull from '../data/buildings_full.json'
import { lineageEdges, lineageRelationTypes } from '../data/lineage.js'
import { craftBuildingRelations } from '../data/craft_building_relations.js'
import { workCraftRelations } from '../data/work_craft_relations.js'
import { workBuildingRelations } from '../data/work_building_relations.js'
import DetailDrawer from '../components/heritage/DetailDrawer.vue'

const router = useRouter()
const route = useRoute()

const PERIODS = ['先秦两汉', '魏晋隋唐', '宋辽金元', '明清']
const TYPES = ['皇宫', '官府', '民居', '桥梁']
const SANKEY_BUILDING_TYPES = ['all', ...TYPES]
const SANKEY_MAX_SCHOOL_NODES = 999
const SANKEY_MAX_WORK_NODES = 999
const SANKEY_REPRESENTATIVE_CONFIG = {
  all: {
    worksPerType: 4,
    maxSchools: 9,
    maxSchoolsPerWork: 2,
  },
  focused: {
    worksPerType: 8,
    maxSchools: 10,
    maxSchoolsPerWork: 3,
  },
}
const WORK_TIMELINE_BUCKET_YEAR = 50
const RELATION_ORDER = ['mentor', 'student', 'collab', 'school']
const TYPE_COLOR = {
  皇宫: '#e8c96d',
  官府: '#00d4ff',
  民居: '#81c784',
  桥梁: '#ff8a65',
}
const RELATION_COLOR = {
  mentor: '#e8c96d',
  student: '#7bc8a4',
  collab: '#5ab8ff',
  school: '#ff8a65',
}
const PERIOD_COLOR = {
  先秦两汉: '#8b6914',
  魏晋隋唐: '#1a6b8a',
  宋辽金元: '#2d6a4f',
  明清: '#8b1a1a',
}
const RELATION_LABEL = {
  AUTHOR: '作者',
  EDIT: '编修',
  QUOTE: '引用记述',
  PRACTICE: '实践应用关联',
  INSTITUTION: '制度关联',
  URBAN: '都城规划关联',
  DESIGN: '设计',
  BUILD: '主持营建',
  SUPERVISE: '监造',
  REPAIR: '修缮',
  DOC: '文献记述关联',
}
const WORKS_ROUTE_PATH = '/works'
const LINEAGE_ROUTE_PATH = '/lineage'

const activeTab = ref('works')

function resolveTabByPath(path) {
  return path === LINEAGE_ROUTE_PATH ? 'craftsmen' : 'works'
}

const selectedWorkPeriod = ref('all')
const selectedWorkType = ref('all')
const selectedCraftPeriod = ref('all')
const selectedCraftType = ref('all')
const selectedCraftSchool = ref('all')
const selectedSankeyBuildingType = ref('all')

const detailDrawer = ref({
  visible: false,
  entityType: 'work',
  entityId: null,
})
const focusedCraftId = ref(null)

const works = worksData
const craftsmen = craftsmenData

const workMap = computed(() => {
  const map = {}
  works.forEach(item => {
    map[item.id] = item
  })
  return map
})

const craftMap = computed(() => {
  const map = {}
  craftsmen.forEach(item => {
    map[item.id] = item
  })
  return map
})

const buildingMap = computed(() => {
  const map = {}
  buildingsFull.forEach(item => {
    map[item.id] = item
  })
  featuredBuildings.forEach(item => {
    map[item.id] = {
      ...(map[item.id] || {}),
      ...item,
      isFeatured: true,
    }
  })
  return map
})

const featuredBuildingIdSet = computed(() => new Set(featuredBuildings.map(item => item.id)))

const craftBuildingRelationMap = computed(() => {
  const map = {}
  craftBuildingRelations.forEach(rel => {
    if (!map[rel.craftId]) map[rel.craftId] = {}
    map[rel.craftId][rel.buildingId] = rel
  })
  return map
})

const workCraftRelationMap = computed(() => {
  const map = {}
  workCraftRelations.forEach(rel => {
    if (!map[rel.workId]) map[rel.workId] = {}
    map[rel.workId][rel.craftId] = rel
  })
  return map
})

const workBuildingRelationMap = computed(() => {
  const map = {}
  workBuildingRelations.forEach(rel => {
    if (!map[rel.workId]) map[rel.workId] = {}
    map[rel.workId][rel.buildingId] = rel
  })
  return map
})

const totalSourceRefs = computed(() => {
  const refs = new Set()
  works.forEach(w => (w.sourceRefs || []).forEach(s => refs.add(s)))
  craftsmen.forEach(c => (c.sourceRefs || []).forEach(s => refs.add(s)))
  return refs.size
})

function extractApproxYear(work) {
  const yearText = String(work?.year || '').trim()
  if (yearText) {
    const rangeMatch = yearText.match(/(\d{3,4})\s*[-—至]\s*(\d{2,4})/)
    if (rangeMatch) {
      const start = Number(rangeMatch[1])
      const endRaw = rangeMatch[2]
      const end = Number(endRaw.length < 4 ? `${String(start).slice(0, 4 - endRaw.length)}${endRaw}` : endRaw)
      if (Number.isFinite(start) && Number.isFinite(end)) return Math.round((start + end) / 2)
    }

    const centuryMatch = yearText.match(/(前)?\s*(\d{1,2})\s*世纪/)
    if (centuryMatch) {
      const n = Number(centuryMatch[2])
      if (Number.isFinite(n)) {
        if (centuryMatch[1]) return -((n - 1) * 100 + 50)
        return (n - 1) * 100 + 50
      }
    }

    const yearMatch = yearText.match(/(前)?\s*(\d{1,4})\s*年/)
    if (yearMatch) {
      const n = Number(yearMatch[2])
      if (Number.isFinite(n)) return yearMatch[1] ? -n : n
    }

    const plainMatch = yearText.match(/(前)?\s*(\d{3,4})/)
    if (plainMatch) {
      const n = Number(plainMatch[2])
      if (Number.isFinite(n)) return plainMatch[1] ? -n : n
    }
  }

  const dynastyText = `${work?.dynasty || ''}${work?.period || ''}`
  if (/先秦|战国|春秋/.test(dynastyText)) return -400
  if (/秦|西汉|东汉|两汉/.test(dynastyText)) return 0
  if (/魏|晋|南北朝/.test(dynastyText)) return 380
  if (/隋|唐/.test(dynastyText)) return 700
  if (/宋|辽|金|元/.test(dynastyText)) return 1150
  if (/明|清/.test(dynastyText)) return 1650
  return null
}

function stableUnitHash(seed) {
  const text = String(seed || '')
  let hash = 0
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 131 + text.charCodeAt(i)) % 1000003
  }
  return (hash / 1000003) * 2 - 1
}

function normalizeDynastyLabel(rawDynasty, withWeiJinTangDetails = false) {
  const value = String(rawDynasty || '')
    .replace(/[（(].*?[）)]/g, '')
    .replace(/\s+/g, '')
    .trim()
  if (!value) return '未知'

  if (/先秦/.test(value)) return '先秦'
  if (/春秋/.test(value)) return '春秋'
  if (/战国/.test(value)) return '战国'
  if (/西汉/.test(value)) return '西汉'
  if (/东汉/.test(value)) return '东汉'
  if (/两汉|汉魏/.test(value)) return '两汉'
  if (/曹魏/.test(value)) return withWeiJinTangDetails ? '曹魏' : '南北朝'
  if (/魏晋|晋/.test(value)) return withWeiJinTangDetails ? '晋' : '南北朝'
  if (/北魏|北周|南朝宋|南北朝/.test(value)) return '南北朝'
  if (/隋/.test(value)) return '隋'
  if (/唐/.test(value)) return '唐'
  if (/北宋/.test(value)) return '北宋'
  if (/南宋/.test(value)) return '南宋'
  if (/金元/.test(value)) return '元'
  if (/元/.test(value)) return '元'
  if (/明/.test(value)) return '明'
  if (/清/.test(value)) return '清'
  if (/民国/.test(value)) return '民国'
  if (/秦/.test(value)) return '秦'
  if (/汉/.test(value)) return '汉'
  return value
}

const CONFIDENCE_ORDER = { A: 0, B: 1, C: 2 }
const WORKS_PAGE_SIZE = 4
const CRAFTS_PAGE_SIZE = 8

const worksPage = ref(1)
const craftsPage = ref(1)

function compareByPriority(a, b) {
  if (a.tier !== b.tier) return a.tier === 'core' ? -1 : 1
  const c1 = CONFIDENCE_ORDER[a.confidence] ?? 9
  const c2 = CONFIDENCE_ORDER[b.confidence] ?? 9
  if (c1 !== c2) return c1 - c2
  const p1 = PERIODS.indexOf(a.period)
  const p2 = PERIODS.indexOf(b.period)
  if (p1 !== p2) return p1 - p2
  return a.id.localeCompare(b.id)
}

function getCraftSchoolLabel(craft) {
  return craft.schoolTags?.[0] || craft.primaryType || '未分类'
}

const filteredWorks = computed(() => {
  let list = works
  if (selectedWorkPeriod.value !== 'all') {
    list = list.filter(w => w.period === selectedWorkPeriod.value)
  }
  if (selectedWorkType.value !== 'all') {
    list = list.filter(w => w.primaryType === selectedWorkType.value)
  }
  return [...list].sort(compareByPriority)
})

const workTimelinePoints = computed(() => {
  const bucketMap = new Map()
  filteredWorks.value.forEach(work => {
    const year = extractApproxYear(work)
    if (!Number.isFinite(year)) return
    const bucket = Math.floor(year / WORK_TIMELINE_BUCKET_YEAR) * WORK_TIMELINE_BUCKET_YEAR
    const key = `${work.primaryType}::${bucket}`
    const current = bucketMap.get(key) || {
      type: work.primaryType,
      bucket,
      count: 0,
      workIds: [],
      yearSum: 0,
    }
    current.count += 1
    current.workIds.push(work.id)
    current.yearSum += year
    bucketMap.set(key, current)
  })
  return [...bucketMap.values()]
    .map(item => ({
      ...item,
      anchorYear: Math.round(item.yearSum / item.count),
    }))
    .sort((a, b) => a.anchorYear - b.anchorYear)
})

const filteredCraftsmen = computed(() => {
  let list = craftsmen
  if (selectedCraftPeriod.value !== 'all') {
    list = list.filter(c => c.period === selectedCraftPeriod.value)
  }
  if (selectedCraftType.value !== 'all') {
    list = list.filter(c => c.primaryType === selectedCraftType.value)
  }
  if (selectedCraftSchool.value !== 'all') {
    list = list.filter(c => getCraftSchoolLabel(c) === selectedCraftSchool.value)
  }
  return [...list].sort(compareByPriority)
})

const activeLineageEdges = computed(() => {
  const visibleIds = new Set(filteredCraftsmen.value.map(c => c.id))
  return lineageEdges.filter(edge => visibleIds.has(edge.source) && visibleIds.has(edge.target))
})

const connectedLineageIds = computed(() => {
  const ids = new Set()
  activeLineageEdges.value.forEach(edge => {
    ids.add(edge.source)
    ids.add(edge.target)
  })
  return ids
})

const visibleLineageCraftsmen = computed(() => {
  if (!connectedLineageIds.value.size) return filteredCraftsmen.value
  return filteredCraftsmen.value.filter(item => connectedLineageIds.value.has(item.id) || item.id === focusedCraftId.value)
})

const worksTotalPages = computed(() => Math.max(1, Math.ceil(filteredWorks.value.length / WORKS_PAGE_SIZE)))
const craftsTotalPages = computed(() => Math.max(1, Math.ceil(visibleLineageCraftsmen.value.length / CRAFTS_PAGE_SIZE)))

const pagedWorks = computed(() => {
  const start = (worksPage.value - 1) * WORKS_PAGE_SIZE
  return filteredWorks.value.slice(start, start + WORKS_PAGE_SIZE)
})

const pagedCraftsmen = computed(() => {
  const start = (craftsPage.value - 1) * CRAFTS_PAGE_SIZE
  return visibleLineageCraftsmen.value.slice(start, start + CRAFTS_PAGE_SIZE)
})

const lineageNodes = computed(() => {
  const connected = connectedLineageIds.value

  return visibleLineageCraftsmen.value.map(item => {
    const isFocused = focusedCraftId.value === item.id
    const hasConnection = connected.has(item.id)
    return {
      id: item.id,
      name: item.name,
      category: Math.max(0, TYPES.indexOf(item.primaryType)),
      value: item.impactLevel || (item.tier === 'core' ? 5 : 3),
      symbolSize: isFocused ? 34 : item.tier === 'core' ? 23 : 17,
      itemStyle: {
        color: TYPE_COLOR[item.primaryType] || '#c9a84c',
        opacity: isFocused ? 1 : hasConnection ? 0.95 : 0.7,
        shadowBlur: isFocused ? 18 : 8,
        shadowColor: TYPE_COLOR[item.primaryType] || '#c9a84c',
      },
      label: {
        show: isFocused || hasConnection,
        color: isFocused ? '#e8c96d' : '#c9a84c',
        fontFamily: 'Noto Serif SC',
      },
    }
  })
})

const sankeyGraph = computed(() => {
  const seeds = []
  const workScoreByType = new Map()
  const workTotalScore = new Map()
  const workTitleById = new Map()

  filteredCraftsmen.value.forEach(craft => {
    const rawSchool = getCraftSchoolLabel(craft)
    resolveWorks(craft.relatedWorks).forEach(work => {
      const buildingTypes = (work.buildingTypes?.length ? work.buildingTypes : [work.primaryType])
        .filter(Boolean)
        .filter(type => selectedSankeyBuildingType.value === 'all' || type === selectedSankeyBuildingType.value)
      if (!buildingTypes.length) return

      seeds.push({
        rawSchool,
        workId: work.id,
        workTitle: work.title,
        buildingTypes,
      })
      workTitleById.set(work.id, work.title)
      buildingTypes.forEach(type => {
        const typeMap = workScoreByType.get(type) || new Map()
        typeMap.set(work.id, (typeMap.get(work.id) || 0) + 1)
        workScoreByType.set(type, typeMap)
      })
      workTotalScore.set(work.id, (workTotalScore.get(work.id) || 0) + 1)
    })
  })

  const isAllMode = selectedSankeyBuildingType.value === 'all'
  const cfg = isAllMode ? SANKEY_REPRESENTATIVE_CONFIG.all : SANKEY_REPRESENTATIVE_CONFIG.focused
  const targetTypes = isAllMode ? TYPES : [selectedSankeyBuildingType.value]
  const selectedWorkIds = new Set()
  targetTypes.forEach(type => {
    const ranking = [...(workScoreByType.get(type) || new Map()).entries()]
      .sort((a, b) => b[1] - a[1] || (workTotalScore.get(b[0]) || 0) - (workTotalScore.get(a[0]) || 0))
      .slice(0, cfg.worksPerType)
      .map(([workId]) => workId)
    ranking.forEach(workId => selectedWorkIds.add(workId))
  })
  if (!selectedWorkIds.size) {
    return { nodes: [], links: [], meta: { schoolNodeCount: 0, workNodeCount: 0, nodeNameMap: {} } }
  }

  const schoolScore = new Map()
  const schoolByWork = new Map()
  seeds.forEach(seed => {
    if (!selectedWorkIds.has(seed.workId)) return
    schoolScore.set(seed.rawSchool, (schoolScore.get(seed.rawSchool) || 0) + 1)
    const m = schoolByWork.get(seed.workId) || new Map()
    m.set(seed.rawSchool, (m.get(seed.rawSchool) || 0) + 1)
    schoolByWork.set(seed.workId, m)
  })
  const selectedSchools = new Set(
    [...schoolScore.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, cfg.maxSchools)
      .map(([school]) => school),
  )
  selectedWorkIds.forEach(workId => {
    const m = schoolByWork.get(workId)
    if (!m?.size) return
    const bestSchool = [...m.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]
    if (bestSchool) selectedSchools.add(bestSchool)
  })

  const nodeMap = new Map()
  const linkMap = new Map()

  function addNode(id, displayName, nodeKind, color, extras = {}) {
    if (nodeMap.has(id)) return
    const { itemStyle: extraItemStyle, label: extraLabel, ...restExtras } = extras
    nodeMap.set(id, {
      name: id,
      displayName,
      nodeKind,
      ...restExtras,
      itemStyle: {
        color,
        borderColor: '#2d2d2d',
        borderWidth: 1,
        ...(extraItemStyle || {}),
      },
      label: {
        color: '#e6d5b8',
        fontFamily: 'Noto Serif SC',
        ...(extraLabel || {}),
      },
    })
  }

  function addLink(source, target, amount = 1) {
    const key = `${source}::${target}`
    const current = linkMap.get(key) || { source, target, value: 0 }
    current.value += amount
    linkMap.set(key, current)
  }

  function arrangeCenterOut(nodes, getWeight, pinnedLastName = null) {
    const core = []
    const pinned = []
    nodes.forEach(node => {
      if (pinnedLastName && node.displayName === pinnedLastName) {
        pinned.push(node)
      } else {
        core.push(node)
      }
    })
    core.sort((a, b) => (getWeight(b) || 0) - (getWeight(a) || 0))
    const arranged = []
    let flip = true
    core.forEach((node, idx) => {
      if (idx === 0) {
        arranged.push(node)
        return
      }
      if (flip) arranged.unshift(node)
      else arranged.push(node)
      flip = !flip
    })
    return [...arranged, ...pinned]
  }

  seeds.forEach(seed => {
    if (!selectedWorkIds.has(seed.workId) || !selectedSchools.has(seed.rawSchool)) return

    const schoolId = `school:${seed.rawSchool}`
    const workId = `work:${seed.workId}`
    addNode(schoolId, seed.rawSchool, 'school', '#74a3d9', { schoolLabel: seed.rawSchool })
    addNode(workId, workTitleById.get(seed.workId) || seed.workTitle, 'work', '#c9a84c', { workId: seed.workId })
    addLink(schoolId, workId, 1)

    seed.buildingTypes.forEach(type => {
      const typeId = `type:${type}`
      addNode(typeId, type, 'type', TYPE_COLOR[type] || '#81c784', { typeLabel: type })
      addLink(workId, typeId, 1)
    })
  })

  const rawLinks = [...linkMap.values()]
  const incomingByWork = new Map()
  rawLinks.forEach(link => {
    if (!(link.source.startsWith('school:') && link.target.startsWith('work:'))) return
    const list = incomingByWork.get(link.target) || []
    list.push(link)
    incomingByWork.set(link.target, list)
  })
  const keptLinkKeys = new Set()
  const keptWorkIds = new Set()
  incomingByWork.forEach((list, workId) => {
    const picks = [...list]
      .sort((a, b) => b.value - a.value)
      .slice(0, cfg.maxSchoolsPerWork)
    if (!picks.length && list.length) picks.push(list[0])
    picks.forEach(link => {
      keptLinkKeys.add(`${link.source}::${link.target}`)
      keptWorkIds.add(workId)
    })
  })
  rawLinks.forEach(link => {
    if (link.source.startsWith('work:') && link.target.startsWith('type:') && keptWorkIds.has(link.source)) {
      keptLinkKeys.add(`${link.source}::${link.target}`)
    }
  })
  let links = rawLinks
    .filter(link => keptLinkKeys.has(`${link.source}::${link.target}`))
    .map(link => ({ ...link }))

  const incomingValueByWork = new Map()
  const outgoingLinksByWork = new Map()
  links.forEach(link => {
    if (link.source.startsWith('school:') && link.target.startsWith('work:')) {
      incomingValueByWork.set(link.target, (incomingValueByWork.get(link.target) || 0) + link.value)
      return
    }
    if (link.source.startsWith('work:') && link.target.startsWith('type:')) {
      const list = outgoingLinksByWork.get(link.source) || []
      list.push(link)
      outgoingLinksByWork.set(link.source, list)
    }
  })
  outgoingLinksByWork.forEach((outLinks, workId) => {
    const incoming = incomingValueByWork.get(workId) || 0
    const outgoing = outLinks.reduce((sum, link) => sum + link.value, 0)
    if (!incoming || !outgoing) return
    const scale = incoming / outgoing
    outLinks.forEach(link => {
      link.value = Number((link.value * scale).toFixed(4))
    })
  })
  const connected = new Set()
  links.forEach(link => {
    connected.add(link.source)
    connected.add(link.target)
  })

  const schoolScoreFinal = new Map()
  const workScoreFinal = new Map()
  const typeWeightCounter = new Map()
  links.forEach(link => {
    if (link.source.startsWith('school:') && link.target.startsWith('work:')) {
      schoolScoreFinal.set(link.source, (schoolScoreFinal.get(link.source) || 0) + link.value)
      workScoreFinal.set(link.target, (workScoreFinal.get(link.target) || 0) + link.value)
    }
    if (link.source.startsWith('work:') && link.target.startsWith('type:')) {
      typeWeightCounter.set(link.target, (typeWeightCounter.get(link.target) || 0) + link.value)
    }
  })

  const schoolNodes = arrangeCenterOut(
    [...nodeMap.values()]
      .filter(node => node.nodeKind === 'school')
      .filter(node => connected.has(node.name)),
    node => schoolScoreFinal.get(node.name) || 0,
  )
  const workNodes = arrangeCenterOut(
    [...nodeMap.values()]
      .filter(node => node.nodeKind === 'work')
      .filter(node => connected.has(node.name)),
    node => workScoreFinal.get(node.name) || 0,
  )
  const typeNodes = arrangeCenterOut(
    [...nodeMap.values()]
      .filter(node => node.nodeKind === 'type')
      .filter(node => connected.has(node.name)),
    node => typeWeightCounter.get(node.name) || 0,
  )
  const nodes = [...schoolNodes, ...workNodes, ...typeNodes]

  return {
    nodes,
    links,
    meta: {
      schoolNodeCount: new Set(nodes.filter(node => node.nodeKind === 'school').map(node => node.name)).size,
      workNodeCount: new Set(nodes.filter(node => node.nodeKind === 'work').map(node => node.name)).size,
      nodeNameMap: Object.fromEntries(nodes.map(node => [node.name, node.displayName || node.name])),
      isAllMode,
    },
  }
})

const selectedWorkId = computed(() => {
  if (!detailDrawer.value.visible || detailDrawer.value.entityType !== 'work') return null
  return detailDrawer.value.entityId
})

const selectedCraftId = computed(() => {
  if (!detailDrawer.value.visible || detailDrawer.value.entityType !== 'craft') return null
  return detailDrawer.value.entityId
})

const drawerPayload = computed(() => {
  if (!detailDrawer.value.visible || !detailDrawer.value.entityId) return null

  if (detailDrawer.value.entityType === 'work') {
    const work = workMap.value[detailDrawer.value.entityId]
    if (!work) return null

    return {
      typeLabel: '文化著作详情',
      title: work.title,
      subtitle: `${work.author} · ${work.dynasty} · ${work.year}`,
      description: work.significance || work.summary,
      infoRows: [
        { label: '时期', value: work.period },
        { label: '主类型', value: work.primaryType },
        { label: '作者', value: work.author },
        { label: '朝代', value: work.dynasty },
        { label: '时间', value: work.year },
      ],
      tags: work.buildingTypes || [],
      keywords: work.keywords || [],
      groups: [
        {
          title: '关联工匠',
          items: resolveWorkCraftItems(work),
        },
        {
          title: '关联建筑',
          items: resolveWorkBuildingItems(work),
        },
      ],
    }
  }

  const craft = craftMap.value[detailDrawer.value.entityId]
  if (!craft) return null

  const relatedWorks = resolveWorks(craft.relatedWorks)
  const relatedCrafts = resolveCrafts([...(craft.mentorIds || []), ...(craft.studentIds || [])])

  return {
    typeLabel: '科学家谱系详情',
    title: craft.name,
    subtitle: `${craft.dynasty} · ${craft.title}`,
    description: craft.achievement,
    infoRows: [
      { label: '时期', value: craft.period },
      { label: '主类型', value: craft.primaryType },
      { label: '职衔', value: craft.title },
      { label: '朝代', value: craft.dynasty },
      { label: '籍贯', value: craft.hometown },
    ],
    tags: craft.buildingTypes || [],
    keywords: craft.schoolTags || [],
    groups: [
      {
        title: '关联著作',
        items: relatedWorks.map(w => ({ id: w.id, label: w.title, kind: 'work' })),
      },
      {
        title: '关联工匠',
        items: relatedCrafts.map(c => ({ id: c.id, label: c.name, kind: 'craft' })),
      },
      {
        title: '关联建筑',
        items: resolveCraftBuildingItems(craft),
      },
    ],
  }
})

function resolveCrafts(ids) {
  return (ids || []).map(id => craftMap.value[id]).filter(Boolean)
}

function resolveWorks(ids) {
  return (ids || []).map(id => workMap.value[id]).filter(Boolean)
}

function resolveBuildings(ids) {
  return (ids || []).map(id => ({ id, ...(buildingMap.value[id] || { name: id }) }))
}

function formatRelationType(type) {
  return RELATION_LABEL[type] || type || ''
}

function resolveCraftBuildingItems(craft) {
  const relByBuilding = craftBuildingRelationMap.value[craft.id] || {}
  return resolveBuildings(craft.relatedBuildings).map(building => {
    const rel = relByBuilding[building.id]
    return {
      id: building.id,
      label: building.name,
      kind: 'building',
      clickable: featuredBuildingIdSet.value.has(building.id),
      chipMeta: rel
        ? {
            relationType: formatRelationType(rel.relationType),
            isCrossPeriod: rel.isCrossPeriod,
          }
        : null,
    }
  })
}

function resolveWorkCraftItems(work) {
  const relByCraft = workCraftRelationMap.value[work.id] || {}
  return resolveCrafts(work.relatedCraftsmen).map(craft => {
    const rel = relByCraft[craft.id]
    return {
      id: craft.id,
      label: craft.name,
      kind: 'craft',
      chipMeta: rel
        ? {
            relationType: formatRelationType(rel.relationType),
            isCrossPeriod: rel.isCrossPeriod,
          }
        : null,
    }
  })
}

function resolveWorkBuildingItems(work) {
  const relByBuilding = workBuildingRelationMap.value[work.id] || {}
  return resolveBuildings(work.relatedBuildings).map(building => {
    const rel = relByBuilding[building.id]
    return {
      id: building.id,
      label: building.name,
      kind: 'building',
      clickable: featuredBuildingIdSet.value.has(building.id),
      chipMeta: rel
        ? {
            relationType: formatRelationType(rel.relationType),
            isCrossPeriod: rel.isCrossPeriod,
          }
        : null,
    }
  })
}

function locatePage(list, id, pageSize) {
  const idx = list.findIndex(item => item.id === id)
  if (idx < 0) return 1
  return Math.floor(idx / pageSize) + 1
}

function openDrawer(entityType, entityId) {
  detailDrawer.value = {
    visible: true,
    entityType,
    entityId,
  }
}

function closeDetailDrawer() {
  detailDrawer.value.visible = false
}

function focusWorkInCurrentFilter(id) {
  worksPage.value = locatePage(filteredWorks.value, id, WORKS_PAGE_SIZE)
  openDrawer('work', id)
}

function focusCraftInCurrentFilter(id) {
  focusedCraftId.value = id
  craftsPage.value = locatePage(visibleLineageCraftsmen.value, id, CRAFTS_PAGE_SIZE)
  openDrawer('craft', id)
  if (activeTab.value === 'craftsmen') {
    nextTick(() => renderLineageChart())
  }
}

async function openWorkContext(id) {
  const item = workMap.value[id]
  if (!item) return
  selectedWorkPeriod.value = item.period
  selectedWorkType.value = item.primaryType
  if (route.path !== WORKS_ROUTE_PATH) {
    await router.push(WORKS_ROUTE_PATH)
  }
  activeTab.value = 'works'
  await ensureWorksDashboard()
  focusWorkInCurrentFilter(id)
}

async function openCraftContext(id) {
  const item = craftMap.value[id]
  if (!item) return
  selectedCraftPeriod.value = item.period
  selectedCraftType.value = item.primaryType
  selectedCraftSchool.value = 'all'
  if (route.path !== LINEAGE_ROUTE_PATH) {
    await router.push(LINEAGE_ROUTE_PATH)
  }
  activeTab.value = 'craftsmen'
  await ensureCraftDashboard()
  focusCraftInCurrentFilter(id)
}

function openWorkCard(id) {
  openDrawer('work', id)
}

function openCraftCard(id) {
  focusCraftInCurrentFilter(id)
}

function jumpToBuilding(id) {
  if (!featuredBuildingIdSet.value.has(id)) return
  router.push(`/building/${id}`)
  closeDetailDrawer()
}

function handleDrawerOpenWork(id) {
  openWorkContext(id)
}

function handleDrawerOpenCraft(id) {
  openCraftContext(id)
}

function handleDrawerOpenBuilding(id) {
  jumpToBuilding(id)
}

function handleSankeyNodeClick(node) {
  if (!node?.nodeKind) return

  if (node.nodeKind === 'work' && node.workId) {
    openWorkContext(node.workId)
    return
  }

  if (node.nodeKind === 'school' && node.schoolLabel) {
    selectedCraftSchool.value = selectedCraftSchool.value === node.schoolLabel ? 'all' : node.schoolLabel
    return
  }

  if (node.nodeKind === 'type' && node.typeLabel) {
    selectedSankeyBuildingType.value = selectedSankeyBuildingType.value === node.typeLabel ? 'all' : node.typeLabel
  }
}

function clearWorksFilter() {
  selectedWorkPeriod.value = 'all'
  selectedWorkType.value = 'all'
  worksPage.value = 1
}

function clearCraftFilter() {
  selectedCraftPeriod.value = 'all'
  selectedCraftType.value = 'all'
  selectedCraftSchool.value = 'all'
  selectedSankeyBuildingType.value = 'all'
  craftsPage.value = 1
}

function prevWorksPage() {
  worksPage.value = Math.max(1, worksPage.value - 1)
}

function nextWorksPage() {
  worksPage.value = Math.min(worksTotalPages.value, worksPage.value + 1)
}

function prevCraftsPage() {
  craftsPage.value = Math.max(1, craftsPage.value - 1)
}

function nextCraftsPage() {
  craftsPage.value = Math.min(craftsTotalPages.value, craftsPage.value + 1)
}

const worksPeriodRef = ref(null)
const worksTypeRef = ref(null)
const worksTimelineRef = ref(null)
const lineageRef = ref(null)
const sankeyRef = ref(null)

let worksPeriodChart = null
let worksTypeChart = null
let worksTimelineChart = null
let lineageChart = null
let sankeyChart = null

const TOOLTIP_STYLE = {
  backgroundColor: '#161b22',
  borderColor: '#c9a84c44',
  textStyle: { color: '#e6d5b8', fontSize: 12, fontFamily: 'Noto Serif SC' },
}

function initWorksCharts() {
  if (worksPeriodChart && worksPeriodChart.getDom() !== worksPeriodRef.value) {
    worksPeriodChart.dispose()
    worksPeriodChart = null
  }
  if (worksPeriodRef.value && !worksPeriodChart) {
    worksPeriodChart = echarts.init(worksPeriodRef.value, null, { renderer: 'svg' })
    worksPeriodChart.on('click', params => {
      const period = params.name
      selectedWorkPeriod.value = selectedWorkPeriod.value === period ? 'all' : period
    })
  }

  if (worksTypeChart && worksTypeChart.getDom() !== worksTypeRef.value) {
    worksTypeChart.dispose()
    worksTypeChart = null
  }
  if (worksTypeRef.value && !worksTypeChart) {
    worksTypeChart = echarts.init(worksTypeRef.value, null, { renderer: 'svg' })
    worksTypeChart.on('click', params => {
      const type = params.name
      selectedWorkType.value = selectedWorkType.value === type ? 'all' : type
    })
  }

  if (worksTimelineChart && worksTimelineChart.getDom() !== worksTimelineRef.value) {
    worksTimelineChart.dispose()
    worksTimelineChart = null
  }
  if (worksTimelineRef.value && !worksTimelineChart) {
    worksTimelineChart = echarts.init(worksTimelineRef.value, null, { renderer: 'svg' })
  }

  renderWorksCharts()
}

function renderWorksCharts() {
  if (!worksPeriodChart || !worksTypeChart || !worksTimelineChart) return

  const periodBase = selectedWorkType.value === 'all'
    ? works
    : works.filter(w => w.primaryType === selectedWorkType.value)

  worksPeriodChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...TOOLTIP_STYLE },
    grid: { left: 40, right: 14, top: 20, bottom: 36 },
    xAxis: {
      type: 'category',
      data: PERIODS,
      axisLabel: { color: '#c9a84c', fontFamily: 'Noto Serif SC', fontSize: 12 },
      axisLine: { lineStyle: { color: '#c9a84c44' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8b8680' },
      splitLine: { lineStyle: { color: '#c9a84c22' } },
    },
    series: [{
      type: 'bar',
      barWidth: 26,
      data: PERIODS.map(period => {
        const value = periodBase.filter(w => w.period === period).length
        const active = selectedWorkPeriod.value === period
        return {
          value,
          itemStyle: {
            color: active ? '#e8c96d' : PERIOD_COLOR[period],
            shadowBlur: active ? 14 : 4,
            shadowColor: PERIOD_COLOR[period],
          },
        }
      }),
      label: { show: true, position: 'top', color: '#e6d5b8', fontSize: 11 },
    }],
  })

  const typeBase = selectedWorkPeriod.value === 'all'
    ? works
    : works.filter(w => w.period === selectedWorkPeriod.value)

  worksTypeChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', ...TOOLTIP_STYLE },
    series: [{
      type: 'pie',
      radius: ['34%', '72%'],
      center: ['50%', '50%'],
      roseType: 'radius',
      data: TYPES.map(type => ({
        name: type,
        value: typeBase.filter(w => w.primaryType === type).length,
        itemStyle: {
          color: selectedWorkType.value === type ? '#e8c96d' : TYPE_COLOR[type],
        },
      })),
      label: {
        color: '#c9a84c',
        fontSize: 12,
        fontFamily: 'Noto Serif SC',
      },
      labelLine: { lineStyle: { color: '#c9a84c44' } },
    }],
  })

  const points = workTimelinePoints.value
  const years = points.map(item => item.anchorYear)
  const minYear = years.length ? Math.min(...years) - WORK_TIMELINE_BUCKET_YEAR : -500
  const maxYear = years.length ? Math.max(...years) + WORK_TIMELINE_BUCKET_YEAR : 1900
  const maxCount = points.length ? Math.max(...points.map(item => item.count)) : 1
  const axisRange = Math.max(1, maxYear - minYear)
  const axisInterval = axisRange > 2200 ? 300 : axisRange > 1400 ? 200 : 150
  const typeOrder = ['皇宫', '官府', '民居', '桥梁']
  const withWeiJinTangDetails = selectedWorkPeriod.value === '魏晋隋唐'
  const dynastyMap = new Map()
  filteredWorks.value.forEach(work => {
    const year = extractApproxYear(work)
    if (!Number.isFinite(year)) return
    const dynasty = normalizeDynastyLabel(work.dynasty, withWeiJinTangDetails)
    const current = dynastyMap.get(dynasty) || { name: dynasty, min: year, max: year, count: 0 }
    current.min = Math.min(current.min, year)
    current.max = Math.max(current.max, year)
    current.count += 1
    dynastyMap.set(dynasty, current)
  })
  const dynastyBands = [...dynastyMap.values()]
    .sort((a, b) => a.min - b.min)
    .map((item, idx, arr) => {
      const prevMax = idx > 0 ? arr[idx - 1].max : item.min
      const nextMin = idx < arr.length - 1 ? arr[idx + 1].min : item.max
      const halfGapLeft = idx > 0 ? Math.max(6, Math.min(42, (item.min - prevMax) * 0.35)) : 10
      const halfGapRight = idx < arr.length - 1 ? Math.max(6, Math.min(42, (nextMin - item.max) * 0.35)) : 10
      return {
        name: item.name,
        start: Math.max(minYear, Math.floor(item.min - halfGapLeft)),
        end: Math.min(maxYear, Math.ceil(item.max + halfGapRight)),
        count: item.count,
      }
    })
    .filter(item => item.end > item.start)
    .filter(item => item.name !== '先秦两汉' && item.name !== '两汉')
    .map(item => {
      if (item.name !== '先秦') return item
      const shift = 34
      return {
        ...item,
        start: Math.min(maxYear, item.start + shift),
        end: Math.min(maxYear, item.end + shift),
      }
    })

  worksTimelineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...TOOLTIP_STYLE,
      formatter: params => {
        const item = params.data || {}
        if (!item.type) return ''
        const start = item.bucket
        const end = item.bucket + WORK_TIMELINE_BUCKET_YEAR - 1
        return `${item.type}<br/>时间段：${start} - ${end}<br/>著作数量：${item.count}`
      },
    },
      grid: { left: 50, right: 18, top: 38, bottom: 30 },
    xAxis: {
      type: 'value',
      min: minYear,
      max: maxYear,
      interval: axisInterval,
      axisLabel: {
        color: '#9f988c',
        fontSize: 12,
        fontFamily: 'Noto Serif SC',
        formatter: value => (value < 0 ? `前${Math.abs(value)}` : `${value}`),
      },
      splitLine: {
        show: false,
      },
      axisLine: { lineStyle: { color: '#c9a84c44' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category',
      data: typeOrder,
      inverse: true,
      axisLabel: {
        color: '#c9a84c',
        fontSize: 14,
        fontFamily: 'Noto Serif SC',
      },
      axisLine: { lineStyle: { color: '#c9a84c44' } },
      axisTick: { show: false },
    },
    series: [{
      type: 'scatter',
      data: points.map(item => ({
        value: [item.anchorYear, item.type],
        type: item.type,
        bucket: item.bucket,
        count: item.count,
        anchorYear: item.anchorYear,
        symbolSize: 6 + Math.sqrt(item.count / maxCount) * 14,
        symbolOffset: [
          Math.round(stableUnitHash(`${item.type}-${item.bucket}-x`) * 8),
          Math.round(stableUnitHash(`${item.type}-${item.bucket}-y`) * 5),
        ],
        itemStyle: {
          color: TYPE_COLOR[item.type] || '#c9a84c',
          opacity: 0.82,
          shadowBlur: 10,
          shadowColor: TYPE_COLOR[item.type] || '#c9a84c',
        },
      })),
      emphasis: {
        scale: 1.18,
      },
      markArea: {
        silent: true,
        itemStyle: {
          color: 'rgba(0,0,0,0)',
          borderColor: 'rgba(0,0,0,0)',
          borderWidth: 0,
        },
        label: {
          show: true,
          position: 'top',
          color: '#8b8680',
          fontSize: withWeiJinTangDetails ? 14 : 16,
          fontFamily: 'Noto Serif SC',
          distance: 8,
        },
        data: dynastyBands.map(item => [
          {
            name: item.name,
            xAxis: item.start,
            itemStyle: {
              color: 'rgba(0,0,0,0)',
              borderColor: 'rgba(0,0,0,0)',
              borderWidth: 0,
            },
          },
          {
            xAxis: item.end,
            itemStyle: {
              color: 'rgba(0,0,0,0)',
              borderColor: 'rgba(0,0,0,0)',
              borderWidth: 0,
            },
          },
        ]),
      },
    }],
  })
}

function initCraftCharts() {
  if (lineageChart && lineageChart.getDom() !== lineageRef.value) {
    lineageChart.dispose()
    lineageChart = null
  }
  if (lineageRef.value && !lineageChart) {
    lineageChart = echarts.init(lineageRef.value, null, { renderer: 'svg' })
    lineageChart.on('click', params => {
      if (params.dataType !== 'node' || !params.data?.id) return
      focusCraftInCurrentFilter(params.data.id)
    })
  }

  if (sankeyChart && sankeyChart.getDom() !== sankeyRef.value) {
    sankeyChart.dispose()
    sankeyChart = null
  }
  if (sankeyRef.value && !sankeyChart) {
    sankeyChart = echarts.init(sankeyRef.value, null, { renderer: 'svg' })
    sankeyChart.on('click', params => {
      if (params.dataType !== 'node') return
      handleSankeyNodeClick(params.data)
    })
  }

  renderLineageChart()
  renderSankeyChart()
}

function renderLineageChart() {
  if (!lineageChart) return

  const edges = activeLineageEdges.value.map(edge => {
    const relationKey = edge.relationType
    const relationLabel = lineageRelationTypes[relationKey] || relationKey
    const sourceName = craftMap.value[edge.source]?.name || edge.source
    const targetName = craftMap.value[edge.target]?.name || edge.target
    return {
      source: edge.source,
      target: edge.target,
      relationType: relationKey,
      lineStyle: {
        color: RELATION_COLOR[relationKey] || '#c9a84c',
        width: 1.9,
        type: 'solid',
        opacity: 0.9,
      },
      label: {
        show: false,
      },
      tooltip: {
        formatter: `${relationLabel}：${sourceName} → ${targetName}`,
      },
    }
  })
  const edgeRelationTypes = new Set(edges.map(item => item.relationType))
  const relationLegendGraphic = RELATION_ORDER.filter(type => edgeRelationTypes.has(type)).flatMap((type, idx) => {
    const y = 8 + idx * 18
    return [
      {
        type: 'line',
        right: 102,
        top: y + 7,
        shape: { x1: 0, y1: 0, x2: 16, y2: 0 },
        style: {
          stroke: RELATION_COLOR[type] || '#c9a84c',
          lineWidth: 2.6,
          opacity: 0.95,
        },
      },
      {
        type: 'text',
        right: 42,
        top: y,
        style: {
          text: lineageRelationTypes[type] || type,
          fill: '#9f988c',
          fontSize: 12,
          fontFamily: 'Noto Serif SC',
        },
      },
    ]
  })

  lineageChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...TOOLTIP_STYLE,
      formatter: params => {
        if (params.dataType === 'edge') return params.data.tooltip.formatter
        const craft = craftMap.value[params.data.id]
        if (!craft) return params.name
        return `${craft.name}<br/>${craft.period} · ${craft.primaryType}`
      },
    },
    legend: {
      top: 0,
      textStyle: { color: '#8b8680', fontSize: 12, fontFamily: 'Noto Serif SC' },
      itemWidth: 10,
      itemHeight: 10,
      data: TYPES,
    },
    graphic: relationLegendGraphic,
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      top: 20,
      force: {
        repulsion: 145,
        gravity: 0.06,
        edgeLength: [68, 112],
      },
      data: lineageNodes.value,
      links: edges,
      categories: TYPES.map(type => ({ name: type })),
      label: {
        show: true,
        position: 'right',
        formatter: '{b}',
        fontSize: 13,
        fontFamily: 'Noto Serif SC',
      },
      lineStyle: {
        curveness: 0.16,
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 2.2 },
      },
    }],
  })
}

function renderSankeyChart() {
  if (!sankeyChart) return

  const { nodes, links, meta } = sankeyGraph.value
  const nodeNameMap = meta?.nodeNameMap || {}
  const isAllMode = Boolean(meta?.isAllMode)
  const maxColumnNodes = Math.max(meta?.schoolNodeCount || 0, meta?.workNodeCount || 0, TYPES.length)
  const nodeGap = maxColumnNodes > 16 ? 10 : maxColumnNodes > 12 ? 14 : 20
  const labelFontSize = maxColumnNodes > 16 ? 14 : maxColumnNodes > 12 ? 16 : 18
  const leftLabelFontSize = isAllMode ? labelFontSize + 1 : labelFontSize + 1
  const leftLabelWidth = isAllMode ? 182 : 156
  const sankeyNodeWidth = isAllMode ? 18 : 16

  sankeyChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...TOOLTIP_STYLE,
      formatter: params => {
        if (params.dataType === 'edge') {
          const sourceName = nodeNameMap[params.data.source] || params.data.sourceName || params.data.source
          const targetName = nodeNameMap[params.data.target] || params.data.targetName || params.data.target
          return `${sourceName} → ${targetName}`
        }
        const node = params.data || {}
        const labels = {
          school: '流派/工种',
          work: '代表著作',
          type: '建筑类型',
        }
        return `${labels[node.nodeKind] || '节点'}：${node.displayName || params.name}`
      },
    },
    series: [{
      type: 'sankey',
      top: 28,
      left: 112,
      right: 112,
      bottom: 28,
      data: nodes,
      links,
      nodeWidth: sankeyNodeWidth,
      nodeGap,
      draggable: true,
      layoutIterations: 0,
      nodeSort: 'none',
      nodeAlign: 'justify',
      lineStyle: {
        color: 'source',
        curveness: 0.46,
        opacity: 0.38,
      },
      label: {
        formatter: params => params.data.displayName || params.name,
        color: '#e6d5b8',
        fontSize: labelFontSize,
        fontFamily: 'Noto Serif SC',
      },
      levels: [
        {
          depth: 0,
          label: {
            position: 'right',
            width: leftLabelWidth,
            align: 'left',
            verticalAlign: 'middle',
            overflow: 'truncate',
            fontSize: leftLabelFontSize,
            color: '#d8e7ff',
            fontFamily: 'Noto Serif SC',
          },
        },
        {
          depth: 1,
          label: {
            position: 'right',
            width: 224,
            align: 'left',
            verticalAlign: 'middle',
            overflow: 'truncate',
            fontSize: labelFontSize,
            fontFamily: 'Noto Serif SC',
          },
        },
        {
          depth: 2,
          label: {
            position: 'left',
            width: 102,
            align: 'right',
            verticalAlign: 'middle',
            overflow: 'truncate',
            fontSize: labelFontSize,
            fontFamily: 'Noto Serif SC',
          },
        },
      ],
      emphasis: {
        focus: 'adjacency',
      },
    }],
    graphic: links.length
      ? []
      : [{
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '当前筛选下暂无可用链路',
          fill: '#8b8680',
          fontSize: 12,
          fontFamily: 'Noto Serif SC',
        },
      }],
  }, true)
}

function handleResize() {
  worksPeriodChart?.resize()
  worksTypeChart?.resize()
  worksTimelineChart?.resize()
  lineageChart?.resize()
  sankeyChart?.resize()
}

async function ensureWorksDashboard() {
  await nextTick()
  initWorksCharts()
  renderWorksCharts()
  worksPeriodChart?.resize()
  worksTypeChart?.resize()
  worksTimelineChart?.resize()
}

async function ensureCraftDashboard() {
  await nextTick()
  initCraftCharts()
  renderLineageChart()
  renderSankeyChart()
  lineageChart?.resize()
  sankeyChart?.resize()
}

watch([selectedWorkPeriod, selectedWorkType], async () => {
  worksPage.value = 1
  if (activeTab.value === 'works') {
    await ensureWorksDashboard()
  }
}, { flush: 'post' })

watch([selectedCraftPeriod, selectedCraftType, selectedCraftSchool], async () => {
  craftsPage.value = 1
  if (activeTab.value === 'craftsmen') {
    await ensureCraftDashboard()
  }
}, { flush: 'post' })

watch(selectedSankeyBuildingType, async () => {
  if (activeTab.value !== 'craftsmen') return
  await nextTick()
  renderSankeyChart()
  sankeyChart?.resize()
}, { flush: 'post' })

watch(filteredWorks, list => {
  if (worksPage.value > worksTotalPages.value) worksPage.value = worksTotalPages.value
  if (selectedWorkId.value && !list.some(item => item.id === selectedWorkId.value)) {
    closeDetailDrawer()
  }
})

watch(visibleLineageCraftsmen, list => {
  if (craftsPage.value > craftsTotalPages.value) craftsPage.value = craftsTotalPages.value
  if (focusedCraftId.value && !filteredCraftsmen.value.some(item => item.id === focusedCraftId.value)) {
    focusedCraftId.value = null
  }
  if (selectedCraftId.value && !filteredCraftsmen.value.some(item => item.id === selectedCraftId.value)) {
    closeDetailDrawer()
  }
})

watch(activeTab, async tab => {
  if (tab === 'works') {
    await ensureWorksDashboard()
  } else {
    await ensureCraftDashboard()
  }
  handleResize()
}, { flush: 'post' })

watch(
  () => route.path,
  path => {
    const tab = resolveTabByPath(path)
    if (activeTab.value !== tab) {
      activeTab.value = tab
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (activeTab.value === 'craftsmen') {
    await ensureCraftDashboard()
  } else {
    await ensureWorksDashboard()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  worksPeriodChart?.dispose()
  worksTypeChart?.dispose()
  worksTimelineChart?.dispose()
  lineageChart?.dispose()
  sankeyChart?.dispose()
  worksPeriodChart = null
  worksTypeChart = null
  worksTimelineChart = null
  lineageChart = null
  sankeyChart = null
})
</script>

<template>
  <div class="heritage-page">
    <nav class="top-nav">
      <span class="nav-title text-glow-gold">匠心千年</span>
      <div class="nav-links">
        <router-link to="/explore">建筑地图</router-link>
        <router-link to="/works">文化著作</router-link>
        <router-link to="/lineage">科学家谱系</router-link>
      </div>
    </nav>

    <div class="stats-bar">
      <div class="stat-item">
        <div class="stat-num text-glow-gold">{{ works.length }}</div>
        <div class="stat-label">著作总量</div>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <div class="stat-num text-glow-gold">{{ craftsmen.length }}</div>
        <div class="stat-label">工匠总量</div>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <div class="stat-num text-glow-gold">{{ activeLineageEdges.length }}</div>
        <div class="stat-label">谱系关系边</div>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <div class="stat-num text-glow-gold">{{ totalSourceRefs }}</div>
        <div class="stat-label">来源编号数</div>
      </div>
    </div>

    <div class="divider-gold" />

    <div class="content-area" v-if="activeTab === 'works'">
      <div class="dashboard-column">
        <div class="panel-title">著作分布与类型结构</div>
        <div class="filter-row">
          <span class="filter-chip">时期：{{ selectedWorkPeriod === 'all' ? '全部' : selectedWorkPeriod }}</span>
          <span class="filter-chip">类型：{{ selectedWorkType === 'all' ? '全部' : selectedWorkType }}</span>
          <button class="ghost-btn" @click="clearWorksFilter">清空筛选</button>
        </div>
        <div class="chart-card">
          <div class="chart-title">朝代分布（点击柱体筛选）</div>
          <div ref="worksPeriodRef" class="chart-box" />
        </div>
        <div class="chart-card">
          <div class="chart-title">类型结构（点击扇区筛选）</div>
          <div ref="worksTypeRef" class="chart-box" />
        </div>
      </div>

      <div class="list-column works-list-column">
        <div class="list-head">著作列表 · {{ filteredWorks.length }} 条</div>
        <div class="list-scroll works-list-grid">
          <div
            v-for="w in pagedWorks"
            :key="w.id"
            class="card-ancient work-card"
            :class="{ active: selectedWorkId === w.id }"
            @click="openWorkCard(w.id)"
          >
            <div class="work-title">{{ w.title }}</div>
            <div class="work-meta">{{ w.author }} · {{ w.dynasty }} · {{ w.year }} · {{ w.primaryType }}</div>
            <div class="work-summary">{{ w.summary }}</div>
            <div class="work-tags">
              <span v-for="t in w.buildingTypes" :key="t" :class="`tag tag-${t}`">{{ t }}</span>
              <span v-for="k in (w.keywords || []).slice(0, 3)" :key="k" class="keyword-tag">{{ k }}</span>
            </div>
            <div class="quick-row">
              <button
                class="chip"
                v-for="p in resolveCrafts(w.relatedCraftsmen).slice(0, 2)"
                :key="p.id"
                @click.stop="openCraftContext(p.id)"
              >
                {{ p.name }}
              </button>
              <button
                class="chip"
                v-for="b in resolveBuildings(w.relatedBuildings).slice(0, 1)"
                :key="b.id"
                @click.stop="jumpToBuilding(b.id)"
              >
                {{ b.name }}
              </button>
            </div>
          </div>
        </div>
        <div class="pager-row">
          <button class="ghost-btn" :disabled="worksPage <= 1" @click="prevWorksPage">上一页</button>
          <span class="pager-text">{{ worksPage }} / {{ worksTotalPages }}</span>
          <button class="ghost-btn" :disabled="worksPage >= worksTotalPages" @click="nextWorksPage">下一页</button>
        </div>
        <div class="chart-card works-timeline-card">
          <div class="chart-title">文化著作数量分布时间轴</div>
          <div ref="worksTimelineRef" class="chart-box works-timeline-box" />
        </div>
      </div>
    </div>

    <div class="content-area crafts-layout" v-else>
      <div class="dashboard-column crafts-main-column">
        <div class="panel-title">科学家谱系与分布</div>
        <div class="filter-row">
          <span class="filter-chip">时期：{{ selectedCraftPeriod === 'all' ? '全部' : selectedCraftPeriod }}</span>
          <span class="filter-chip">类型：{{ selectedCraftType === 'all' ? '全部' : selectedCraftType }}</span>
          <span class="filter-chip">流派：{{ selectedCraftSchool === 'all' ? '全部' : selectedCraftSchool }}</span>
          <button class="ghost-btn" @click="clearCraftFilter">清空筛选</button>
        </div>

        <div class="chart-card lineage-card">
          <div class="chart-title">关系图谱（按关系分色，节点与卡片双向高亮）</div>
          <div ref="lineageRef" class="lineage-box" />
        </div>
      </div>

      <div class="list-column crafts-side-column">
        <div class="list-head">谱系列表 · {{ visibleLineageCraftsmen.length }} 人</div>
        <div class="grid-scroll">
          <div
            v-for="c in pagedCraftsmen"
            :key="c.id"
            class="card-ancient crafts-card"
            :class="{ focused: focusedCraftId === c.id, active: selectedCraftId === c.id }"
            @click="openCraftCard(c.id)"
          >
            <div class="craft-name">{{ c.name }}</div>
            <div class="craft-meta">{{ c.dynasty }} · {{ c.title }}</div>
            <div class="craft-meta craft-sub">{{ c.hometown }} · {{ c.primaryType }}</div>
            <div class="craft-brief">{{ c.achievement }}</div>
            <div class="craft-tags">
              <span v-for="t in c.buildingTypes" :key="t" :class="`tag tag-${t}`">{{ t }}</span>
              <span v-for="s in (c.schoolTags || []).slice(0, 2)" :key="s" class="keyword-tag">{{ s }}</span>
            </div>
          </div>
        </div>
        <div class="pager-row">
          <button class="ghost-btn" :disabled="craftsPage <= 1" @click="prevCraftsPage">上一页</button>
          <span class="pager-text">{{ craftsPage }} / {{ craftsTotalPages }}</span>
          <button class="ghost-btn" :disabled="craftsPage >= craftsTotalPages" @click="nextCraftsPage">下一页</button>
        </div>
      </div>

      <div class="chart-card sankey-wide-card">
        <div class="chart-title-row">
          <div class="chart-title">流派/工种 -> 代表著作 -> 建筑类型</div>
          <div class="viz-switch">
            <button
              v-for="type in SANKEY_BUILDING_TYPES"
              :key="type"
              :class="['switch-btn', { active: selectedSankeyBuildingType === type }]"
              @click="selectedSankeyBuildingType = type"
            >
              {{ type === 'all' ? '全部类型' : type }}
            </button>
          </div>
        </div>
        <div ref="sankeyRef" class="chart-box sankey-wide-box" />
      </div>
    </div>

    <DetailDrawer
      :visible="detailDrawer.visible"
      :payload="drawerPayload"
      @close="closeDetailDrawer"
      @open-work="handleDrawerOpenWork"
      @open-craft="handleDrawerOpenCraft"
      @open-building="handleDrawerOpenBuilding"
    />
  </div>
</template>

<style scoped>
.heritage-page {
  min-height: 100vh;
  background: var(--color-ink);
  display: flex;
  flex-direction: column;
}

.top-nav {
  height: 60px;
  padding: 0 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #c9a84c55;
  flex-shrink: 0;
  background: rgba(10,14,26,0.98);
  box-shadow: 0 2px 24px rgba(201,168,76,0.08);
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
  gap: 40px;
  margin-left: 0;
  margin-right: 0;
}

.nav-links a {
  color: #8b8680;
  text-decoration: none;
  font-size: 16px;
  font-weight: 500;
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

.stats-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 20px 28px;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
}

.stat-num {
  font-size: 28px;
  color: var(--color-gold-light);
  font-weight: 700;
}

.stat-label {
  font-size: 11px;
  color: var(--color-text-dim);
  letter-spacing: 0.08em;
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 30px;
  background: var(--color-gold-dim);
}

.tab-bar {
  display: flex;
  gap: 0;
  padding: 14px 32px 0;
}

.tab-btn {
  padding: 9px 34px;
  background: transparent;
  border: 1px solid var(--color-gold-dim);
  color: var(--color-text-dim);
  font-family: 'Noto Serif SC', serif;
  font-size: 14px;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.25s;
}

.tab-btn.active {
  background: rgba(201, 168, 76, 0.12);
  border-color: var(--color-gold);
  color: var(--color-gold-light);
}

.content-area {
  flex: 1;
  padding: 20px 32px 28px;
  display: grid;
  grid-template-columns: minmax(320px, 42%) minmax(0, 58%);
  gap: 20px;
  min-height: 0;
}

.crafts-layout {
  --craft-list-offset: 54px;
  --lineage-panel-height: 424px;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 340px);
  grid-template-rows: minmax(0, 1fr) auto;
  align-items: start;
}

.dashboard-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.panel-title {
  font-size: 15px;
  color: var(--color-gold-light);
  letter-spacing: 0.12em;
}

.filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-chip {
  border: 1px solid var(--color-gold-dim);
  color: var(--color-text-dim);
  padding: 2px 8px;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.ghost-btn {
  background: transparent;
  color: var(--color-gold);
  border: 1px solid var(--color-gold-dim);
  font-size: 11px;
  padding: 2px 10px;
  cursor: pointer;
}

.ghost-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.chart-card {
  background: rgba(15, 20, 28, 0.9);
  border: 1px solid var(--color-gold-dim);
  padding: 10px;
}

.chart-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.viz-switch {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  border: 1px solid var(--color-gold-dim);
  max-width: 100%;
}

.switch-btn {
  border: 0;
  background: transparent;
  color: var(--color-text-dim);
  font-size: 11px;
  padding: 3px 10px;
  cursor: pointer;
}

.switch-btn + .switch-btn {
  border-left: 1px solid var(--color-gold-dim);
}

.switch-btn.active {
  color: var(--color-gold-light);
  background: rgba(201, 168, 76, 0.12);
}

.chart-title {
  color: #c9a84c;
  font-size: 12px;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}

.chart-box {
  width: 100%;
  height: 224px;
}

.lineage-card {
  min-height: var(--lineage-panel-height);
}

.lineage-box {
  width: 100%;
  height: calc(var(--lineage-panel-height) - 44px);
}

.crafts-side-column {
  margin-top: var(--craft-list-offset);
  min-height: var(--lineage-panel-height);
  max-height: var(--lineage-panel-height);
}

.crafts-side-column .grid-scroll {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 10px;
  max-height: none;
}

.crafts-side-column .crafts-card {
  width: 100%;
  min-height: 148px;
  padding: 10px;
  overflow: hidden;
}

.crafts-side-column .craft-brief {
  -webkit-line-clamp: 1;
  min-height: 1.7em;
}

.crafts-side-column .quick-row .chip {
  white-space: normal;
  line-height: 1.35;
}

.sankey-wide-card {
  grid-column: 1 / -1;
}

.sankey-wide-box {
  height: 520px;
}

.list-column {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.works-list-column {
  width: 100%;
  justify-self: start;
  align-self: start;
}

.works-timeline-card {
  margin-top: 4px;
}

.works-timeline-box {
  height: 250px;
}

.list-head {
  font-size: 13px;
  color: var(--color-gold);
  letter-spacing: 0.12em;
  margin-bottom: 8px;
}

.list-scroll,
.grid-scroll {
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.list-scroll {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.works-list-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  overflow-y: visible;
  padding-right: 0;
}

.works-list-column .work-card {
  min-height: 176px;
}

.grid-scroll {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
  align-content: start;
  align-items: start;
}

.pager-row {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.pager-text {
  font-size: 12px;
  color: var(--color-text-dim);
  min-width: 54px;
  text-align: center;
}

.work-card,
.crafts-card {
  padding: 12px;
  cursor: pointer;
}

.crafts-card {
  align-self: start;
  display: flex;
  flex-direction: column;
  min-height: 192px;
}

.work-card.active,
.crafts-card.active,
.crafts-card.focused {
  border-color: var(--color-gold);
  box-shadow: 0 0 20px rgba(201, 168, 76, 0.15);
}

.work-title,
.craft-name {
  font-size: 17px;
  color: var(--color-gold-light);
  line-height: 1.4;
  font-family: 'Noto Serif SC', serif;
}

.work-meta,
.craft-meta {
  color: var(--color-text-dim);
  font-size: 12px;
  margin-top: 4px;
}

.craft-sub {
  opacity: 0.85;
}

.work-summary,
.craft-brief {
  margin-top: 8px;
  color: var(--color-text);
  font-size: 13px;
  line-height: 1.7;
  min-height: calc(1.7em * 2);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.work-tags,
.craft-tags {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.keyword-tag {
  border: 1px solid #2a4250;
  color: #8cc5d9;
  background: rgba(0, 212, 255, 0.08);
  padding: 2px 6px;
  font-size: 11px;
}

.quick-row {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  border: 1px solid var(--color-gold-dim);
  background: rgba(201, 168, 76, 0.08);
  color: var(--color-text);
  font-size: 11px;
  padding: 3px 8px;
  cursor: pointer;
}

@media (max-width: 1100px) {
  .content-area {
    grid-template-columns: 1fr;
  }

  .lineage-box {
    height: 300px;
  }

  .lineage-card {
    min-height: 344px;
  }

  .chart-box,
  .sankey-wide-box {
    height: 260px;
  }

  .chart-title-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .works-list-grid {
    grid-template-columns: 1fr;
  }

  .crafts-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    --craft-list-offset: 0px;
  }

  .crafts-side-column,
  .crafts-side-column .grid-scroll {
    min-height: 0;
    max-height: none;
  }
}
</style>
