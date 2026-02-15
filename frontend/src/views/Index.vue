<template>
  <div class="home-dialog">
    <div class="dialog-center">
      <h1 class="dialog-title">空压机能效计算系统</h1>
      <p class="dialog-subtitle">输入或选择要执行的操作</p>
      <div class="dialog-input-wrap">
        <input
          v-model="userInput"
          type="text"
          class="dialog-input"
          placeholder="例如：录入客户设备、查看某公司设备、数据与对比…"
          @keydown.enter="onSubmit"
        />
        <button type="button" class="dialog-send" @click="onSubmit" :aria-label="'发送'">
          <span class="send-icon">↵</span>
        </button>
      </div>
      <div class="dialog-quick">
        <span class="quick-label">快捷操作</span>
        <div class="quick-chips">
          <router-link to="/add-client" class="chip">录入客户设备信息</router-link>
          <router-link to="/add-supplier" class="chip">录入供应商设备信息</router-link>
          <router-link to="/data-process" class="chip">数据与对比</router-link>
          <router-link to="/equipment/clients" class="chip">按公司查看客户设备</router-link>
          <router-link to="/equipment/suppliers" class="chip">按供应商查看设备</router-link>
          <button type="button" class="chip chip-button" @click="goAnalysis">新建分析</button>
        </div>
      </div>
      <p class="dialog-hint">也可从左侧侧边栏选择公司或供应商查看、录入设备。</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const userInput = ref('')

function goAnalysis() {
  router.push({ name: 'analysis' })
}

function onSubmit() {
  const t = userInput.value.trim().toLowerCase()
  if (!t) return
  if (t.includes('客户') && (t.includes('录入') || t.includes('添加'))) router.push('/add-client')
  else if (t.includes('供应商') && (t.includes('录入') || t.includes('添加'))) router.push('/add-supplier')
  else if (t.includes('对比') || t.includes('数据')) router.push('/data-process')
  else if (t.includes('客户') && t.includes('查看')) router.push('/equipment/clients')
  else if (t.includes('供应商') && t.includes('查看')) router.push('/equipment/suppliers')
  else if (t.includes('分析') || t.includes('新建分析')) goAnalysis()
  else router.push('/data-process')
  userInput.value = ''
}
</script>

<style scoped>
.home-dialog {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
}

.dialog-center {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
}

.dialog-title {
  font-family: var(--font-head);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text);
  text-align: center;
  margin-bottom: 0.35rem;
}

.dialog-subtitle {
  font-size: 0.95rem;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 1.5rem;
}

.dialog-input-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.dialog-input-wrap:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-glow);
}

.dialog-input {
  flex: 1;
  background: none;
  border: none;
  color: var(--text);
  font-size: 1rem;
  outline: none;
}

.dialog-input::placeholder {
  color: var(--text-muted);
}

.dialog-send {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: opacity 0.2s, transform 0.2s;
}

.dialog-send:hover {
  opacity: 0.9;
  transform: scale(1.05);
}

.send-icon {
  font-size: 1.1rem;
  font-weight: 700;
}

.dialog-quick {
  margin-top: 1.5rem;
}

.quick-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  display: block;
  margin-bottom: 0.5rem;
}

.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chip {
  display: inline-block;
  padding: 0.4rem 0.85rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-muted);
  font-size: 0.875rem;
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.chip:hover,
.chip-button:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(124, 58, 237, 0.08);
}

.chip-button {
  appearance: none;
  font-family: var(--font) !important;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
}

.dialog-hint {
  margin-top: 1.25rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  text-align: center;
}
</style>
