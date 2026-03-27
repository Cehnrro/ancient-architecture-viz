<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'

const router = useRouter()

onMounted(() => {
  gsap.from('.intro-title', { opacity: 0, y: 40, duration: 1.2, ease: 'power3.out' })
  gsap.from('.intro-subtitle', { opacity: 0, y: 20, duration: 1, delay: 0.5, ease: 'power3.out' })
  gsap.fromTo('.intro-btn', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 1, delay: 1, ease: 'power3.out' })
})
</script>

<template>
  <div class="intro-page">
    <!-- 背景粒子层 -->
    <div class="bg-overlay" />

    <!-- 中央内容 -->
    <div class="center-content">
      <div class="intro-title text-glow-gold">匠心千年</div>
      <div class="intro-subtitle">中国古代建筑成就数据可视化</div>
      <div class="divider-gold my-8" />
      <button class="intro-btn" @click="router.push('/explore')">
        开始探索
      </button>
    </div>
  </div>
</template>

<style scoped>
.intro-page {
  width: 100vw;
  height: 100vh;
  background: var(--color-ink);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.bg-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(201,168,76,0.05) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 50%, rgba(0,212,255,0.05) 0%, transparent 60%);
}

.center-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.intro-title {
  font-size: 72px;
  font-weight: 700;
  color: var(--color-gold-light);
  letter-spacing: 0.3em;
}

.intro-subtitle {
  font-size: 18px;
  color: var(--color-text-dim);
  letter-spacing: 0.2em;
  margin-top: 16px;
}

.intro-btn {
  margin-top: 32px;
  padding: 14px 56px;
  background: rgba(201,168,76,0.12);
  border: 1.5px solid var(--color-gold-light);
  color: var(--color-gold-light);
  font-family: 'Noto Serif SC', serif;
  font-size: 16px;
  letter-spacing: 0.3em;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 20px rgba(201,168,76,0.15), inset 0 0 20px rgba(201,168,76,0.05);
}

.intro-btn:hover {
  background: rgba(201,168,76,0.22);
  box-shadow: 0 0 40px rgba(201,168,76,0.35), inset 0 0 20px rgba(201,168,76,0.1);
  border-color: var(--color-gold-light);
}
</style>
