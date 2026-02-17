<template>
  <div class="app-wrap">
    <div class="app-body" :class="{ 'with-sidebar': authStore.token, 'sidebar-collapsed': sidebarCollapsed }">
      <div v-if="authStore.token" class="sidebar-column">
        <div class="sidebar-head">
          <div class="sidebar-title">
            <img src="/logo.png" alt="AirComp" class="sidebar-logo" />
            <span class="sidebar-title-full">AirComp</span>
            <span class="sidebar-title-short">AC</span>
          </div>
          <button
            type="button"
            class="sidebar-collapse-btn"
            :title="sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
            aria-label="折叠侧边栏"
            @click="sidebarCollapsed = !sidebarCollapsed"
          >
            <svg v-if="sidebarCollapsed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <path d="M9 18l6-6-6-6" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
        </div>
        <AppSidebar
          :collapsed="sidebarCollapsed"
          @open-profile="openUserModal('profile')"
          @open-password="openUserModal('password')"
          @open-permissions="openUserModal('permissions')"
          @logout="onLogout"
        />
      </div>
      <main class="main-content">
        <div v-if="flash.message" :class="['flash-toast', flash.class]" role="alert">
          {{ flash.message }}
        </div>
        <div class="container py-4" :class="{ 'container--equipment': $route.path.startsWith('/equipment') }">
          <router-view :key="routerViewKey" />
        </div>
      </main>
    </div>
    <ProfileModal :visible="userModal === 'profile'" @close="userModal = null" />
    <PasswordModal :visible="userModal === 'password'" @close="userModal = null" />
    <PermissionsModal :visible="userModal === 'permissions'" @close="userModal = null" />
  </div>
</template>

<script setup>
import { computed, onMounted, watch, onUnmounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from './stores/auth'
import { useRoute, useRouter } from 'vue-router'
import AppSidebar from './components/AppSidebar.vue'
import ProfileModal from './components/ProfileModal.vue'
import PasswordModal from './components/PasswordModal.vue'
import PermissionsModal from './components/PermissionsModal.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const { flash } = storeToRefs(authStore)

const userModal = ref(null)
const SIDEBAR_COLLAPSED_KEY = 'aircomp_sidebar_collapsed'
const sidebarCollapsed = ref(localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1')

function openUserModal(which) {
  userModal.value = which
}

watch(sidebarCollapsed, (v) => {
  localStorage.setItem(SIDEBAR_COLLAPSED_KEY, v ? '1' : '0')
})

onMounted(() => {
  authStore.loadUser()
})

// 设备信息为嵌套路由，用稳定 key 避免 /equipment -> /equipment/clients 时整块被销毁导致右侧空白
const routerViewKey = computed(() =>
  route.path.startsWith('/equipment') ? '/equipment' : route.fullPath
)

const FLASH_AUTO_CLEAR_MS = 4000
let flashTimer = null

watch(() => flash.value.message, (msg) => {
  if (flashTimer) clearTimeout(flashTimer)
  if (msg) {
    flashTimer = setTimeout(() => {
      authStore.clearFlash()
      flashTimer = null
    }, FLASH_AUTO_CLEAR_MS)
  }
})

onUnmounted(() => {
  if (flashTimer) clearTimeout(flashTimer)
})

function logout() {
  authStore.logout()
  router.push('/login')
}

function onLogout() {
  logout()
}
</script>

<style scoped>
.app-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

.app-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  overflow-x: hidden;
  min-width: 0;
}

.app-body.with-sidebar {
  flex-direction: row;
}

.sidebar-column {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 260px;
  min-width: 260px;
  transition: width 0.2s, min-width 0.2s;
  background: var(--surface);
  border-right: 1px solid var(--border);
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.2);
}

.app-body.sidebar-collapsed .sidebar-column {
  width: 56px;
  min-width: 56px;
}

/* 侧边栏顶部：标题 + 折叠按钮 */
.sidebar-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--border);
}

.sidebar-title {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.04em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-logo {
  flex-shrink: 0;
  height: 28px;
  width: auto;
  display: block;
  object-fit: contain;
}

.sidebar-title-full {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-title-short {
  display: none;
}

.app-body.sidebar-collapsed .sidebar-title-full,
.app-body.sidebar-collapsed .sidebar-title-short {
  display: none;
}

.app-body.sidebar-collapsed .sidebar-title {
  justify-content: center;
}

.app-body.sidebar-collapsed .sidebar-logo {
  height: 24px;
}

.sidebar-collapse-btn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.2);
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}

.sidebar-collapse-btn:hover {
  color: var(--accent);
  background: rgba(124, 58, 237, 0.12);
  border-color: rgba(124, 58, 237, 0.35);
}

.app-body.sidebar-collapsed .sidebar-head {
  flex-direction: column;
  padding: 0.5rem;
}

.app-body.sidebar-collapsed .sidebar-collapse-btn {
  width: 100%;
}

.app-body.with-sidebar .main-content {
  flex: 1;
  min-width: 0;
  min-height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
}

.main-content {
  flex: 1;
  min-height: 0;
  position: relative;
}

/* 通知浮层：固定定位，不占文档流，不会挤压侧栏 */
.flash-toast {
  position: fixed;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9998;
  max-width: min(90vw, 28rem);
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 500;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  word-break: break-word;
  pointer-events: none;
}

.flash-toast.alert-success {
  background: var(--success);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.flash-toast.alert-danger {
  background: var(--danger);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.flash-toast.alert-info {
  background: var(--surface-elevated);
  color: var(--text);
  border: 1px solid var(--border);
}
</style>
