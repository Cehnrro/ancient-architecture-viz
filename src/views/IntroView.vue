<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'

const router = useRouter()

onMounted(() => {
  // 背景Ken Burns缓慢缩放
  gsap.fromTo('.bg-image', { scale: 1.1 }, { scale: 1, duration: 8, ease: 'power1.out' })

  // 标题淡入 + 光效扫过
  gsap.from('.intro-title', { opacity: 0, y: 40, duration: 1.2, ease: 'power3.out' })
  gsap.fromTo('.title-shimmer', { x: '-100%' }, { x: '200%', duration: 1.5, delay: 1.2, ease: 'power2.inOut' })

  // 分隔线从中间展开
  gsap.fromTo('.divider-gold', { scaleX: 0 }, { scaleX: 1, duration: 0.8, delay: 0.4, ease: 'power3.out' })

  gsap.from('.intro-subtitle', { opacity: 0, y: 20, duration: 1, delay: 0.5, ease: 'power3.out' })
  gsap.fromTo('.intro-btn', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 1, delay: 1, ease: 'power3.out' })
})
</script>

<template>
  <div class="intro-page">
    <!-- 背景图层（独立用于Ken Burns） -->
    <div class="bg-image" />
    <!-- 暗色遮罩 -->
    <div class="bg-overlay" />

    <!-- 中央内容 -->
    <div class="center-content">
      <div class="intro-title text-glow-gold">
        匠心千年
        <span class="title-shimmer" />
      </div>
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
  background: #0a0e1a;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.bg-image {
  position: absolute;
  inset: -20px;
  background: url('/images/open/intro-bg.png') center/cover no-repeat;
  will-change: transform;
}

.bg-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(10,14,26,0.6) 0%, rgba(10,14,26,0.3) 40%, rgba(10,14,26,0.5) 70%, rgba(10,14,26,0.8) 100%),
    radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(10,14,26,0.7) 100%);
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
  position: relative;
  overflow: hidden;
  display: inline-block;
}

.title-shimmer {
  position: absolute;
  top: 0; left: 0;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  pointer-events: none;
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
  transform: scale(1.04);
}

.intro-btn:active {
  transform: scale(0.97);
  box-shadow: 0 0 16px rgba(201,168,76,0.25), inset 0 0 12px rgba(201,168,76,0.08);
}

.intro-btn:focus-visible {
  outline: 2px solid var(--color-gold-light);
  outline-offset: 4px;
  box-shadow: 0 0 40px rgba(201,168,76,0.35), inset 0 0 20px rgba(201,168,76,0.1);
}
</style>
