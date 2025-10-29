import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Login from '../views/Login.vue'
import AssistantSelect from '../views/AssistantSelect.vue'
import Chat from '../views/Chat.vue'

const routes: Array<RouteRecordRaw> = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/assistants', component: AssistantSelect },
  {
    path: '/chat/:id',
    component: Chat,
    props: (route) => ({ id: Number(route.params.id) })
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
