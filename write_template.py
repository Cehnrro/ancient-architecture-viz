
template_part = """
<template>
  <div class="explore-page">
    <nav class="top-nav">
      <span class="nav-title text-glow-gold">\u5320\u5fc3\u5343\u5e74</span>
      <div class="nav-links">
        <router-link to="/explore">\u5efa\u7b51\u5730\u56fe</router-link>
        <router-link to="/works">\u6587\u5316\u8457\u4f5c</router-link>
        <router-link to="/lineage">\u79d1\u5b66\u5bb6\u8c31\u7cfb</router-link>
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
          <div class="cc-label">\u5efa\u7b51\u6700\u5bc6\u96c6\u7701\u4efd</div>
          <div class="cc-province">{{ topProvince.province }}</div>
          <div class="cc-count">\u5171 {{ topProvince.count }} \u5ea7\u53e4\u5efa\u7b51</div>
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
              {{ activePeriodInfo ? activePeriodInfo.name : '\u4e2d\u534e\u4e0a\u4e0b\u4e94\u5343\u5e74' }}
            </div>
            <div class="period-sub" v-if="activePeriodInfo">
              {{ activePeriodInfo.label }} \u00b7 {{ activePeriodInfo.range }}
            </div>
            <div class="building-count">\u5171 {{ filteredBuildings.length }} \u5904\u53e4\u5efa\u7b51</div>
          </div>

          <button
            v-if="activePeriod === 'all'"
            class="overview-btn"
            :class="{ active: showOverview }"
            @click="showOverview = !showOverview"
          >{{ showOverview ? '\u6536\u8d77\u603b\u89c8' : '\u6570\u636e\u603b\u89c8' }}</button>

          <template v-if="showOverview && activePeriod === 'all'">
            <div class="overview-section">
              <div class="overview-title">\u5404\u671d\u4ee3\u5efa\u7b51\u6570\u91cf</div>
              <div ref="barRef" class="overview-chart" />
            </div>
            <div class="overview-section">
              <div class="overview-title">\u5efa\u7b51\u6700\u5bc6\u96c6\u7701\u4efd\uff08\u524d15\uff09</div>
              <div ref="bubbleRef" class="overview-chart overview-chart-tall" />
            </div>
            <div class="overview-section">
              <div class="overview-title">\u5404\u671d\u4ee3\u5efa\u7b51\u7c7b\u578b\u5206\u5e03</div>
              <div ref="stackRef" class="overview-chart-stack" />
            </div>
            <div class="overview-section">
              <div class="overview-title">\u5404\u671d\u4ee3\u5efa\u7b51\u4fdd\u5b58\u72b6\u51b5</div>
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
                <span class="type-toggle-hint">{{ hiddenTypes.has(type) ? '\u663e\u793a' : '\u9690\u85cf' }}</span>
              </div>
            </div>
            <div class="pie-wrap">
              <div class="pie-title">\u7740\u4f5c\u5206\u5e03\u4e0e\u7c7b\u578b\u7ed3\u6784</div>
              <div ref="pieChart" class="pie-chart" />
            </div>
            <div class="divider-gold my-4" />
            <div class="hint">\u70b9\u51fb\u5730\u56fe\u4e0a\u7684\u5efa\u7b51\u67e5\u770b\u8be6\u60c5</div>
          </template>
        </template>

        <template v-else>
          <button class="back-to-map" @click="selectedBuilding = null">\u2190 \u8fd4\u56de\u5730\u56fe</button>
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
                  <div class="desc-section-label"><span class="desc-label-icon">\u25c6</span>{{ key }}</div>
                  <div class="desc-section-body">{{ val }}</div>
                </div>
              </div>
            </template>
            <template v-else>
              <p class="bc-desc">{{ selectedBuilding.description }}</p>
            </template>
            <div class="bc-features" v-if="selectedBuilding.isFeatured && selectedBuilding.features?.length">
              <div class="bc-features-title">\u5efa\u7b51\u7279\u8272</div>
              <div v-for="f in selectedBuilding.features" :key="f" class="bc-feature-item">{{ f }}</div>
            </div>
            <button v-if="selectedBuilding.isFeatured" class="detail-btn" @click="goToDetail(selectedBuilding.id)">\u67e5\u770b\u8be6\u60c5 \u2192</button>
            <div class="same-province" v-if="sameProvinceBuildings.length">
              <div class="sp-title">\u540c\u7701\u5176\u4ed6\u5efa\u7b51</div>
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
        v-for="p in [{ id: 'all', name: '\u5168\u90e8' }, ...periods]"
        :key="p.id || p.name"
        class="period-btn"
        :class="{ active: activePeriod === (p.id === 'all' ? 'all' : p.name) }"
        @click="activePeriod = p.id === 'all' ? 'all' : p.name; selectedBuilding = null"
      >{{ p.name }}</button>
    </div>
  </div>
</template>
"""

with open(r'D:/jishe/ancient-architecture-viz/src/views/ExploreView_new.vue', 'a', encoding='utf-8') as f:
    f.write(template_part)

print('template appended')
