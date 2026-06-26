import { createRouter, createWebHistory } from 'vue-router'

import Events from './components/Events.vue'
import Assets from './components/Assets.vue'
import Search from './components/Search.vue'

const routes = [
  { path: '/', redirect: '/events' }, 
  { path: '/events', component: Events },
  { path: '/assets', component: Assets },
  { path: '/search', component: Search }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router