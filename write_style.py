
style_part = """
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
  padding: 0 24px;
  height: 48px;
  background: rgba(10,14,26,0.95);
  border-bottom: 1px solid #c9a84c33;
  flex-shrink: 0;
  z-index: 100;
}

.nav-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 4px;
  color: #c9a84c;
  text-shadow: 0 0 12px #c9a84c88;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-links a {
  color: #8b8680;
  text-decoration: none;
  font-size: 14px;
  letter-spacing: 1px;
  transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #c9a84c;
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
  background: rgba(255,255,255,0.02);
  border-left: 1px solid #c9a84c22;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar::-webkit-scrollbar { width: 4px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: #c9a84c44; border-radius: 2px; }

.period-timeline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(10,14,26,0.95);
  border-top: 1px solid #c9a84c33;
  flex-shrink: 0;
}

.period-btn {
  padding: 5px 14px;
  border: 1px solid #c9a84c44;
  background: transparent;
  color: #8b8680;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.2s;
  letter-spacing: 1px;
}

.period-btn:hover { color: #c9a84c; border-color: #c9a84c88; }
.period-btn.active {
  background: rgba(201,168,76,0.15);
  color: #e8c96d;
  border-color: #c9a84c;
  text-shadow: 0 0 8px #c9a84c66;
}

.sidebar-period { text-align: center; padding: 8px 0; }
.period-name-label { font-size: 18px; color: #c9a84c; letter-spacing: 3px; margin-bottom: 4px; }
.period-sub { font-size: 12px; color: #8b8680; margin-bottom: 4px; }
.building-count { font-size: 13px; color: #e6d5b8aa; }

.overview-btn {
  width: 100%;
  padding: 7px;
  border: 1px solid #c9a84c44;
  background: transparent;
  color: #c9a84c;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.2s;
  letter-spacing: 1px;
}
.overview-btn:hover, .overview-btn.active {
  background: rgba(201,168,76,0.12);
  border-color: #c9a84c;
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
  padding: 6px 10px;
  border: 1px solid #c9a84c22;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255,255,255,0.02);
}
.type-stat-item:hover { border-color: #c9a84c66; background: rgba(201,168,76,0.05); }
.type-stat-item.type-hidden { opacity: 0.4; }
.type-count { margin-left: auto; font-size: 13px; color: #e6d5b8; }
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
.bc-name { font-size: 20px; letter-spacing: 3px; color: #c9a84c; text-shadow: 0 0 10px #c9a84c66; }
.bc-image-wrap { width: 100%; border-radius: 2px; overflow: hidden; border: 1px solid #c9a84c33; }
.bc-image { width: 100%; height: 160px; object-fit: cover; display: block; }
.bc-tagline { font-size: 12px; color: #8b8680; line-height: 1.6; font-style: italic; }
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
  width: 100%; padding: 8px;
  background: rgba(201,168,76,0.1);
  border: 1px solid #c9a84c66;
  color: #c9a84c;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px; cursor: pointer; border-radius: 2px;
  transition: all 0.2s; letter-spacing: 2px;
}
.detail-btn:hover { background: rgba(201,168,76,0.2); border-color: #c9a84c; }

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
  background: rgba(10,14,26,0.92);
  border: 1px solid #c9a84c44;
  border-radius: 4px; padding: 12px 14px;
  min-width: 160px; max-width: 200px;
  backdrop-filter: blur(8px);
}
.cc-label { font-size: 11px; color: #8b8680; letter-spacing: 1px; margin-bottom: 4px; }
.cc-province { font-size: 18px; color: #c9a84c; letter-spacing: 2px; font-weight: 700; }
.cc-count { font-size: 12px; color: #e6d5b8aa; margin-bottom: 6px; }
.cc-map { width: 100%; height: 100px; }
.cc-divider { height: 1px; background: #c9a84c33; margin: 6px 0; }
.cc-list { display: flex; flex-direction: column; gap: 3px; }
.cc-item { font-size: 12px; color: #e6d5b8aa; display: flex; align-items: center; gap: 4px; }

.tag {
  display: inline-block; padding: 1px 6px; border-radius: 2px;
  font-size: 11px; font-family: 'Noto Serif SC', serif;
}
.tag-\u7687\u5bab { background: rgba(232,201,109,0.15); color: #e8c96d; border: 1px solid #e8c96d44; }
.tag-\u5b98\u5e9c { background: rgba(0,212,255,0.1); color: #00d4ff; border: 1px solid #00d4ff44; }
.tag-\u6c11\u5c45 { background: rgba(129,199,132,0.1); color: #81c784; border: 1px solid #81c78444; }
.tag-\u6865\u6881 { background: rgba(255,138,101,0.1); color: #ff8a65; border: 1px solid #ff8a6544; }

.text-glow-gold { color: #c9a84c; text-shadow: 0 0 10px #c9a84c66; }
</style>
"""

with open(r'D:/jishe/ancient-architecture-viz/src/views/ExploreView_new.vue', 'a', encoding='utf-8') as f:
    f.write(style_part)

print('style appended')
