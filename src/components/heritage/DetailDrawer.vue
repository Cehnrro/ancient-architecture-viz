<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  payload: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'open-work', 'open-craft', 'open-building'])

const groups = computed(() => props.payload?.groups || [])
const infoRows = computed(() => props.payload?.infoRows || [])
const tags = computed(() => props.payload?.tags || [])
const keywords = computed(() => props.payload?.keywords || [])

function handleChip(item) {
  if (!item || !item.id) return
  if (item.clickable === false) return
  if (item.kind === 'work') emit('open-work', item.id)
  if (item.kind === 'craft') emit('open-craft', item.id)
  if (item.kind === 'building') emit('open-building', item.id)
}
</script>

<template>
  <teleport to="body">
    <div v-if="visible && payload" class="drawer-mask" @click.self="emit('close')">
      <aside class="drawer-panel card-ancient">
        <header class="drawer-header">
          <div>
            <div class="drawer-type">{{ payload.typeLabel }}</div>
            <div class="drawer-title">{{ payload.title }}</div>
          </div>
          <button class="drawer-close" @click="emit('close')">关闭</button>
        </header>

        <div class="drawer-scroll">
          <section class="drawer-section">
            <div class="section-title">基础信息</div>
            <div class="info-grid">
              <div
                v-for="(item, idx) in infoRows"
                :key="item.label"
                class="info-item"
                :class="{ 'info-item-full': infoRows.length % 2 === 1 && idx === infoRows.length - 1 }"
              >
                <div class="info-label">{{ item.label }}</div>
                <div class="info-value">{{ item.value || '—' }}</div>
              </div>
            </div>
            <div class="drawer-body" v-if="payload.description">{{ payload.description }}</div>
          </section>

          <section class="drawer-section" v-if="tags.length || keywords.length">
            <div class="section-title">关键词与类型</div>
            <div class="tag-row" v-if="tags.length">
              <span v-for="tag in tags" :key="tag" :class="`tag tag-${tag}`">{{ tag }}</span>
            </div>
            <div class="tag-row" v-if="keywords.length">
              <span v-for="kw in keywords" :key="kw" class="keyword-tag">{{ kw }}</span>
            </div>
          </section>

          <section class="drawer-section" v-if="groups.length">
            <div class="section-title">关联实体</div>
            <div class="group-list">
              <div class="group-block" v-for="group in groups" :key="group.title" v-show="group.items.length">
                <div class="group-title">{{ group.title }}</div>
                <div class="chips">
                  <button
                    class="chip"
                    :class="{ 'chip-static': item.clickable === false }"
                    v-for="item in group.items"
                    :key="item.id"
                    @click="handleChip(item)"
                  >
                    <span>{{ item.label }}</span>
                    <span v-if="item.chipMeta?.relationType" class="chip-meta">{{ item.chipMeta.relationType }}</span>
                    <span v-if="item.chipMeta?.isCrossPeriod" class="chip-cross">跨期</span>
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </aside>
    </div>
  </teleport>
</template>

<style scoped>
.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.34);
  z-index: 80;
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
}

.drawer-panel {
  width: min(540px, 100vw);
  height: min(92vh, 980px);
  margin-top: max(18px, 4vh);
  border-radius: 0;
  border-right: 0;
  background: #111823;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.32);
}

.drawer-header {
  padding: 20px 20px 14px;
  border-bottom: 1px solid var(--color-gold-dim);
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.drawer-type {
  font-size: 13px;
  letter-spacing: 0.12em;
  color: #8b8680;
}

.drawer-title {
  margin-top: 6px;
  color: var(--color-gold-light);
  font-size: 30px;
  line-height: 1.35;
}

.drawer-close {
  align-self: flex-start;
  background: transparent;
  border: 1px solid var(--color-gold-dim);
  color: var(--color-gold);
  font-size: 14px;
  padding: 6px 12px;
  cursor: pointer;
}

.drawer-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.drawer-section {
  border: 1px solid var(--color-gold-dim);
  background: rgba(201, 168, 76, 0.04);
  padding: 12px;
}

.section-title {
  font-size: 15px;
  color: var(--color-gold);
  letter-spacing: 0.08em;
  margin-bottom: 10px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.info-item {
  border: 1px solid #7a603044;
  padding: 9px 10px;
  background: rgba(13, 17, 23, 0.4);
}

.info-item-full {
  grid-column: 1 / -1;
}

.info-label {
  color: #8b8680;
  font-size: 13px;
}

.info-value {
  margin-top: 5px;
  color: var(--color-text);
  font-size: 22px;
  line-height: 1.25;
  font-weight: 500;
}

.drawer-body {
  margin-top: 12px;
  color: var(--color-text);
  line-height: 1.75;
  font-size: 16px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-row + .tag-row {
  margin-top: 8px;
}

.keyword-tag {
  border: 1px solid #2a4250;
  color: #8cc5d9;
  background: rgba(0, 212, 255, 0.08);
  padding: 4px 9px;
  font-size: 13px;
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-title {
  color: var(--color-gold);
  font-size: 14px;
  margin-bottom: 7px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  border: 1px solid var(--color-gold-dim);
  background: rgba(201, 168, 76, 0.08);
  color: var(--color-text);
  font-size: 13px;
  padding: 5px 10px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.chip-static {
  cursor: default;
}

.chip-meta {
  border: 1px solid #2a4250;
  background: rgba(0, 212, 255, 0.08);
  color: #8cc5d9;
  font-size: 11px;
  padding: 1px 4px;
}

.chip-cross {
  border: 1px solid rgba(201, 168, 76, 0.6);
  color: var(--color-gold-light);
  font-size: 11px;
  padding: 1px 4px;
}

@media (max-width: 1100px) {
  .drawer-mask {
    justify-content: center;
    align-items: flex-end;
  }

  .drawer-panel {
    width: 100vw;
    height: min(76vh, 640px);
    border: 1px solid var(--color-gold-dim);
    border-radius: 12px 12px 0 0;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
