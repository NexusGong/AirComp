<template>
  <div class="page-card equipment-page-wrap">
    <h1 class="page-title">供应商设备信息</h1>

    <div class="equipment-tabs">
      <button type="button" class="tab" :class="{ active: view === 'add' }" @click="switchView('add')">
        设备信息录入
      </button>
      <button type="button" class="tab" :class="{ active: view === 'list' }" @click="switchView('list')">
        查看信息
      </button>
    </div>

    <template v-if="view === 'add'">
      <AddSupplierEmbed />
    </template>

    <template v-else>
      <div class="equipment-card">
        <div class="filter-row">
          <label class="form-label">选择供应商</label>
          <select v-model="selectedSupplier" class="form-select">
            <option value="">请选择供应商</option>
            <option v-for="n in supplierNames" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>
      </div>
      <div class="equipment-card">
        <SupplierEquipmentEmbed :supplier="selectedSupplier" embedded />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AddSupplierEmbed from './AddSupplier.vue'
import SupplierEquipmentEmbed from './SupplierEquipment.vue'
import api from '../api'

const route = useRoute()
const router = useRouter()
const supplierNames = ref([])
const selectedSupplier = ref('')

const view = computed({
  get: () => (route.query.view === 'list' ? 'list' : 'add'),
  set: (v) => {
    const q = { ...route.query }
    if (v === 'list') q.view = 'list'
    else delete q.view
    router.replace({ path: '/equipment/suppliers', query: q })
  },
})

function switchView(v) {
  view.value = v
  if (v === 'list' && supplierNames.value.length > 0 && !selectedSupplier.value) {
    selectedSupplier.value = supplierNames.value[0]
  }
}

async function loadOptions() {
  try {
    const res = await api.get('machines/options')
    supplierNames.value = res.data.supplier_name || []
    if (route.query.supplier && supplierNames.value.includes(route.query.supplier)) {
      selectedSupplier.value = route.query.supplier
    } else if (view.value === 'list' && supplierNames.value.length > 0 && !selectedSupplier.value) {
      selectedSupplier.value = supplierNames.value[0]
    }
  } catch {
    supplierNames.value = []
  }
}

watch(selectedSupplier, (name) => {
  if (name && route.query.supplier !== name) {
    router.replace({ path: '/equipment/suppliers', query: { view: 'list', supplier: name } })
  }
})
watch(() => route.query.supplier, (supplier) => {
  if (supplier && supplier !== selectedSupplier.value) selectedSupplier.value = supplier
})

onMounted(() => {
  if (route.query.supplier) selectedSupplier.value = route.query.supplier
  loadOptions()
})
watch(() => route.path, loadOptions)
</script>
