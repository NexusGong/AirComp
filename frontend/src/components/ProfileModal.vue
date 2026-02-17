<template>
  <Transition name="modal-fade">
    <div v-if="visible" class="user-modal-overlay" @click.self="$emit('close')">
      <div class="user-modal" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title" @click.stop>
        <div class="user-modal-header">
          <h2 id="profile-modal-title" class="user-modal-title">个人资料</h2>
          <button type="button" class="user-modal-close" aria-label="关闭" @click="$emit('close')">×</button>
        </div>
        <div class="user-modal-body">
          <template v-if="authStore.user">
            <div class="user-modal-field">
              <span class="user-modal-label">头像</span>
              <div class="avatar-picker">
                <button
                  v-for="av in DEFAULT_AVATARS"
                  :key="av"
                  type="button"
                  class="avatar-option avatar-option-emoji"
                  :class="{ selected: selectedAvatar === av }"
                  :aria-pressed="selectedAvatar === av"
                  @click="selectedAvatar = av"
                >
                  <span class="avatar-emoji">{{ av }}</span>
                </button>
              </div>
            </div>
            <label class="user-modal-field">
              <span class="user-modal-label">用户名</span>
              <input
                v-model="username"
                type="text"
                class="user-modal-input"
                placeholder="3–20 个字符"
                maxlength="20"
              />
            </label>
            <div v-if="authStore.user.phone" class="user-modal-field user-modal-field-readonly">
              <span class="user-modal-label">手机号</span>
              <span class="user-modal-value">{{ maskPhone(authStore.user.phone) }}</span>
            </div>
            <p v-if="errorMsg" class="user-modal-error">{{ errorMsg }}</p>
          </template>
          <p v-else class="user-modal-loading">加载中…</p>
        </div>
        <div class="user-modal-footer">
          <button type="button" class="btn btn-ghost" @click="$emit('close')">取消</button>
          <button type="button" class="btn btn-acc" :disabled="loading || !isValid" @click="onSave">
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

const DEFAULT_AVATARS = ['😊', '😎', '🥳', '🤗', '🧑', '👩', '👨', '✨']

defineProps({ visible: Boolean })
const emit = defineEmits(['close'])

const authStore = useAuthStore()
const username = ref(authStore.user?.username ?? '')
const selectedAvatar = ref(authStore.user?.avatar_img ?? DEFAULT_AVATARS[0])
const errorMsg = ref('')
const loading = ref(false)

watch(() => authStore.user, (u) => {
  if (u) {
    username.value = u.username
    selectedAvatar.value = (u.avatar_img && DEFAULT_AVATARS.includes(u.avatar_img)) ? u.avatar_img : DEFAULT_AVATARS[0]
  }
}, { immediate: true })

const isValid = computed(() => {
  const u = username.value.trim()
  return u.length >= 3 && u.length <= 20
})

function maskPhone(phone) {
  if (!phone || phone.length < 11) return phone
  return phone.slice(0, 3) + '****' + phone.slice(7)
}

async function onSave() {
  if (!isValid.value || loading.value) return
  const u = username.value.trim()
  const avatar = selectedAvatar.value
  const sameName = u === authStore.user?.username
  const sameAvatar = avatar === (authStore.user?.avatar_img || DEFAULT_AVATARS[0])
  if (sameName && sameAvatar) {
    emit('close')
    return
  }
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.updateProfile(u, avatar)
    authStore.setFlash('个人资料已更新', 'success')
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
.user-modal-field-readonly {
  margin-bottom: 0.5rem;
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
.user-modal-value {
  color: var(--text);
  font-weight: 500;
}
.user-modal-error {
  color: var(--danger);
  font-size: 0.9rem;
  margin: 0 0 0.5rem 0;
}
.user-modal-loading {
  color: var(--text-muted);
  margin: 0;
}

.avatar-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.avatar-option {
  width: 48px;
  height: 48px;
  padding: 0;
  border: 2px solid var(--border);
  border-radius: 50%;
  background: none;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.avatar-option:hover {
  border-color: var(--accent);
}

.avatar-option.selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3);
}

.avatar-option img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-option-emoji .avatar-emoji {
  font-size: 1.75rem;
  line-height: 1;
  display: block;
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
