<template>
  <div class="app-wrap">
    <header class="nav-tech">
      <div class="container nav-inner">
        <router-link class="nav-brand" to="/">空压机能效计算系统</router-link>
        <div class="nav-right">
          <template v-if="authStore.token">
            <span class="nav-user-pill">{{ authStore.user?.username }}</span>
            <a class="nav-link-tech nav-link-out" href="#" @click.prevent="logout">退出</a>
          </template>
          <template v-else>
            <router-link class="nav-link-tech nav-link-acc" to="/login">登录 / 注册</router-link>
          </template>
        </div>
      </div>
    </header>
    <div class="app-body" :class="{ 'with-sidebar': authStore.token }">
      <AppSidebar v-if="authStore.token" />
      <main class="main-content">
        <div class="container py-4">
          <div v-if="flash.message" :class="['alert-tech', flash.class]" role="alert">
            {{ flash.message }}
          </div>
          <router-view :key="$route.fullPath" />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, watch, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import AppSidebar from './components/AppSidebar.vue'

const authStore = useAuthStore()
const router = useRouter()
const { flash } = storeToRefs(authStore)

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

onMounted(() => {
  authStore.loadUser()
})
</script>

<style scoped>
.app-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav-tech {
  flex-shrink: 0;
  min-height: 3.25rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  font-family: var(--font-head);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

.nav-inner {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 3.25rem;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.nav-brand {
  flex-shrink: 0;
  max-width: 50%;
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: 0.03em;
  color: var(--text) !important;
  text-decoration: none;
  transition: color 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-brand:hover {
  color: var(--accent) !important;
}

.nav-right {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.nav-user-pill {
  padding: 0.4rem 0.85rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text);
  background: rgba(124, 58, 237, 0.12);
  border: 1px solid rgba(124, 58, 237, 0.25);
  border-radius: 999px;
  white-space: nowrap;
}

.nav-link-tech {
  color: var(--text-muted) !important;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.5rem 0.75rem !important;
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: color 0.2s, background 0.2s;
}

.nav-link-tech:hover {
  color: var(--accent) !important;
  background: rgba(124, 58, 237, 0.08);
}

.nav-link-tech.router-link-active {
  color: var(--accent) !important;
}

.nav-link-acc {
  color: var(--accent) !important;
}

.nav-link-out {
  color: var(--text-muted) !important;
}

.app-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.app-body.with-sidebar {
  flex-direction: row;
  min-height: calc(100vh - 3.25rem);
}

.app-body.with-sidebar .main-content {
  flex: 1;
  min-width: 0;
  min-height: calc(100vh - 3.25rem);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
}

.main-content {
  flex: 1;
  min-height: 0;
}
</style>
