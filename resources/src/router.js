import { createWebHashHistory, createRouter } from 'vue-router'

import HomeView from './pages/HomeView.vue'
import ProjectView from './pages/ProjectView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/project', component: ProjectView },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export {
  router,
}
