<template>
  <aside class="app-sidebar">
    <div class="sidebar-inner">
      <router-link to="/data-process" class="sidebar-item sidebar-link">
        <span class="sidebar-icon">📊</span>
        <span>数据与对比</span>
      </router-link>

      <router-link to="/equipment/clients" class="sidebar-item sidebar-link">
        <span class="sidebar-icon">🖥️</span>
        <span>客户设备信息</span>
      </router-link>
      <router-link to="/equipment/suppliers" class="sidebar-item sidebar-link">
        <span class="sidebar-icon">📦</span>
        <span>供应商设备信息</span>
      </router-link>

      <button
        type="button"
        class="sidebar-item sidebar-link sidebar-link-button"
        :class="{ 'router-link-active': isAnalysisSection }"
        @click="goAnalysis"
      >
        <span class="sidebar-icon">📝</span>
        <span>新建分析</span>
      </button>
      <div class="sidebar-section" v-if="analysisList.length > 0">
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
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAnalysisStore } from '../stores/analysis'

const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()
const { analysisList } = storeToRefs(analysisStore)

const isAnalysisSection = computed(() => route.path === '/' || route.path === '/analysis' || route.path.startsWith('/analysis/'))

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
  width: 260px;
  min-width: 260px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: min-width 0.2s, width 0.2s;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.2);
}

.sidebar-inner {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 0;
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
