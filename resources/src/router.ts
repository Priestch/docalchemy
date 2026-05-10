import { createWebHashHistory, createRouter } from 'vue-router'

import HomeView from './views/HomeView.vue'
import FileView from './views/FileView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/files/:id', component: FileView },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router;
