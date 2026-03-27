import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Intro',
    component: () => import('../views/IntroView.vue'),
  },
  {
    path: '/explore',
    name: 'Explore',
    component: () => import('../views/ExploreView.vue'),
  },
  {
    path: '/building/:id',
    name: 'BuildingDetail',
    component: () => import('../views/BuildingDetailView.vue'),
  },
  {
    path: '/works',
    name: 'Works',
    component: () => import('../views/HeritageView.vue'),
  },
  {
    path: '/lineage',
    name: 'Lineage',
    component: () => import('../views/HeritageView.vue'),
  },
  {
    path: '/heritage',
    redirect: '/works',
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
