import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import ForgotPassword from '../views/ForgotPassword.vue'

import AssistantSelect from '../views/AssistantSelect.vue'
import Chat from '../views/Chat.vue'
import AdminDocs from '../views/AdminDocs.vue'
import AdminAssistants from '../views/AdminAssistants.vue'
import AdminUsers from '../views/AdminUsers.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { useAuthStore } from '@/stores/auth'

const routes: Array<RouteRecordRaw> = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/forgot-password', component: ForgotPassword },
  { path: '/assistants', component: AssistantSelect, meta: { requiresAuth: true } },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/assistants' },
      { path: 'assistants', component: AdminAssistants },
      { path: 'docs', component: AdminDocs },
      { path: 'users', component: AdminUsers },
    ],
  },
  {
    path: '/chat/:id',
    component: Chat,
    props: route => ({ id: Number(route.params.id) }),
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta?.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta?.requiresAdmin)

  if (requiresAuth && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  if (requiresAdmin && authStore.role !== 'admin') {
    next('/assistants')
    return
  }

  if (to.path === '/login' && authStore.isLoggedIn) {
    next('/assistants')
    return
  }

  next()
})

export default router
