<template>
  <div class="page-card">
    <div v-if="loading" class="text-muted">加载中…</div>
    <div v-else-if="!report" class="empty-hint">报告不存在或已删除。</div>
    <template v-else>
      <div class="report-detail-header">
        <h1 class="page-title">{{ report.title || report.company_name || '节能量计算' }}</h1>
        <div class="report-detail-header-actions">
          <router-link to="/reports" class="btn btn-ghost">返回列表</router-link>
          <button type="button" class="btn btn-danger-tech" @click="showConfirm = true">删除报告</button>
        </div>
      </div>
      <dl class="report-detail-meta">
        <dt>计算时间</dt>
        <dd>{{ formatDate(report.created_at) }}</dd>
        <dt>来源</dt>
        <dd>{{ report.source === 'manual' ? '能耗计算' : '新建对话' }}</dd>
        <dt>年节电量</dt>
        <dd>{{ (report.energy_savings_kwh ?? 0).toLocaleString() }} kWh</dd>
        <dt v-if="report.energy_savings_cost != null">年节约电费</dt>
        <dd v-if="report.energy_savings_cost != null">¥{{ Number(report.energy_savings_cost).toLocaleString() }}</dd>
      </dl>
      <div class="report-detail-actions">
        <button type="button" class="btn btn-acc" :disabled="downloading" @click="doDownload">
          {{ downloading ? '下载中…' : '下载 Excel' }}
        </button>
      </div>
    </template>

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
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import ConfirmModal from '../components/ConfirmModal.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const report = ref(null)
const loading = ref(true)
const downloading = ref(false)
const showConfirm = ref(false)

async function doDownload() {
  if (!report.value?.id) return
  downloading.value = true
  try {
    const res = await api.get(`reports/${report.value.id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = (report.value.company_name || report.value.title || '节能量计算') + '.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    // ignore
  } finally {
    downloading.value = false
  }
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function load() {
  const id = route.params.id
  if (!id) {
    report.value = null
    loading.value = false
    return
  }
  loading.value = true
  try {
    const res = await api.get(`reports/${id}`)
    report.value = res.data
  } catch {
    report.value = null
  } finally {
    loading.value = false
  }
}

async function doDelete() {
  const id = report.value?.id
  showConfirm.value = false
  if (!id) return
  try {
    await api.delete(`reports/${id}`)
    authStore.setFlash('已删除', 'success')
    router.replace('/reports')
  } catch {
    authStore.setFlash('删除失败', 'danger')
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<style scoped>
.report-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.report-detail-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.report-detail-meta {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 2rem;
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

.report-detail-meta dt {
  color: var(--text-muted);
  font-weight: 500;
}

.report-detail-meta dd {
  margin: 0;
  color: var(--text);
}

.report-detail-actions {
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.empty-hint {
  color: var(--text-muted);
  padding: 2rem;
}
</style>
