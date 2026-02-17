<template>
  <Transition name="modal-fade">
    <div v-if="visible" class="user-modal-overlay" @click.self="$emit('close')">
      <div class="user-modal" role="dialog" aria-modal="true" aria-labelledby="perms-modal-title" @click.stop>
        <div class="user-modal-header">
          <h2 id="perms-modal-title" class="user-modal-title">账号权限</h2>
          <button type="button" class="user-modal-close" aria-label="关闭" @click="$emit('close')">×</button>
        </div>
        <div class="user-modal-body">
          <template v-if="authStore.user">
            <div class="user-modal-field user-modal-field-readonly">
              <span class="user-modal-label">用户名</span>
              <span class="user-modal-value">{{ authStore.user.username }}</span>
            </div>
            <div class="user-modal-field user-modal-field-readonly">
              <span class="user-modal-label">角色</span>
              <span class="user-modal-value">普通用户</span>
            </div>
            <p class="user-modal-desc">您可以使用能耗计算、设备信息、历史报告、新建对话等全部功能。如需更高权限请联系管理员。</p>
          </template>
          <p v-else class="user-modal-loading">加载中…</p>
        </div>
        <div class="user-modal-footer">
          <button type="button" class="btn btn-acc" @click="$emit('close')">知道了</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'

defineProps({ visible: Boolean })
defineEmits(['close'])

const authStore = useAuthStore()
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
.user-modal-value {
  color: var(--text);
  font-weight: 500;
}
.user-modal-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0.5rem 0 0 0;
}
.user-modal-loading {
  color: var(--text-muted);
  margin: 0;
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
