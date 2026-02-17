<template>
  <Transition name="modal-fade">
    <div v-if="visible" class="user-modal-overlay" @click.self="$emit('close')">
      <div class="user-modal" role="dialog" aria-modal="true" aria-labelledby="password-modal-title" @click.stop>
        <div class="user-modal-header">
          <h2 id="password-modal-title" class="user-modal-title">修改密码</h2>
          <button type="button" class="user-modal-close" aria-label="关闭" @click="$emit('close')">×</button>
        </div>
        <form class="user-modal-body" @submit.prevent="onSubmit">
          <label class="user-modal-field">
            <span class="user-modal-label">新密码</span>
            <input
              v-model="password"
              type="password"
              class="user-modal-input"
              placeholder="至少 4 位"
              autocomplete="new-password"
            />
          </label>
          <label class="user-modal-field">
            <span class="user-modal-label">确认新密码</span>
            <input
              v-model="passwordConfirm"
              type="password"
              class="user-modal-input"
              placeholder="再次输入新密码"
              autocomplete="new-password"
            />
          </label>
          <p v-if="errorMsg" class="user-modal-error">{{ errorMsg }}</p>
        </form>
        <div class="user-modal-footer">
          <button type="button" class="btn btn-ghost" @click="$emit('close')">取消</button>
          <button type="button" class="btn btn-acc" :disabled="loading || !isValid" @click="onSubmit">
            {{ loading ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getApiErrorMessage } from '../utils/errorMessage'

defineProps({ visible: Boolean })
const emit = defineEmits(['close'])

const authStore = useAuthStore()
const password = ref('')
const passwordConfirm = ref('')
const errorMsg = ref('')
const loading = ref(false)

watch(() => password.value, () => { errorMsg.value = '' })
watch(() => passwordConfirm.value, () => { errorMsg.value = '' })

const isValid = computed(() => {
  return password.value.length >= 4 && password.value === passwordConfirm.value
})

async function onSubmit() {
  if (!isValid.value || loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.setPassword(null, password.value)
    await authStore.loadUser()
    authStore.setFlash('密码已更新', 'success')
    emit('close')
  } catch (e) {
    errorMsg.value = getApiErrorMessage(e, '保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.user-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.88);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}
.user-modal {
  width: 100%;
  max-width: 420px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}
.user-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}
.user-modal-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text);
}
.user-modal-close {
  width: 2rem;
  height: 2rem;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  border-radius: var(--radius-sm);
}
.user-modal-close:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.06);
}
.user-modal-body {
  padding: 1rem 1.25rem;
}
.user-modal-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1rem;
}
.user-modal-label {
  font-size: 0.9rem;
  color: var(--text-muted);
}
.user-modal-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-elevated);
  color: var(--text);
  font-size: 0.95rem;
}
.user-modal-input:focus {
  outline: none;
  border-color: var(--accent);
}
.user-modal-error {
  color: var(--danger);
  font-size: 0.9rem;
  margin: 0 0 0.5rem 0;
}
.user-modal-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border);
}
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .user-modal,
.modal-fade-leave-active .user-modal {
  transition: transform 0.2s ease;
}
.modal-fade-enter-from .user-modal,
.modal-fade-leave-to .user-modal {
  transform: translateY(-12px);
}
</style>
