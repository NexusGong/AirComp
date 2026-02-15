<template>
  <div class="page-card">
    <h1 class="page-title">数据与对比</h1>

    <p class="section-title">客户设备信息（原有设备）</p>
    <div class="table-responsive mb-4">
      <table class="table table-tech table-bordered table-sm">
        <thead>
          <tr>
            <th v-for="c in clientCols" :key="c">{{ c }}</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in clientList" :key="row.id">
            <td v-for="(v, i) in row.cells" :key="i">{{ v }}</td>
            <td>
              <router-link :to="`/data-modify/client/${row.id}`" class="btn btn-sm-acc me-1">修改</router-link>
              <button type="button" class="btn btn-danger-tech" @click="openDeleteConfirm('client', row.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="clientList.length === 0" class="text-muted small">暂无客户设备信息，请先 <router-link to="/add-client">录入客户设备信息</router-link>。</p>

    <p class="section-title">供应商设备信息</p>
    <div class="table-responsive mb-4">
      <table class="table table-tech table-bordered table-sm">
        <thead>
          <tr>
            <th v-for="c in supplierCols" :key="c">{{ c }}</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in supplierList" :key="row.id">
            <td v-for="(v, i) in row.cells" :key="i">{{ v }}</td>
            <td>
              <router-link :to="`/data-modify/supplier/${row.id}`" class="btn btn-sm-acc me-1">修改</router-link>
              <button type="button" class="btn btn-danger-tech" @click="openDeleteConfirm('supplier', row.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="supplierList.length === 0" class="text-muted small">暂无供应商设备信息，请先 <router-link to="/add-supplier">录入供应商设备信息</router-link>。</p>

    <hr class="divider-tech" />
    <p class="section-title">添加对比（将客户设备与供应商设备对应）</p>
    <form @submit.prevent="addCompare" class="row g-2 mb-4 compare-form">
      <div class="col-auto">
        <select v-model="compareForm.company_name" class="form-select form-select-sm" required>
          <option value="">客户公司</option>
          <option v-for="x in options.company_name" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <select v-model="compareForm.client_no" class="form-select form-select-sm" required>
          <option value="">客户机器编号</option>
          <option v-for="x in options.client_no" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <select v-model="compareForm.client_brand" class="form-select form-select-sm" required>
          <option value="">客户品牌</option>
          <option v-for="x in options.client_brand" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <select v-model="compareForm.client_model" class="form-select form-select-sm" required>
          <option value="">客户型号</option>
          <option v-for="x in options.client_model" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <select v-model="compareForm.supplier_name" class="form-select form-select-sm" required>
          <option value="">供应商</option>
          <option v-for="x in options.supplier_name" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <select v-model="compareForm.supplier_no" class="form-select form-select-sm" required>
          <option value="">供应商机器编号</option>
          <option v-for="x in options.supplier_no" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <select v-model="compareForm.supplier_brand" class="form-select form-select-sm" required>
          <option value="">供应商品牌</option>
          <option v-for="x in options.supplier_brand" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <select v-model="compareForm.supplier_model" class="form-select form-select-sm" required>
          <option value="">供应商型号</option>
          <option v-for="x in options.supplier_model" :key="x" :value="x">{{ x }}</option>
        </select>
      </div>
      <div class="col-auto">
        <button type="submit" class="btn btn-acc btn-sm">添加</button>
      </div>
    </form>

    <p class="section-title">对比列表（勾选后生成报表）</p>
    <form @submit.prevent="generate">
      <div class="table-responsive mb-3">
        <table class="table table-tech table-bordered table-sm">
          <thead>
            <tr>
              <th>客户公司</th>
              <th>客户编号</th>
              <th>客户品牌</th>
              <th>客户型号</th>
              <th>供应商</th>
              <th>供应商编号</th>
              <th>供应商品牌</th>
              <th>供应商型号</th>
              <th>操作</th>
              <th>勾选</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in compareList" :key="row.id">
              <td>{{ row.company_name }}</td>
              <td>{{ row.client_no }}</td>
              <td>{{ row.client_brand }}</td>
              <td>{{ row.client_model }}</td>
              <td>{{ row.supplier_name }}</td>
              <td>{{ row.supplier_no }}</td>
              <td>{{ row.supplier_brand }}</td>
              <td>{{ row.supplier_model }}</td>
              <td>
                <button type="button" class="btn btn-danger-tech" @click="openDeleteConfirm('compare', row.id)">删除</button>
              </td>
              <td>
                <input type="checkbox" :value="row.id" v-model="selectedCompareIds" class="form-check-input" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-muted small mb-3">勾选需要参与计算的对比项，点击生成文件。</p>
      <div class="d-flex flex-wrap gap-2 align-items-center">
        <button type="submit" class="btn btn-acc" :disabled="selectedCompareIds.length === 0 || generating">
          {{ generating ? '生成中…' : '生成 Excel' }}
        </button>
        <button v-if="lastFilename" type="button" class="btn btn-outline-acc" @click="doDownload">下载 {{ lastFilename }}</button>
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import ConfirmModal from '../components/ConfirmModal.vue'

const authStore = useAuthStore()
const clientList = ref([])
const supplierList = ref([])
const compareList = ref([])
const options = reactive({
  company_name: [],
  client_no: [],
  client_brand: [],
  client_model: [],
  supplier_name: [],
  supplier_no: [],
  supplier_brand: [],
  supplier_model: [],
})
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
const selectedCompareIds = ref([])
const generating = ref(false)
const lastFilename = ref('')
const showConfirm = ref(false)
const pendingDeleteType = ref(null)
const pendingDeleteId = ref(null)

const confirmTitle = computed(() => '删除确认')
const confirmMessage = computed(() => {
  const t = pendingDeleteType.value
  if (t === 'client') return '确定要删除这条客户设备记录吗？删除后无法恢复。'
  if (t === 'supplier') return '确定要删除这条供应商设备记录吗？删除后无法恢复。'
  if (t === 'compare') return '确定要删除这条对比关系吗？删除后无法恢复。'
  return '确定删除？'
})

const clientCols = ['ID', '用户ID', '公司名称', '编号', '型号', '运行时间', '加载时间', '额定功率', '气量', '品牌', '变频/工频', '额定压力', '实际压力', '采集日期', '录入时间']
const supplierCols = ['ID', '用户ID', '公司名称', '编号', '型号', '额定功率', '气量', '品牌', '变频/工频', '额定压力', '比功率', '单位能耗', '采集日期', '录入时间']

function toClientRow(r) {
  return {
    id: r.id,
    cells: [
      r.id, r.user_id, r.name, r.no, r.model, r.run_time, r.load_time, r.ori_power, r.air, r.brand,
      r.is_FC === 1 ? '变频' : '工频', r.origin_pre, r.actual_pre,
      r.collect_time, r.timestamp ? r.timestamp.slice(0, 19) : '',
    ],
  }
}
function toSupplierRow(r) {
  return {
    id: r.id,
    cells: [
      r.id, r.user_id, r.name, r.no, r.model, r.ori_power, r.air, r.brand,
      r.is_FC === 1 ? '变频' : '工频', r.origin_pre, r.energy_con, r.energy_con_min,
      r.collect_time, r.timestamp ? r.timestamp.slice(0, 19) : '',
    ],
  }
}

async function doDownload() {
  if (!lastFilename.value) return
  try {
    const res = await api.get('calculate/download', { params: { filename: lastFilename.value }, responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = lastFilename.value
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    authStore.setFlash('下载失败', 'danger')
  }
}

async function load() {
  const [clients, suppliers, compare, opts] = await Promise.all([
    api.get('machines/clients'),
    api.get('machines/suppliers'),
    api.get('machines/compare'),
    api.get('machines/options'),
  ])
  clientList.value = clients.data.map(toClientRow)
  supplierList.value = suppliers.data.map(toSupplierRow)
  compareList.value = compare.data
  Object.assign(options, opts.data)
}

function openDeleteConfirm(type, id) {
  pendingDeleteType.value = type
  pendingDeleteId.value = id
  showConfirm.value = true
}

async function doDelete() {
  const type = pendingDeleteType.value
  const id = pendingDeleteId.value
  showConfirm.value = false
  pendingDeleteType.value = null
  pendingDeleteId.value = null
  if (id == null) return
  if (type === 'client') await api.delete(`machines/clients/${id}`)
  else if (type === 'supplier') await api.delete(`machines/suppliers/${id}`)
  else await api.delete(`machines/compare/${id}`)
  authStore.setFlash('已删除', 'success')
  load()
}

async function addCompare() {
  await api.post('machines/compare', compareForm)
  authStore.setFlash('对比已添加', 'success')
  load()
}

async function generate() {
  if (selectedCompareIds.value.length === 0) return
  generating.value = true
  try {
    const res = await api.post('calculate', { compare_ids: selectedCompareIds.value })
    lastFilename.value = res.data.filename
    authStore.setFlash(res.data.message || '生成成功', 'success')
  } catch (e) {
    authStore.setFlash(e.response?.data?.detail || '生成失败', 'danger')
  } finally {
    generating.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.text-muted { color: var(--text-muted) !important; }
.compare-form .form-select { min-width: 120px; }
</style>
