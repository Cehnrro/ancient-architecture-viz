with open(r'D:/jishe/ancient-architecture-viz/src/views/ExploreView.vue', 'r', encoding='utf-8') as f:
    lines = f.readlines()

script_end = next(i for i,l in enumerate(lines) if l.strip() == '</script>')
style_start = next(i for i,l in enumerate(lines) if l.strip() == '<style scoped>')

template = """
<template>
  <div class="explore-page">
    <nav class="top-nav">
      <span class="nav-title text-glow-gold" v-text="'\\u5320\\u5fc3\\u5343\\u5e74'" />
      <div class="nav-links">
        <router-link to="/explore" v-text="'\\u5efa\\u7b51\\u5730\\u56fe'" />
        <router-link to="/works" v-text="'\\u6587\\u5316\\u8457\\u4f5c'" />
        <router-link to="/lineage" v-text="'\\u79d1\\u5b66\\u5bb6\\u8c31\\u7cfb'" />
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
                v-for="type in ['皇宫','官府','民居','桥梁']"
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
              <div class="pie-title">著作分布与类型结构</div>
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
            <template v-if="!selectedBuilding.isFeatured">
              <template v-if="descSections">
                <div class="desc-sections">
                  <div v-for="(val, key) in descSections" :key="key" class="desc-section">
                    <div class="desc-section-label">
                      <span class="desc-label-icon">◆</span>{{ key }}
                    </div>
                    <div class="desc-section-body">{{ val }}</div>
                  </div>
                </div>
              </template>
              <template v-else>
                <p class="bc-desc">{{ selectedBuilding.description }}</p>
              </template>
            </template>
            <div class="bc-features" v-if="selectedBuilding.isFeatured && selectedBuilding.features?.length">
              <div class="bc-features-title">建筑特色</div>
              <ul>
                <li v-for="f in selectedBuilding.features" :key="f">{{ f }}</li>
              </ul>
            </div>
            <button
              v-if="selectedBuilding.isFeatured"
              class="detail-btn"
              @click="goToDetail(selectedBuilding.id)"
            >查看详情 →</button>
            <div class="same-province" v-if="sameProvinceBuildings.length">
              <div class="divider-gold my-4" />
              <div class="sp-title">{{ selectedBuilding.province }}的其他古建筑</div>
              <div
                v-for="b in sameProvinceBuildings"
                :key="b.name"
                class="sp-item"
                @click="selectedBuilding = b"
              >
                <span :class="`tag tag-${b.type} tag-sm`">{{ b.type }}</span>
                <span class="sp-name">{{ b.name }}</span>
                <span class="sp-dynasty" :class="b.period !== selectedBuilding.period ? 'sp-dynasty-other' : ''">
                  {{ b.dynasty }}
                  <span v-if="b.period !== selectedBuilding.period" class="sp-other-tag">{{ b.period }}</span>
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="timeline">
      <div
        v-for="p in periods"
        :key="p.id"
        class="timeline-item"
        :class="{ active: activePeriod === p.name }"
        @click="activePeriod = p.name; selectedBuilding = null"
      >
        <div class="period-name">{{ p.name }}</div>
        <div class="period-label-sub">{{ p.label }}</div>
      </div>
      <div
        class="timeline-item"
        :class="{ active: activePeriod === 'all' }"
        @click="activePeriod = 'all'; selectedBuilding = null"
      >
        <div class="period-name">总览</div>
      </div>
    </div>
  </div>
</template>
"""

new_lines = lines[:script_end+1] + [template + '\n'] + lines[style_start:]

with open(r'D:/jishe/ancient-architecture-viz/src/views/ExploreView.vue', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('done, total lines:', len(new_lines))
