<template>
  <div class="page-card equipment-page-wrap">
    <h1 class="page-title">客户设备信息</h1>

    <div class="equipment-tabs">
      <button type="button" class="tab" :class="{ active: view === 'add' }" @click="switchView('add')">
        设备信息录入
      </button>
      <button type="button" class="tab" :class="{ active: view === 'list' }" @click="switchView('list')">
        查看信息
      </button>
    </div>

    <template v-if="view === 'add'">
      <AddClientEmbed />
    </template>

    <template v-else>
      <div class="equipment-card">
        <div class="filter-row">
          <label class="form-label">选择公司</label>
          <select v-model="selectedCompany" class="form-select">
            <option value="">请选择公司</option>
            <option v-for="n in companyNames" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>
      </div>
      <div class="equipment-card">
        <ClientEquipmentEmbed :company="selectedCompany" embedded />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AddClientEmbed from './AddClient.vue'
import ClientEquipmentEmbed from './ClientEquipment.vue'
import api from '../api'

const route = useRoute()
const router = useRouter()
const companyNames = ref([])
const selectedCompany = ref('')

const view = computed({
  get: () => (route.query.view === 'list' ? 'list' : 'add'),
  set: (v) => {
    const q = { ...route.query }
    if (v === 'list') q.view = 'list'
    else delete q.view
    router.replace({ path: '/equipment/clients', query: q })
  },
})

function switchView(v) {
  view.value = v
  if (v === 'list' && companyNames.value.length > 0 && !selectedCompany.value) {
    selectedCompany.value = companyNames.value[0]
  }
}

async function loadOptions() {
  try {
    const res = await api.get('machines/options')
    companyNames.value = res.data.company_name || []
    if (route.query.company && companyNames.value.includes(route.query.company)) {
      selectedCompany.value = route.query.company
    } else if (view.value === 'list' && companyNames.value.length > 0 && !selectedCompany.value) {
      selectedCompany.value = companyNames.value[0]
    }
  } catch {
    companyNames.value = []
  }
}

watch(selectedCompany, (name) => {
  if (name && route.query.company !== name) {
    router.replace({ path: '/equipment/clients', query: { view: 'list', company: name } })
  }
})
watch(() => route.query.company, (company) => {
  if (company && company !== selectedCompany.value) selectedCompany.value = company
})

onMounted(() => {
  if (route.query.company) selectedCompany.value = route.query.company
  loadOptions()
})
watch(() => route.path, loadOptions)
</script>
