<template>
  <div class="page-card equipment-page-wrap" v-if="form">
    <h1 class="page-title">修改客户设备信息</h1>

    <div class="equipment-card">
      <form @submit.prevent="onSubmit" class="form-grid-equipment">
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

        <span class="form-section-title">运行与能效</span>
        <div class="form-group">
          <label class="form-label">运行时间 (h)</label>
          <input v-model.number="form.run_time" type="number" class="form-control" />
        </div>
        <div class="form-group">
          <label class="form-label">加载时间 (h)</label>
          <input v-model.number="form.load_time" type="number" class="form-control" />
        </div>
        <div class="form-group">
          <label class="form-label">额定功率 (kW)</label>
          <input v-model.number="form.ori_power" type="number" step="0.01" class="form-control" required />
        </div>
        <div class="form-group">
          <label class="form-label">额定气量 (m³)</label>
          <input v-model.number="form.air" type="number" step="0.01" class="form-control" required />
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
        <div class="form-group">
          <label class="form-label">实际压力 (MPa)</label>
          <input v-model.number="form.actual_pre" type="number" step="0.01" class="form-control" required />
        </div>

        <span class="form-section-title">采集信息</span>
        <div class="form-group">
          <label class="form-label">数据记录日期</label>
          <input v-model="form.collect_time" type="date" class="form-control" required />
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-acc" :disabled="loading">保存</button>
          <router-link to="/data-process" class="btn btn-ghost">返回</router-link>
        </div>
      </form>
    </div>
  </div>
  <div v-else class="page-card">
    <p class="empty-hint mb-0">加载中…</p>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const brands = ['英格索兰', '阿特拉斯', '寿力', '凯撒', '捷豹', '开山', '复盛', '其他']
const form = ref(null)

onMounted(async () => {
  const id = route.params.id
  const res = await api.get(`machines/clients/${id}`)
  const r = res.data
  form.value = reactive({
    name: r.name,
    no: r.no,
    model: r.model,
    run_time: r.run_time ?? 0,
    load_time: r.load_time ?? 0,
    ori_power: r.ori_power ?? 0,
    air: r.air ?? 0,
    brand: r.brand || '阿特拉斯',
    is_FC: r.is_FC === 1,
    origin_pre: r.origin_pre ?? 0,
    actual_pre: r.actual_pre ?? 0,
    collect_time: r.collect_time ? r.collect_time.slice(0, 10) : new Date().toISOString().slice(0, 10),
  })
})

async function onSubmit() {
  if (!form.value) return
  loading.value = true
  try {
    await api.put(`machines/clients/${route.params.id}`, {
      ...form.value,
      is_FC: !!form.value.is_FC,
    })
    authStore.setFlash('已更新', 'success')
    router.push('/data-process')
  } catch (e) {
    authStore.setFlash(e.response?.data?.detail || '更新失败', 'danger')
  } finally {
    loading.value = false
  }
}
</script>
