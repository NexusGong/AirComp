<template>
  <div class="page-card">
    <h1 class="page-title">历史报告</h1>
    <p class="section-desc">所有能耗计算生成的报告均保存在此，点击卡片可查看详情并下载 Excel。</p>

    <div v-if="loading" class="text-muted">加载中…</div>
    <div v-else-if="list.length === 0" class="empty-hint">暂无历史报告，请先在「能耗计算」或「新建对话」中完成节能量计算。</div>
    <div v-else class="report-cards">
      <div v-for="r in list" :key="r.id" class="report-card-wrap">
        <router-link :to="'/reports/' + r.id" class="report-card">
          <div class="report-card-title">{{ r.title || r.company_name || '节能量计算' }}</div>
          <div class="report-card-meta">
            <span class="report-card-date">{{ formatDate(r.created_at) }}</span>
            <span class="report-card-source">{{ r.source === 'manual' ? '能耗计算' : '新建对话' }}</span>
          </div>
          <div class="report-card-energy">
            <span class="report-card-kwh">年节电量 {{ (r.energy_savings_kwh ?? 0).toLocaleString() }} kWh</span>
            <span v-if="r.energy_savings_cost != null" class="report-card-cost">节约电费 ¥{{ Number(r.energy_savings_cost).toLocaleString() }}</span>
          </div>
        </router-link>
        <button
          type="button"
          class="report-card-delete"
          title="删除"
          aria-label="删除该报告"
          @click.stop="openDeleteConfirm(r.id)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
            <path d="M10 11v6M14 11v6" />
          </svg>
        </button>
      </div>
    </div>

    <ConfirmModal
      :visible="showConfirm"
      title="删除确认"
      message="确定要删除这条历史报告吗？删除后无法恢复。"
      confirm-text="确定删除"
      cancel-text="取消"
      :danger="true"
      @confirm="doDelete"
      @cancel="showConfirm = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import ConfirmModal from '../components/ConfirmModal.vue'

const authStore = useAuthStore()
const list = ref([])
const loading = ref(true)
const showConfirm = ref(false)
const pendingDeleteId = ref(null)

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function openDeleteConfirm(id) {
  pendingDeleteId.value = id
  showConfirm.value = true
}

async function doDelete() {
  const id = pendingDeleteId.value
  showConfirm.value = false
  pendingDeleteId.value = null
  if (id == null) return
  try {
    await api.delete(`reports/${id}`)
    list.value = list.value.filter((r) => r.id !== id)
    authStore.setFlash('已删除', 'success')
  } catch {
    authStore.setFlash('删除失败', 'danger')
  }
}

async function load() {
  try {
    const res = await api.get('reports')
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.section-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.empty-hint {
  color: var(--text-muted);
  padding: 2rem;
  text-align: center;
}

.report-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.report-card-wrap {
  position: relative;
}

.report-card {
  display: block;
  padding: 1.25rem;
  padding-right: 2.5rem;
  background: linear-gradient(145deg, var(--surface-elevated) 0%, rgba(24, 24, 28, 0.98) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.report-card-wrap:hover .report-card {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px rgba(124, 58, 237, 0.2);
}

.report-card-delete {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  opacity: 0.7;
  transition: color 0.2s, background 0.2s, opacity 0.2s;
}

.report-card-delete:hover {
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
  opacity: 1;
}

.report-card-title {
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: var(--text);
}

.report-card-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.report-card-energy {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.report-card-kwh {
  color: var(--primary);
  font-weight: 500;
}

.report-card-cost {
  color: var(--text-muted);
}
</style>
