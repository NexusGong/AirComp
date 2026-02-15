<template>
  <div>
    <template v-if="!companyName">
      <p class="empty-hint">{{ props.embedded ? '请在上方选择公司查看设备信息。' : '请从左侧侧边栏选择一家公司查看其设备信息。' }}</p>
    </template>

    <template v-else>
      <p class="table-caption">该公司下已录入的原有设备</p>

      <div class="table-responsive">
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
                <button type="button" class="btn btn-danger-tech btn-sm" @click="openDeleteConfirm(row.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="clientList.length === 0" class="empty-hint">该公司暂无设备，请先录入。</p>
      <div class="table-actions">
        <router-link :to="addClientLink" class="btn btn-acc">+ 录入该公司设备</router-link>
      </div>
    </template>

    <ConfirmModal
      :visible="showConfirm"
      title="删除确认"
      message="确定要删除这条客户设备记录吗？删除后无法恢复。"
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
  company: { type: String, default: '' },
  embedded: { type: Boolean, default: false },
})

const route = useRoute()
const authStore = useAuthStore()
const clientList = ref([])
const showConfirm = ref(false)
const pendingDeleteId = ref(null)

const companyName = computed(() => (props.embedded ? props.company : (route.query.company || '')))

const clientCols = ['编号', '型号', '运行时间', '加载时间', '额定功率', '气量', '品牌', '变频/工频', '额定压力', '实际压力', '采集日期']

const addClientLink = computed(() => {
  if (route.path === '/equipment/clients') {
    return { path: '/equipment/clients', query: { view: 'add', ...(companyName.value ? { company: companyName.value } : {}) } }
  }
  return { path: '/add-client', query: companyName.value ? { company: companyName.value } : {} }
})

function toRow(r) {
  return {
    id: r.id,
    cells: [
      r.no, r.model, r.run_time, r.load_time, r.ori_power, r.air, r.brand,
      r.is_FC === 1 ? '变频' : '工频', r.origin_pre, r.actual_pre,
      r.collect_time || '',
    ],
  }
}

async function load() {
  if (!companyName.value) {
    clientList.value = []
    return
  }
  try {
    const res = await api.get('machines/clients')
    const list = (res.data || []).filter((c) => c.name === companyName.value)
    clientList.value = list.map(toRow)
  } catch {
    clientList.value = []
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
  await api.delete(`machines/clients/${id}`)
  authStore.setFlash('已删除', 'success')
  load()
}

watch([() => companyName.value], load, { immediate: true })
</script>
