<template>
  <aside class="app-sidebar" ref="sidebarRef" :class="{ collapsed }">
    <div class="sidebar-inner">
      <div class="sidebar-nav-wrap">
        <router-link to="/data-process" class="sidebar-item sidebar-link" title="能耗计算">
          <span class="sidebar-icon">📊</span>
          <span class="sidebar-text">能耗计算</span>
        </router-link>

        <router-link to="/reports" class="sidebar-item sidebar-link" :class="{ 'router-link-active': isReportsSection }" title="历史报告">
          <span class="sidebar-icon">📋</span>
          <span class="sidebar-text">历史报告</span>
        </router-link>

        <router-link to="/equipment" class="sidebar-item sidebar-link" active-class="router-link-active" :class="{ 'router-link-active': isEquipmentSection }" title="设备信息">
          <span class="sidebar-icon">🖥️</span>
          <span class="sidebar-text">设备信息</span>
        </router-link>

        <button
          type="button"
          class="sidebar-item sidebar-link sidebar-link-button"
          :class="{ 'router-link-active': isAnalysisSection }"
          @click="goAnalysis"
          title="新建对话"
        >
          <span class="sidebar-icon">📝</span>
          <span class="sidebar-text">新建对话</span>
        </button>
        <div class="sidebar-section" v-if="analysisList.length > 0 && !collapsed">
          <div class="sidebar-list-label">分析历史</div>
          <div class="sidebar-list">
            <div
              v-for="a in analysisList"
              :key="a.id"
              class="sidebar-card-wrap"
              :class="{ active: isAnalysisActive(a.id) }"
            >
              <router-link :to="{ path: '/analysis/' + a.id }" class="sidebar-card">
                {{ a.title || '未命名分析' }}
              </router-link>
              <button
                type="button"
                class="sidebar-card-delete"
                @click.stop="onDeleteAnalysis(a.id)"
                title="删除"
                aria-label="删除该分析"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                  <path d="M10 11v6M14 11v6" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="sidebar-user-block">
        <button
          type="button"
          class="sidebar-user-trigger"
          :class="{ open: userMenuOpen }"
          @click.stop="userMenuOpen = !userMenuOpen"
          aria-haspopup="menu"
          :aria-expanded="userMenuOpen"
        >
          <span class="sidebar-user-avatar-wrap">
            <img
              v-if="avatarUrl"
              class="sidebar-user-avatar"
              :src="avatarUrl"
              alt=""
              referrerpolicy="no-referrer"
            />
            <span v-else-if="avatarEmoji" class="sidebar-user-avatar sidebar-user-avatar-emoji">{{ avatarEmoji }}</span>
            <span v-else class="sidebar-user-avatar sidebar-user-avatar-initials">{{ userInitial }}</span>
          </span>
          <span class="sidebar-user-name">{{ authStore.user?.username ?? '用户' }}</span>
        </button>
        <Transition name="dropdown">
          <div v-show="userMenuOpen" class="sidebar-user-dropdown" role="menu" @click.stop>
            <button type="button" class="sidebar-user-item" role="menuitem" @click="onMenuAction('profile')">
              个人资料
            </button>
            <button type="button" class="sidebar-user-item" role="menuitem" @click="onMenuAction('password')">
              修改密码
            </button>
            <button type="button" class="sidebar-user-item" role="menuitem" @click="onMenuAction('permissions')">
              查看账号权限
            </button>
            <div class="sidebar-user-divider" role="separator"></div>
            <button type="button" class="sidebar-user-item sidebar-user-item-danger" role="menuitem" @click="onMenuAction('logout')">
              退出登录
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAnalysisStore } from '../stores/analysis'
import { useAuthStore } from '../stores/auth'

defineProps({ collapsed: Boolean })
const emit = defineEmits(['open-profile', 'open-password', 'open-permissions', 'logout'])

const sidebarRef = ref(null)
const userMenuOpen = ref(false)
const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()
const authStore = useAuthStore()
const { analysisList } = storeToRefs(analysisStore)

const avatarUrl = computed(() => {
  const u = authStore.user?.avatar_img
  if (!u || typeof u !== 'string') return ''
  if (u.startsWith('http') || u.startsWith('/')) {
    if (u.startsWith('http')) return u
    const base = (import.meta.env.VITE_API_BASE || '/api/').replace(/\/api\/?$/, '') || ''
    return base + u
  }
  return ''
})

const avatarEmoji = computed(() => {
  const u = authStore.user?.avatar_img
  if (!u || typeof u !== 'string') return ''
  if (u.startsWith('http') || u.startsWith('/')) return ''
  return u
})

const userInitial = computed(() => {
  const name = authStore.user?.username
  return name && name.length ? name.slice(0, 1).toUpperCase() : '?'
})

function onMenuAction(which) {
  userMenuOpen.value = false
  if (which === 'logout') emit('logout')
  else if (which === 'profile') emit('open-profile')
  else if (which === 'password') emit('open-password')
  else if (which === 'permissions') emit('open-permissions')
}

function onClickOutside(e) {
  if (sidebarRef.value && !sidebarRef.value.contains(e.target)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})

const isAnalysisSection = computed(() => route.path === '/' || route.path === '/analysis' || route.path.startsWith('/analysis/'))
const isEquipmentSection = computed(() => route.path.startsWith('/equipment'))
const isReportsSection = computed(() => route.path === '/reports' || route.path.startsWith('/reports/'))

function isAnalysisActive(id) {
  return route.path === '/analysis/' + id
}

function goAnalysis() {
  router.push({ name: 'home' })
}

function onDeleteAnalysis(id) {
  const wasViewingDeleted = route.path === '/analysis/' + id
  analysisStore.remove(id)
  if (wasViewingDeleted) {
    router.replace({ name: 'home' })
  }
}
</script>

<style scoped>
.app-sidebar {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--surface);
}

.sidebar-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0.75rem 0 0;
}

.sidebar-nav-wrap {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.sidebar-user-block {
  flex-shrink: 0;
  position: relative;
  border-top: 1px solid var(--border);
  padding: 0.75rem 1rem;
  margin-top: 0.25rem;
}

.sidebar-user-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.35rem 0;
  border: none;
  background: none;
  cursor: pointer;
  font-family: var(--font);
  text-align: left;
  border-radius: var(--radius-sm);
  transition: background 0.2s;
}

.sidebar-user-trigger:hover {
  background: rgba(124, 58, 237, 0.08);
}

.sidebar-user-trigger.open {
  background: rgba(124, 58, 237, 0.12);
}

.sidebar-user-avatar-wrap {
  flex-shrink: 0;
}

.sidebar-user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  background: rgba(124, 58, 237, 0.2);
}

.sidebar-user-avatar-initials {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--accent);
}

.sidebar-user-avatar-emoji {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  line-height: 1;
}

.sidebar-user-name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  line-height: 22px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-sidebar.collapsed .sidebar-user-name {
  display: none;
}

.app-sidebar.collapsed .sidebar-user-trigger {
  justify-content: center;
}

.sidebar-user-dropdown {
  position: absolute;
  bottom: calc(100% + 0.35rem);
  left: 0;
  right: 0;
  padding: 0.35rem 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.25);
  z-index: 1000;
}

.sidebar-user-item {
  display: block;
  width: 100%;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  color: var(--text-muted);
  text-align: left;
  border: none;
  background: none;
  cursor: pointer;
  font-family: var(--font);
  transition: color 0.2s, background 0.2s;
}

.sidebar-user-item:hover {
  color: var(--accent);
  background: rgba(124, 58, 237, 0.08);
}

.sidebar-user-item-danger:hover {
  color: var(--danger);
  background: rgba(239, 68, 68, 0.08);
}

.sidebar-user-divider {
  height: 1px;
  margin: 0.35rem 0;
  background: var(--border);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  color: var(--text-muted);
  text-decoration: none;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  font-size: 0.9rem;
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}

.sidebar-item:hover {
  color: var(--accent);
  background: rgba(124, 58, 237, 0.08);
}

.sidebar-link.router-link-active,
.sidebar-link-button.router-link-active {
  color: var(--accent);
  background: rgba(124, 58, 237, 0.12);
}

.sidebar-link-button {
  font-family: var(--font) !important;
  cursor: pointer;
}

.sidebar-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.sidebar-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-sidebar.collapsed .sidebar-text {
  display: none;
}

.app-sidebar.collapsed .sidebar-item {
  justify-content: center;
  padding: 0.5rem;
}

.app-sidebar.collapsed .sidebar-list-label,
.app-sidebar.collapsed .sidebar-list {
  display: none;
}

.sidebar-section {
  border-bottom: 1px solid var(--border);
  padding-top: 0.25rem;
}

.sidebar-list-label {
  padding: 0.25rem 1rem 0;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.sidebar-list {
  padding: 0 0 0.5rem 0;
}

.sidebar-card-wrap {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin: 0.15rem 0.5rem 0.15rem 1rem;
  padding: 0.25rem 0.35rem 0.25rem 0.5rem;
  border-radius: 0 8px 8px 0;
  border-left: 2px solid transparent;
  transition: background 0.2s, border-color 0.2s;
}

.sidebar-card-wrap:hover {
  background: rgba(124, 58, 237, 0.08);
}

.sidebar-card-wrap.active {
  background: rgba(124, 58, 237, 0.12);
  border-left-color: var(--accent);
}

.sidebar-card {
  flex: 1;
  min-width: 0;
  display: block;
  padding: 0.2rem 0.25rem;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.85rem;
  border-radius: 4px;
  transition: color 0.2s;
}

.sidebar-card-wrap:hover .sidebar-card,
.sidebar-card-wrap.active .sidebar-card {
  color: var(--accent);
}

.sidebar-card-delete {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--text-muted);
  cursor: pointer;
  opacity: 0.6;
  transition: color 0.2s, background 0.2s, opacity 0.2s;
}

.sidebar-card-delete:hover {
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
  opacity: 1;
}

</style>
