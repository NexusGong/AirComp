<template>
  <div class="equipment-layout">
    <aside class="equipment-sub-sidebar">
      <div class="equipment-sub-label">设备类型</div>
      <router-link
        to="/equipment/clients"
        class="equipment-sub-item"
        :class="{ active: isClients }"
      >
        <span class="equipment-sub-icon">🖥️</span>
        <span>客户</span>
      </router-link>
      <router-link
        to="/equipment/suppliers"
        class="equipment-sub-item"
        :class="{ active: isSuppliers }"
      >
        <span class="equipment-sub-icon">📦</span>
        <span>供应商</span>
      </router-link>
    </aside>
    <div class="equipment-main">
      <router-view v-slot="{ Component }">
        <component v-if="Component" :is="Component" />
        <div v-else class="equipment-main-placeholder">加载中…</div>
      </router-view>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const isClients = computed(() => route.path.startsWith('/equipment/clients'))
const isSuppliers = computed(() => route.path.startsWith('/equipment/suppliers'))
</script>

<style scoped>
.equipment-layout {
  display: flex;
  gap: 0;
  align-items: stretch;
  min-height: 0;
  width: 100%;
}

.equipment-main {
  flex: 1;
  min-width: 0;
  min-height: 320px;
  padding: 0 1.25rem 1.5rem 1rem;
  overflow-x: auto;
}

.equipment-main-placeholder {
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.95rem;
}

.equipment-sub-sidebar {
  width: 160px;
  min-width: 160px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.equipment-sub-label {
  padding: 0 1rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.03em;
}

.equipment-sub-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s, background 0.2s;
  border-left: 3px solid transparent;
  margin-left: 0;
}

.equipment-sub-item:hover {
  color: var(--accent);
  background: rgba(124, 58, 237, 0.08);
}

.equipment-sub-item.active {
  color: var(--accent);
  background: rgba(124, 58, 237, 0.12);
  border-left-color: var(--accent);
}

.equipment-sub-icon {
  font-size: 1rem;
  flex-shrink: 0;
}
</style>
