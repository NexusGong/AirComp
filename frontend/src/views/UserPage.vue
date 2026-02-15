<template>
  <div class="page-card" v-if="data">
    <h1 class="page-title">用户：{{ data.user.username }}</h1>
    <ul class="list-group list-group-flush">
      <li v-for="p in data.posts" :key="p.id" class="list-group-item list-group-item-tech">
        {{ p.body }}
        <small class="text-muted ms-2">{{ formatTime(p.timestamp) }}</small>
      </li>
    </ul>
  </div>
  <div v-else class="page-card">
    <p class="text-muted mb-0">加载中…</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const data = ref(null)

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('zh-CN')
}

onMounted(async () => {
  const username = route.params.username
  const res = await api.get(`posts/user/${username}`, { params: { page: 1, per_page: 10 } })
  data.value = res.data
})
</script>

<style scoped>
.list-group-item-tech { border-radius: var(--radius) !important; }
.text-muted { color: var(--text-muted) !important; }
</style>
