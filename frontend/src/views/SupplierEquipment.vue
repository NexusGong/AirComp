<template>
  <div>
    <template v-if="!supplierName">
      <p class="empty-hint">{{ props.embedded ? '请在上方选择供应商查看设备信息。' : '请从左侧侧边栏选择一个供应商查看其设备信息。' }}</p>
    </template>

    <template v-else>
      <p class="table-caption">该供应商下已录入的设备</p>

      <div class="table-responsive">
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
                <button type="button" class="btn btn-danger-tech btn-sm" @click="openDeleteConfirm(row.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="supplierList.length === 0" class="empty-hint">该供应商暂无设备，请先录入。</p>
      <div class="table-actions">
        <router-link :to="addSupplierLink" class="btn btn-acc">+ 录入该供应商设备</router-link>
      </div>
    </template>

    <ConfirmModal
      :visible="showConfirm"
      title="删除确认"
      message="确定要删除这条供应商设备记录吗？删除后无法恢复。"
      confirm-text="确定删除"
      cancel-text="取消"
      :danger="true"
      @confirm="doDelete"
      @cancel="showConfirm = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import ConfirmModal from '../components/ConfirmModal.vue'

const props = defineProps({
  supplier: { type: String, default: '' },
  embedded: { type: Boolean, default: false },
})

const route = useRoute()
const authStore = useAuthStore()
const supplierList = ref([])
const showConfirm = ref(false)
const pendingDeleteId = ref(null)

const supplierName = computed(() => (props.embedded ? props.supplier : (route.query.supplier || '')))

const supplierCols = ['编号', '型号', '额定功率', '气量', '品牌', '变频/工频', '额定压力', '比功率', '采集日期']

const addSupplierLink = computed(() => {
  if (route.path === '/equipment/suppliers') {
    return { path: '/equipment/suppliers', query: { view: 'add', ...(supplierName.value ? { supplier: supplierName.value } : {}) } }
  }
  return { path: '/add-supplier', query: supplierName.value ? { supplier: supplierName.value } : {} }
})

function toRow(r) {
  return {
    id: r.id,
    cells: [
      r.no, r.model, r.ori_power, r.air, r.brand,
      r.is_FC === 1 ? '变频' : '工频', r.origin_pre, r.energy_con,
      r.collect_time || '',
    ],
  }
}

async function load() {
  if (!supplierName.value) {
    supplierList.value = []
    return
  }
  try {
    const res = await api.get('machines/suppliers')
    const list = (res.data || []).filter((s) => s.name === supplierName.value)
    supplierList.value = list.map(toRow)
  } catch {
    supplierList.value = []
  }
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
  await api.delete(`machines/suppliers/${id}`)
  authStore.setFlash('已删除', 'success')
  load()
}

watch([() => supplierName.value], load, { immediate: true })
</script>
