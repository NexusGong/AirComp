<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="onCancel">
        <div class="modal-box" :class="{ 'modal-box--danger': danger }" role="dialog" aria-modal="true" :aria-labelledby="titleId">
          <div class="modal-header">
            <span :id="titleId" class="modal-title">{{ title }}</span>
          </div>
          <p class="modal-message">{{ message }}</p>
          <div class="modal-actions">
            <button type="button" class="btn modal-btn-cancel" @click="onCancel">
              {{ cancelText }}
            </button>
            <button type="button" class="btn modal-btn-confirm" :class="{ 'modal-btn-confirm--danger': danger }" @click="onConfirm">
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '确认' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])

const titleId = computed(() => 'modal-title-' + Math.random().toString(36).slice(2, 9))

function onConfirm() {
  emit('confirm')
}

function onCancel() {
  emit('cancel')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(6px);
}

.modal-box {
  width: 100%;
  max-width: 380px;
  background: var(--surface-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(124, 58, 237, 0.08);
  padding: 1.5rem 1.5rem 1.25rem;
}

.modal-box--danger .modal-header {
  border-bottom-color: rgba(239, 68, 68, 0.3);
}

.modal-box--danger .modal-title {
  color: var(--danger);
}

.modal-header {
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--primary);
}

.modal-message {
  font-size: 0.95rem;
  color: var(--text);
  line-height: 1.5;
  margin: 0 0 1.25rem 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.modal-btn-cancel {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.5rem 1.1rem;
  border-radius: var(--radius-sm);
}

.modal-btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
  border-color: var(--text-muted);
}

.modal-btn-confirm {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.modal-btn-confirm:hover {
  background: var(--primary-hover);
  box-shadow: 0 0 12px var(--primary-glow-soft);
}

.modal-btn-confirm--danger {
  background: var(--danger);
}

.modal-btn-confirm--danger:hover {
  background: var(--danger-hover);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.25);
}

/* 过渡 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-active .modal-box,
.modal-fade-leave-active .modal-box {
  transition: transform 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .modal-box,
.modal-fade-leave-to .modal-box {
  transform: scale(0.96);
}
</style>
