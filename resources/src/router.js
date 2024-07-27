import { createWebHashHistory, createRouter } from 'vue-router'

import HomeView from './pages/HomePage.vue'
import ProjectView from './pages/ProjectPage.vue'
import ProjectDetailPage from './pages/ProjectDetailPage.vue'

const routes = [
  { path: '/', component: HomeView, name: 'home' },
  { path: '/projects', component: ProjectView, name: 'projectList' },
  { path: '/projects/:id', component: ProjectDetailPage, name: 'projectDetail' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export {
  router,
}
