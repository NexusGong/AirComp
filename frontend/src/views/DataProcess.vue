<template>
  <div class="page-card">
    <h1 class="page-title">能耗计算</h1>

    <div class="equipment-select-section">
      <p class="section-title">添加设备对比</p>
      <p class="section-desc">先选择要替换的原有设备（客户），再选择替换后的新设备（供应商），形成一对一的节能对比关系。设备需先在 <router-link to="/equipment">设备信息</router-link> 中录入。</p>
      <div class="compare-cards">
        <div class="compare-card compare-card--client">
          <div class="compare-card-header">
            <span class="compare-card-label">原有设备（客户）</span>
          </div>
          <div class="compare-card-body">
            <label class="compare-field">
              <span class="compare-field-label">选择公司</span>
              <select v-model="selectedCompany" class="form-select" @change="onCompanyChange">
                <option value="">请选择公司</option>
                <option v-for="n in companyNames" :key="n" :value="n">{{ n }}</option>
              </select>
            </label>
            <label class="compare-field">
              <span class="compare-field-label">选择设备</span>
              <select v-model="selectedClientKey" class="form-select form-select-device" :disabled="!selectedCompany" @change="onClientDeviceChange">
                <option value="">请先选择公司</option>
                <option v-for="c in clientDevicesInCompany" :key="clientDeviceKey(c)" :value="clientDeviceKey(c)">
                  {{ deviceOptionLabel(c) }}
                </option>
              </select>
            </label>
          </div>
        </div>
        <div class="compare-card-arrow" aria-hidden="true">→</div>
        <div class="compare-card compare-card--supplier">
          <div class="compare-card-header">
            <span class="compare-card-label">替换设备（供应商）</span>
          </div>
          <div class="compare-card-body">
            <label class="compare-field">
              <span class="compare-field-label">选择供应商</span>
              <select v-model="selectedSupplierName" class="form-select" @change="onSupplierChange">
                <option value="">请选择供应商</option>
                <option v-for="n in supplierNames" :key="n" :value="n">{{ n }}</option>
              </select>
            </label>
            <label class="compare-field">
              <span class="compare-field-label">选择设备</span>
              <select v-model="selectedSupplierKey" class="form-select form-select-device" :disabled="!selectedSupplierName" @change="onSupplierDeviceChange">
                <option value="">请先选择供应商</option>
                <option v-for="s in supplierDevicesInSupplier" :key="supplierDeviceKey(s)" :value="supplierDeviceKey(s)">
                  {{ deviceOptionLabel(s) }}
                </option>
              </select>
            </label>
          </div>
        </div>
      </div>
      <div class="compare-add-wrap">
        <button
          type="button"
          class="btn btn-acc"
          :disabled="!canAddCompare"
          @click="addCompare"
        >
          添加对比
        </button>
        <span v-if="!canAddCompare" class="compare-add-hint">请先选择原有设备与替换设备</span>
      </div>
    </div>

    <p class="section-title">选择参与节能量计算的对比项</p>
    <form @submit.prevent="generate">
      <div class="compare-table-wrap table-responsive mb-3">
        <table class="table table-tech table-bordered table-sm compare-table">
          <thead>
            <tr>
              <th class="compare-th-origin">原有设备（客户）</th>
              <th class="compare-th-arrow" aria-hidden="true"></th>
              <th class="compare-th-new">替换设备（供应商）</th>
              <th>操作</th>
              <th class="compare-th-check">参与计算</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in compareList" :key="row.id" class="compare-row">
              <td class="compare-td-origin">
                <span class="compare-cell-company">{{ row.company_name }}</span>
                <span class="compare-cell-detail">{{ row.client_no }} · {{ row.client_model }}（{{ row.client_brand }}）</span>
              </td>
              <td class="compare-td-arrow">→</td>
              <td class="compare-td-new">
                <span class="compare-cell-company">{{ row.supplier_name }}</span>
                <span class="compare-cell-detail">{{ row.supplier_no }} · {{ row.supplier_model }}（{{ row.supplier_brand }}）</span>
              </td>
              <td>
                <button type="button" class="btn btn-danger-tech btn-sm" @click="openDeleteConfirm(row.id)">删除</button>
              </td>
              <td class="compare-td-check">
                <label class="compare-check-label">
                  <input type="checkbox" :value="row.id" v-model="selectedCompareIds" class="form-check-input" />
                  <span>勾选</span>
                </label>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="compareList.length === 0" class="text-muted small mb-3">暂无对比项，请在上方选择原有设备与替换设备后点击「添加对比」。</p>
      <p v-else class="text-muted small mb-3">勾选需要参与节能量计算的对比项，设置下方计算参数后点击「计算节能量」生成报告并加入历史报告。</p>

      <p class="section-title calc-params-title">计算参数</p>
      <div class="calc-params-grid mb-4">
        <label class="calc-param">
          <span class="calc-param-label">年运行时间（小时）</span>
          <input v-model.number="calcParams.running_hours_per_year" type="number" min="1" class="form-control" />
          <span class="calc-param-hint">用于折算年节电量，常用 8000</span>
        </label>
        <label class="calc-param">
          <span class="calc-param-label">电费（元/kWh）</span>
          <input v-model.number="calcParams.electricity_price" type="number" min="0" step="0.01" class="form-control" placeholder="0.8" />
          <span class="calc-param-hint">用于计算年节约电费，默认 0.8</span>
        </label>
        <label class="calc-param">
          <span class="calc-param-label">服务系数默认值</span>
          <input v-model.number="calcParams.default_ser_p" type="number" min="0" step="0.01" class="form-control" placeholder="按品牌" />
          <span class="calc-param-hint">未设则按品牌</span>
        </label>
      </div>

      <div class="d-flex flex-wrap gap-2 align-items-center">
        <button type="submit" class="btn btn-acc" :disabled="selectedCompareIds.length === 0 || generating">
          {{ generating ? '计算中…' : '计算节能量' }}
        </button>
        <router-link v-if="lastReportId" :to="'/reports/' + lastReportId" class="btn btn-outline-acc">前往历史报告</router-link>
      </div>
    </form>

    <ConfirmModal
      :visible="showConfirm"
      :title="confirmTitle"
      :message="confirmMessage"
      confirm-text="确定删除"
      cancel-text="取消"
      :danger="true"
      @confirm="doDelete"
      @cancel="showConfirm = false"
    />

    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showReportSuccessModal" class="report-success-overlay" @click.self="showReportSuccessModal = false">
          <div class="report-success-modal" role="dialog" aria-modal="true" aria-labelledby="report-success-title">
            <div class="report-success-header">
              <h2 id="report-success-title" class="report-success-title">计算完成</h2>
              <button type="button" class="report-success-close" aria-label="关闭" @click="showReportSuccessModal = false">×</button>
            </div>
            <div class="report-success-body">
              <p class="report-success-msg">节能量计算报告已生成，可下载 Excel。</p>
              <p class="report-success-hint">已同步保存至「<router-link to="/reports" @click="showReportSuccessModal = false">历史报告</router-link>」，可随时在左侧侧边栏进入「历史报告」查看或下载。</p>
              <div class="report-success-actions">
                <button type="button" class="btn btn-acc" :disabled="reportDownloading" @click="downloadReportExcel">
                  {{ reportDownloading ? '下载中…' : '下载 Excel' }}
                </button>
                <router-link to="/reports" class="btn btn-outline-acc" @click="showReportSuccessModal = false">前往历史报告</router-link>
                <button type="button" class="btn btn-ghost" @click="showReportSuccessModal = false">关闭</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import ConfirmModal from '../components/ConfirmModal.vue'

const authStore = useAuthStore()
const rawClients = ref([])
const rawSuppliers = ref([])
const compareList = ref([])
const selectedCompany = ref('')
const selectedSupplierName = ref('')
const selectedClientKey = ref('')
const selectedSupplierKey = ref('')
const compareForm = reactive({
  company_name: '',
  client_no: '',
  client_brand: '',
  client_model: '',
  supplier_name: '',
  supplier_no: '',
  supplier_brand: '',
  supplier_model: '',
})
const calcParams = reactive({
  running_hours_per_year: 8000,
  electricity_price: 0.8,
  default_ser_p: undefined,
})
const selectedCompareIds = ref([])
const generating = ref(false)
const lastReportId = ref(null)
const lastReportCompanyName = ref('')
const showReportSuccessModal = ref(false)
const reportDownloading = ref(false)
const showConfirm = ref(false)
const pendingDeleteId = ref(null)

const companyNames = computed(() => {
  const names = [...new Set(rawClients.value.map((c) => c.name).filter(Boolean))]
  return names.sort()
})
const supplierNames = computed(() => {
  const names = [...new Set(rawSuppliers.value.map((s) => s.name).filter(Boolean))]
  return names.sort()
})
const clientDevicesInCompany = computed(() => {
  if (!selectedCompany.value) return []
  return rawClients.value.filter((c) => c.name === selectedCompany.value)
})
const supplierDevicesInSupplier = computed(() => {
  if (!selectedSupplierName.value) return []
  return rawSuppliers.value.filter((s) => s.name === selectedSupplierName.value)
})
const canAddCompare = computed(() => {
  return (
    compareForm.company_name &&
    compareForm.client_no !== '' &&
    compareForm.supplier_name &&
    compareForm.supplier_no !== ''
  )
})

const confirmTitle = computed(() => '删除确认')
const confirmMessage = computed(() => {
  return '确定要删除这条对比关系吗？删除后无法恢复。'
})

function clientDeviceKey(c) {
  return [c.name, c.no, c.brand, c.model].join('|')
}
function supplierDeviceKey(s) {
  return [s.name, s.no, s.brand, s.model].join('|')
}
/** 下拉选项文案：型号 品牌 功率 气量 额定压力（客户与供应商结构一致） */
function deviceOptionLabel(d) {
  const model = d.model ?? ''
  const brand = d.brand ?? ''
  const power = d.ori_power != null ? Number(d.ori_power).toFixed(1) + ' kW' : ''
  const air = d.air != null ? d.air + ' m³/min' : ''
  const pressure = d.origin_pre != null ? d.origin_pre + ' MPa' : ''
  return [model, brand, power, air, pressure].filter(Boolean).join(' · ')
}
function onCompanyChange() {
  selectedClientKey.value = ''
  compareForm.company_name = selectedCompany.value
  compareForm.client_no = ''
  compareForm.client_brand = ''
  compareForm.client_model = ''
}
function onSupplierChange() {
  selectedSupplierKey.value = ''
  compareForm.supplier_name = selectedSupplierName.value
  compareForm.supplier_no = ''
  compareForm.supplier_brand = ''
  compareForm.supplier_model = ''
}
function onClientDeviceChange() {
  const key = selectedClientKey.value
  if (!key) return
  const parts = key.split('|')
  const [name, no, brand, model] = parts
  compareForm.company_name = name || ''
  compareForm.client_no = no !== undefined && no !== '' ? Number(no) : ''
  compareForm.client_brand = brand || ''
  compareForm.client_model = model || ''
}
function onSupplierDeviceChange() {
  const key = selectedSupplierKey.value
  if (!key) return
  const parts = key.split('|')
  const [name, no, brand, model] = parts
  compareForm.supplier_name = name || ''
  compareForm.supplier_no = no !== undefined && no !== '' ? Number(no) : ''
  compareForm.supplier_brand = brand || ''
  compareForm.supplier_model = model || ''
}

async function load() {
  const [clients, suppliers, compare] = await Promise.all([
    api.get('machines/clients'),
    api.get('machines/suppliers'),
    api.get('machines/compare'),
  ])
  rawClients.value = clients.data || []
  rawSuppliers.value = suppliers.data || []
  compareList.value = compare.data || []
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
  await api.delete(`machines/compare/${id}`)
  authStore.setFlash('已删除', 'success')
  load()
}

async function addCompare() {
  if (!canAddCompare.value) return
  await api.post('machines/compare', compareForm)
  authStore.setFlash('对比已添加', 'success')
  selectedClientKey.value = ''
  selectedSupplierKey.value = ''
  compareForm.client_no = ''
  compareForm.client_brand = ''
  compareForm.client_model = ''
  compareForm.supplier_no = ''
  compareForm.supplier_brand = ''
  compareForm.supplier_model = ''
  await load()
}

async function downloadReportExcel() {
  const id = lastReportId.value
  if (!id) return
  reportDownloading.value = true
  try {
    const res = await api.get(`reports/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = (lastReportCompanyName.value || '节能量计算') + '.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    authStore.setFlash('下载失败', 'danger')
  } finally {
    reportDownloading.value = false
  }
}

async function generate() {
  if (selectedCompareIds.value.length === 0) return
  generating.value = true
  lastReportId.value = null
  try {
    const body = { compare_ids: selectedCompareIds.value }
    if (calcParams.running_hours_per_year != null) body.running_hours_per_year = calcParams.running_hours_per_year
    if (calcParams.electricity_price != null && calcParams.electricity_price !== '') body.electricity_price = Number(calcParams.electricity_price)
    if (calcParams.default_ser_p != null && calcParams.default_ser_p !== '') body.default_ser_p = Number(calcParams.default_ser_p)
    const res = await api.post('calculate', body)
    lastReportId.value = res.data.report_id ?? null
    lastReportCompanyName.value = res.data.company_name ?? ''
    if (lastReportId.value) showReportSuccessModal.value = true
    else authStore.setFlash(res.data.message || '生成成功', 'success')
  } catch (e) {
    authStore.setFlash(e.response?.data?.detail || '计算失败', 'danger')
  } finally {
    generating.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.text-muted { color: var(--text-muted) !important; }

.equipment-select-section { margin-bottom: 1.5rem; }
.section-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}
.compare-cards {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 1rem;
  margin-bottom: 1rem;
}
.compare-card {
  flex: 1;
  min-width: 280px;
  background: linear-gradient(145deg, var(--surface-elevated) 0%, rgba(24, 24, 28, 0.98) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.compare-card--client { border-left: 3px solid var(--primary); }
.compare-card--supplier { border-left: 3px solid #22c55e; }
.compare-card-header {
  display: flex;
  align-items: center;
  padding: 0.6rem 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid var(--border);
}
.compare-card-label { font-size: 0.95rem; font-weight: 600; color: var(--text); }
.compare-card-body { padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.compare-card-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--primary);
  opacity: 0.8;
  min-width: 2rem;
}
.compare-field { display: flex; flex-direction: column; gap: 0.25rem; }
.compare-field-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-muted);
}
.compare-field .form-select { width: 100%; }
.form-select-device { min-height: 2.5rem; font-size: 0.9rem; }
.form-select-device option { padding: 0.25rem 0; white-space: normal; }
.compare-add-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.compare-add-hint { font-size: 0.85rem; color: var(--text-muted); }

.calc-params-title { margin-top: 1rem; }
.calc-params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
.calc-param { display: flex; flex-direction: column; gap: 0.25rem; }
.calc-param-label { font-size: 0.9rem; font-weight: 500; color: var(--text-muted); }
.calc-param-hint { font-size: 0.75rem; color: var(--text-muted); }

.compare-table-wrap { border-radius: var(--radius); overflow: hidden; }
.compare-table .compare-th-origin,
.compare-table .compare-th-new { text-align: left; min-width: 140px; }
.compare-table .compare-th-arrow { width: 2.5rem; text-align: center; color: var(--text-muted); }
.compare-table .compare-th-check { width: 6rem; text-align: center; }
.compare-td-origin,
.compare-td-new { vertical-align: middle; }
.compare-td-origin .compare-cell-company,
.compare-td-new .compare-cell-company { display: block; font-weight: 600; color: var(--text); }
.compare-td-origin .compare-cell-detail,
.compare-td-new .compare-cell-detail { display: block; font-size: 0.85rem; color: var(--text-muted); }
.compare-td-arrow { text-align: center; color: var(--primary); font-weight: 600; vertical-align: middle; }
.compare-td-check { vertical-align: middle; text-align: center; }
.compare-check-label { display: inline-flex; align-items: center; gap: 0.35rem; cursor: pointer; margin: 0; font-size: 0.9rem; color: var(--text-muted); }
.compare-check-label:hover { color: var(--accent); }
.compare-row:hover { background: rgba(124, 58, 237, 0.04); }

/* 计算完成弹窗 */
.report-success-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(6px);
}
.report-success-modal {
  width: 100%;
  max-width: 420px;
  background: var(--surface-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(124, 58, 237, 0.08);
  overflow: hidden;
}
.report-success-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  background: rgba(124, 58, 237, 0.08);
}
.report-success-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--primary);
}
.report-success-close {
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
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}
.report-success-close:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.08);
}
.report-success-body {
  padding: 1.25rem 1.25rem 1.5rem;
}
.report-success-msg {
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
  color: var(--text);
}
.report-success-hint {
  margin: 0 0 1.25rem 0;
  font-size: 0.875rem;
  color: var(--text-muted);
  line-height: 1.5;
}
.report-success-hint a {
  color: var(--accent);
  text-decoration: none;
}
.report-success-hint a:hover {
  text-decoration: underline;
}
.report-success-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-active .report-success-modal,
.modal-fade-leave-active .report-success-modal {
  transition: transform 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-from .report-success-modal,
.modal-fade-leave-to .report-success-modal {
  transform: scale(0.96);
}
</style>
