import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/Analysis.vue'), meta: { requiresAuth: true } },
  { path: '/analysis', name: 'analysis', component: () => import('../views/Analysis.vue'), meta: { requiresAuth: true } },
  { path: '/analysis/:id', name: 'analysis-id', component: () => import('../views/Analysis.vue'), meta: { requiresAuth: true } },
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/register', redirect: '/login' },
  { path: '/user/:username', component: () => import('../views/UserPage.vue'), meta: { requiresAuth: true } },
  {
    path: '/equipment',
    component: () => import('../views/EquipmentLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/equipment/clients' },
      { path: 'clients', component: () => import('../views/ClientEquipmentPage.vue') },
      { path: 'suppliers', component: () => import('../views/SupplierEquipmentPage.vue') },
    ],
  },
  { path: '/add-client', redirect: (to) => ({ path: '/equipment/clients', query: { view: 'add', ...to.query } }) },
  { path: '/add-supplier', redirect: (to) => ({ path: '/equipment/suppliers', query: { view: 'add', ...to.query } }) },
  { path: '/data-process', component: () => import('../views/DataProcess.vue'), meta: { requiresAuth: true } },
  { path: '/reports', component: () => import('../views/Reports.vue'), meta: { requiresAuth: true } },
  { path: '/reports/:id', component: () => import('../views/ReportDetail.vue'), meta: { requiresAuth: true } },
  { path: '/data-modify/client/:id', component: () => import('../views/ModifyClient.vue'), meta: { requiresAuth: true } },
  { path: '/data-modify/supplier/:id', component: () => import('../views/ModifySupplier.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
