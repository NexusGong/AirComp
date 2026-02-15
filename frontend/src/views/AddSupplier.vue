<template>
  <div class="equipment-card">
    <!-- 解析结果弹窗：与 tab 无关，解析成功即弹出，不填入手工表单 -->
    <div v-if="showParsedModal" class="parsed-modal-overlay" @click.self="closeParsedModal">
      <div class="parsed-modal" @click.stop>
        <div class="parsed-modal-header">
          <h3 class="parsed-modal-title">解析结果 · 共 {{ parsedRecords.length }} 条</h3>
          <button type="button" class="parsed-modal-close" aria-label="关闭" @click="closeParsedModal">×</button>
        </div>
        <p class="parsed-modal-hint">请核对并编辑下方供应商设备记录，可勾选要添加的条目，点击「确定添加」写入系统。</p>
        <div class="parsed-modal-body">
          <div class="parsed-table-wrap">
            <table class="parsed-table parsed-table-editable">
              <thead>
                <tr>
                  <th class="col-check"><input type="checkbox" :checked="allSelected" @change="toggleSelectAll" /></th>
                  <th>供应商/公司</th>
                  <th>编号</th>
                  <th>型号</th>
                  <th>功率</th>
                  <th>气量</th>
                  <th>比功率</th>
                  <th>品牌</th>
                  <th>变频</th>
                  <th>额定压力</th>
                  <th>采集日期</th>
                  <th class="col-action">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, idx) in parsedRecords" :key="idx">
                  <td class="col-check"><input type="checkbox" :checked="selectedIndexes.has(idx)" @change="toggleSelect(idx)" /></td>
                  <td><input v-model="r.name" type="text" class="parsed-cell-input" /></td>
                  <td><input v-model.number="r.no" type="number" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model="r.model" type="text" class="parsed-cell-input" /></td>
                  <td><input v-model.number="r.ori_power" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model.number="r.air" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model.number="r.energy_con" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td>
                    <select v-model="r.brand" class="parsed-cell-select">
                      <option v-for="b in brands" :key="b" :value="b">{{ b }}</option>
                    </select>
                  </td>
                  <td>
                    <select v-model="r.is_FC" class="parsed-cell-select">
                      <option :value="true">是</option>
                      <option :value="false">否</option>
                    </select>
                  </td>
                  <td><input v-model.number="r.origin_pre" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model="r.collect_time" type="date" class="parsed-cell-input" /></td>
                  <td class="col-action">
                    <button type="button" class="btn-parsed-del" @click="removeParsedRow(idx)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="parsed-modal-footer">
          <button type="button" class="btn btn-acc" :disabled="batchLoading || selectedCount === 0" @click="batchAddSelected">
            {{ batchLoading ? '添加中…' : `确定添加（已选 ${selectedCount} 条）` }}
          </button>
          <button type="button" class="btn btn-ghost" @click="closeParsedModal">取消</button>
        </div>
      </div>
    </div>

    <p v-if="!embedded" class="table-caption">录入供应商设备信息</p>

    <div class="equipment-tabs">
      <button type="button" class="tab" :class="{ active: mode === 'manual' }" @click="mode = 'manual'">手工录入</button>
      <button type="button" class="tab" :class="{ active: mode === 'smart' }" @click="mode = 'smart'">智能录入</button>
    </div>

    <template v-if="mode === 'smart'">
      <div class="smart-entry-panel">
        <p class="smart-entry-heading">选择输入方式</p>
        <div class="smart-sub-tabs">
          <button type="button" class="tab" :class="{ active: smartSubMode === 'paste' }" @click="smartSubMode = 'paste'">
            <span class="tab-icon">📋</span>
            粘贴文本
          </button>
          <button type="button" class="tab" :class="{ active: smartSubMode === 'upload' }" @click="smartSubMode = 'upload'">
            <span class="tab-icon">📁</span>
            上传表格
          </button>
        </div>

        <div v-if="parseLoading" class="smart-parse-loading">
          <span class="smart-parse-spinner"></span>
          <span class="smart-parse-text">正在识别中，请稍候…</span>
        </div>

        <div v-if="smartSubMode === 'paste'" class="smart-input-block smart-input-paste">
          <p class="smart-input-desc">从 Excel 或文档中复制表格/文本，粘贴到下方。AI 将识别并提取多条供应商设备记录。</p>
          <textarea v-model="smartText" class="form-control smart-textarea" rows="6" placeholder="例如：&#10;供应商  B公司  编号  1  型号  YYY  额定功率  75  气量  12  比功率  6.2&#10;或粘贴多行表格内容"></textarea>
          <div class="smart-input-actions">
            <button type="button" class="btn btn-acc" :disabled="parseLoading" @click="parseSmartWithApi">
              {{ parseLoading ? '识别中…' : '解析并填入表单' }}
            </button>
          </div>
        </div>

        <div v-else class="smart-input-block smart-input-upload">
          <div
            class="upload-zone"
            :class="{ dragover: dragOver }"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="onDrop"
          >
            <span class="upload-icon">📤</span>
            <p class="upload-title">拖拽或点击上传 Excel / CSV 文件</p>
            <label class="upload-label">
              <input ref="fileInputRef" type="file" accept=".csv,.xlsx,.xls" @change="onFileSelect" />
              选择 Excel（.xlsx / .xls）或 CSV
            </label>
            <p class="upload-hint">支持 Excel（.xlsx、.xls）和 .csv；首行为表头，列名可与系统字段不同，AI 会自动从多列中抽取所需字段。</p>
            <div v-if="uploadFileName" class="upload-result">
              <span class="file-name">已选：{{ uploadFileName }}</span>
              <button type="button" class="btn btn-acc btn-sm" :disabled="parseLoading" @click="parseUploadedFileWithApi">
                {{ parseLoading ? '识别中…' : '解析并填入表单' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <form v-else @submit.prevent="onSubmit" class="form-grid-equipment">
      <span class="form-section-title">基本信息</span>
      <div class="form-group">
        <label class="form-label">公司名称</label>
        <input v-model="form.name" type="text" class="form-control" required />
      </div>
      <div class="form-group">
        <label class="form-label">机器编号</label>
        <input v-model.number="form.no" type="number" class="form-control" required />
      </div>
      <div class="form-group">
        <label class="form-label">机器型号</label>
        <input v-model="form.model" type="text" class="form-control" required />
      </div>

      <span class="form-section-title">能效参数</span>
      <div class="form-group">
        <label class="form-label">额定功率 (kW)</label>
        <input v-model.number="form.ori_power" type="number" step="0.01" class="form-control" required />
      </div>
      <div class="form-group">
        <label class="form-label">额定气量 (m³)</label>
        <input v-model.number="form.air" type="number" step="0.01" class="form-control" required />
      </div>
      <div class="form-group">
        <label class="form-label">比功率 (kW/m³)</label>
        <input v-model.number="form.energy_con" type="number" step="0.01" class="form-control" required />
      </div>

      <span class="form-section-title">设备属性</span>
      <div class="form-group">
        <label class="form-label">品牌</label>
        <select v-model="form.brand" class="form-select" required>
          <option v-for="b in brands" :key="b" :value="b">{{ b }}</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">是否变频</label>
        <select v-model="form.is_FC" class="form-select" required>
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">额定压力 (MPa)</label>
        <input v-model.number="form.origin_pre" type="number" step="0.01" class="form-control" required />
      </div>

      <span class="form-section-title">采集信息</span>
      <div class="form-group">
        <label class="form-label">采集日期</label>
        <input v-model="form.collect_time" type="date" class="form-control" required />
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-acc" :disabled="loading">提交</button>
        <router-link :to="returnLink" class="btn btn-ghost">返回</router-link>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import { parseCsv, parseExcel, readFileAsText, readFileAsArrayBuffer } from '../utils/smartImport'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const embedded = computed(() => route.path === '/equipment/suppliers')
const loading = ref(false)
const mode = ref('manual')
const smartSubMode = ref('paste')
const smartText = ref('')
const fileInputRef = ref(null)
const dragOver = ref(false)
const uploadFileName = ref('')
const uploadedRows = ref([])
const uploadedHeaders = ref([])
const parseLoading = ref(false)
const batchLoading = ref(false)
const showParsedModal = ref(false)
const parsedRecords = ref([])
const selectedIndexes = ref(new Set())
const brands = ['英格索兰', '阿特拉斯', '寿力', '凯撒', '捷豹', '开山', '复盛', '其他']
const form = reactive({
  name: '',
  no: 0,
  model: '',
  ori_power: 0,
  air: 0,
  brand: '阿特拉斯',
  is_FC: false,
  origin_pre: 0,
  energy_con: 0,
  collect_time: new Date().toISOString().slice(0, 10),
})

const returnLink = computed(() => {
  if (route.path === '/equipment/suppliers') {
    return { path: '/equipment/suppliers', query: { view: 'list', ...(form.name ? { supplier: form.name } : {}) } }
  }
  if (route.query.supplier) return { path: '/equipment/suppliers', query: { view: 'list', supplier: route.query.supplier } }
  return '/data-process'
})

const allSelected = computed(() => parsedRecords.value.length > 0 && selectedIndexes.value.size === parsedRecords.value.length)
const selectedCount = computed(() => {
  const n = selectedIndexes.value.size
  const total = parsedRecords.value.length
  return n > 0 ? n : total
})
function toggleSelectAll() {
  if (selectedIndexes.value.size === parsedRecords.value.length) {
    selectedIndexes.value = new Set()
  } else {
    selectedIndexes.value = new Set(parsedRecords.value.map((_, i) => i))
  }
}
function toggleSelect(idx) {
  const next = new Set(selectedIndexes.value)
  if (next.has(idx)) next.delete(idx)
  else next.add(idx)
  selectedIndexes.value = next
}

onMounted(() => {
  if (route.query.supplier) form.name = route.query.supplier
})

async function parseSmartWithApi() {
  const text = smartText.value?.trim()
  if (!text) {
    authStore.setFlash('请先粘贴文本', 'danger')
    return
  }
  parseLoading.value = true
  parsedRecords.value = []
  selectedIndexes.value = new Set()
  try {
    const { data } = await api.post('machines/smart-parse-supplier', { text }, { timeout: 70000 })
    const records = data?.records || []
    if (records.length === 0) {
      authStore.setFlash('未识别到供应商设备记录，请调整文本后重试', 'warning')
      return
    }
    parsedRecords.value = records
    selectedIndexes.value = new Set(records.map((_, i) => i))
    showParsedModal.value = true
    authStore.setFlash(`已识别 ${records.length} 条记录，请在弹出的窗口中核对并确定添加`, 'success')
  } catch (e) {
    const msg = e.response?.data?.detail ?? (e.code === 'ECONNABORTED' ? '请求超时，请检查网络或稍后重试' : e.message || 'AI 解析失败')
    authStore.setFlash(msg, 'danger')
  } finally {
    parseLoading.value = false
  }
}

function tableToText(headers, rows) {
  const line = (row) => headers.map((h) => row[h] ?? '').join('\t')
  return [headers.join('\t'), ...rows.map(line)].join('\n')
}

async function parseUploadedFileWithApi() {
  const rows = uploadedRows.value
  const headers = uploadedHeaders.value.length ? uploadedHeaders.value : (rows[0] ? Object.keys(rows[0]) : [])
  if (!rows?.length || !headers.length) {
    authStore.setFlash('请先选择并解析文件', 'danger')
    return
  }
  const text = tableToText(headers, rows)
  parseLoading.value = true
  parsedRecords.value = []
  selectedIndexes.value = new Set()
  try {
    const { data } = await api.post('machines/smart-parse-supplier', { text }, { timeout: 70000 })
    const records = data?.records || []
    if (records.length === 0) {
      authStore.setFlash('未识别到供应商设备记录，请检查表头与内容', 'warning')
      return
    }
    parsedRecords.value = records
    selectedIndexes.value = new Set(records.map((_, i) => i))
    showParsedModal.value = true
    authStore.setFlash(`已识别 ${records.length} 条记录，请在弹出的窗口中核对并确定添加`, 'success')
  } catch (e) {
    const msg = e.response?.data?.detail ?? (e.code === 'ECONNABORTED' ? '请求超时，请检查网络或稍后重试' : e.message || 'AI 解析失败')
    authStore.setFlash(msg, 'danger')
  } finally {
    parseLoading.value = false
  }
}

function closeParsedModal() {
  showParsedModal.value = false
  parsedRecords.value = []
  selectedIndexes.value = new Set()
}

function removeParsedRow(idx) {
  parsedRecords.value = parsedRecords.value.filter((_, i) => i !== idx)
  const next = new Set()
  selectedIndexes.value.forEach((i) => {
    if (i < idx) next.add(i)
    else if (i > idx) next.add(i - 1)
  })
  selectedIndexes.value = next
  if (parsedRecords.value.length === 0) showParsedModal.value = false
}

function getItemsToAdd() {
  const list = parsedRecords.value
  const indexes = selectedIndexes.value.size ? selectedIndexes.value : new Set(list.map((_, i) => i))
  return list.filter((_, i) => indexes.has(i))
}

async function batchAddSelected() {
  const items = getItemsToAdd()
  if (!items.length) {
    authStore.setFlash('请至少勾选一条记录', 'danger')
    return
  }
  const payload = items.map((r) => ({
    name: r.name,
    no: Number(r.no) || 0,
    model: r.model || '',
    ori_power: Number(r.ori_power) || 0,
    air: Number(r.air) || 0,
    brand: r.brand || '其他',
    is_FC: !!r.is_FC,
    origin_pre: Number(r.origin_pre) || 0.8,
    energy_con: Number(r.energy_con) || 0,
    collect_time: (r.collect_time || new Date().toISOString().slice(0, 10)).toString().slice(0, 10),
  }))
  batchLoading.value = true
  try {
    const { data } = await api.post('machines/suppliers/batch', { items: payload })
    authStore.setFlash(`成功添加 ${data.created} 条，跳过 ${data.skipped} 条已存在`, 'success')
    showParsedModal.value = false
    parsedRecords.value = []
    selectedIndexes.value = new Set()
    router.push(returnLink.value)
  } catch (e) {
    authStore.setFlash(e.response?.data?.detail || '批量添加失败', 'danger')
  } finally {
    batchLoading.value = false
  }
}

function onFileSelect(e) {
  const file = e.target.files?.[0]
  if (!file) return
  handleFile(file)
  e.target.value = ''
}

function onDrop(e) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  const ext = (file.name || '').toLowerCase()
  if (!['.csv', '.xlsx', '.xls'].some((x) => ext.endsWith(x))) {
    authStore.setFlash('请上传 .csv、.xlsx 或 .xls 文件', 'danger')
    return
  }
  handleFile(file)
}

async function handleFile(file) {
  uploadFileName.value = file.name
  const ext = (file.name || '').toLowerCase()
  try {
    if (ext.endsWith('.csv')) {
      const text = await readFileAsText(file)
      const { headers, rows } = parseCsv(text)
      uploadedHeaders.value = headers
      uploadedRows.value = rows
    } else {
      const ab = await readFileAsArrayBuffer(file)
      const { headers, rows } = parseExcel(ab)
      uploadedHeaders.value = headers
      uploadedRows.value = rows
    }
    if (uploadedRows.value.length > 0) {
      authStore.setFlash('已解析表格，点击「解析并填入表单」识别设备', 'success')
    } else {
      authStore.setFlash('未解析到数据行，请检查表头与内容', 'danger')
    }
  } catch (err) {
    authStore.setFlash(err?.message || '文件解析失败', 'danger')
    uploadedRows.value = []
    uploadedHeaders.value = []
  }
}

async function onSubmit() {
  loading.value = true
  try {
    await api.post('machines/suppliers', { ...form, is_FC: !!form.is_FC })
    authStore.setFlash('添加成功', 'success')
    router.push(returnLink.value)
  } catch (e) {
    authStore.setFlash(e.response?.data?.detail || '添加失败', 'danger')
  } finally {
    loading.value = false
  }
}
</script>
