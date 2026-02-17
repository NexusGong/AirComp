<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <img src="/logo.png" alt="AirComp" class="auth-logo" />
      </div>
      <h1 class="auth-title">登录 / 注册</h1>
      <p class="auth-subtitle">AirComp能耗计算系统</p>

      <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>

      <div class="auth-tabs">
        <button
          type="button"
          class="auth-tab"
          :class="{ active: authMode === 'sms' }"
          @click="authMode = 'sms'; errorMsg = ''; step = 1"
        >
          手机号
        </button>
        <button
          type="button"
          class="auth-tab"
          :class="{ active: authMode === 'password' }"
          @click="authMode = 'password'; errorMsg = ''"
        >
          密码登录
        </button>
      </div>

      <!-- 密码登录 -->
      <form v-if="authMode === 'password'" class="auth-form" @submit.prevent="onPasswordLogin">
        <div class="auth-field">
          <label class="auth-label">手机号或用户名</label>
          <input
            v-model="pwAccount"
            type="text"
            class="auth-input"
            required
            placeholder="请输入手机号或用户名"
            autocomplete="username"
          />
        </div>
        <div class="auth-field">
          <label class="auth-label">密码</label>
          <input
            v-model="pwPassword"
            type="password"
            class="auth-input"
            required
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </div>
        <button type="submit" class="auth-submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>

      <!-- 手机号：步骤 1 输入手机号 -->
      <div v-if="authMode === 'sms' && step === 1" class="auth-form">
        <div class="auth-field">
          <label class="auth-label">手机号</label>
          <input
            v-model="phone"
            type="tel"
            class="auth-input"
            maxlength="11"
            placeholder="11 位手机号"
            autocomplete="tel"
          />
        </div>
        <button
          type="button"
          class="auth-submit"
          :disabled="loading || !isPhoneValid"
          @click="onSendCode"
        >
          {{ loading ? '发送中…' : '获取验证码' }}
        </button>
      </div>

      <!-- 手机号：步骤 2 验证码 -->
      <div v-if="authMode === 'sms' && step === 2" class="auth-form">
        <p class="auth-hint">验证码已发送至 {{ phoneDisplay }}</p>
        <div class="auth-field">
          <label class="auth-label">验证码</label>
          <input
            ref="codeInputRef"
            v-model="code"
            type="text"
            class="auth-input auth-input-center"
            maxlength="6"
            placeholder="6 位数字"
            autocomplete="one-time-code"
            @input="onCodeInput"
          />
        </div>
        <div class="auth-actions">
          <button
            type="button"
            class="auth-link"
            :disabled="countdown > 0"
            @click="onResendCode"
          >
            {{ countdown > 0 ? `${countdown}s 后重发` : '重新发送' }}
          </button>
          <button type="button" class="auth-link" @click="step = 1; code = ''">更换手机号</button>
        </div>
        <button
          v-if="userExists"
          type="button"
          class="auth-submit"
          :disabled="loading || code.length !== 6"
          @click="onSmsLogin"
        >
          {{ loading ? '登录中…' : '登录' }}
        </button>
        <button
          v-else
          type="button"
          class="auth-submit"
          :disabled="loading || code.length !== 6"
          @click="step = 3"
        >
          下一步，设置昵称
        </button>
      </div>

      <!-- 手机号：步骤 3 注册昵称 -->
      <div v-if="authMode === 'sms' && step === 3" class="auth-form">
        <p class="auth-hint">验证码已发送至 {{ phoneDisplay }}</p>
        <div class="auth-field">
          <label class="auth-label">昵称（3–20 个字符）</label>
          <input
            v-model="username"
            type="text"
            class="auth-input"
            minlength="3"
            maxlength="20"
            placeholder="用于展示的名称"
          />
          <p v-if="username.length > 0 && (username.length < 3 || username.length > 20)" class="auth-err-text">昵称需 3–20 个字符</p>
        </div>
        <div class="auth-row">
          <button
            type="button"
            class="auth-submit"
            :disabled="loading || !isUsernameValid"
            @click="onSmsRegister"
          >
            {{ loading ? '注册中…' : '注册' }}
          </button>
          <button type="button" class="auth-secondary" @click="step = 2">上一步</button>
        </div>
      </div>

      <!-- 手机号：步骤 4 设置用户名与密码 -->
      <div v-if="authMode === 'sms' && step === 4" class="auth-form">
        <p class="auth-hint success">注册成功，请设置用户名和密码，便于下次密码登录。</p>
        <div class="auth-field">
          <label class="auth-label">登录用户名（3–20 个字符）</label>
          <input
            v-model="setUsername"
            type="text"
            class="auth-input"
            minlength="3"
            maxlength="20"
            placeholder="用于登录的用户名"
          />
          <p v-if="setUsername.length > 0 && (setUsername.length < 3 || setUsername.length > 20)" class="auth-err-text">用户名需 3–20 个字符</p>
        </div>
        <div class="auth-field">
          <label class="auth-label">密码</label>
          <input
            v-model="setPassword"
            type="password"
            class="auth-input"
            minlength="4"
            placeholder="至少 4 位"
          />
        </div>
        <div class="auth-field">
          <label class="auth-label">确认密码</label>
          <input
            v-model="setPasswordConfirm"
            type="password"
            class="auth-input"
            placeholder="再次输入密码"
          />
          <p v-if="setPassword && setPassword !== setPasswordConfirm" class="auth-err-text">两次密码不一致</p>
        </div>
        <button
          type="button"
          class="auth-submit"
          :disabled="loading || !isSetPasswordValid"
          @click="onSetPassword"
        >
          {{ loading ? '设置中…' : '完成' }}
        </button>
      </div>

      <p class="auth-footer-hint">登录状态保持 7 天</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getApiErrorMessage } from '../utils/errorMessage'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const errorMsg = ref('')
const authMode = ref('sms')
const step = ref(1)
const phone = ref('')
const code = ref('')
const username = ref('')
const userExists = ref(false)
const countdown = ref(0)
const codeInputRef = ref(null)
const pwAccount = ref('')
const pwPassword = ref('')
const setUsername = ref('')
const setPassword = ref('')
const setPasswordConfirm = ref('')

const isPhoneValid = computed(() => /^1\d{10}$/.test(phone.value.replace(/\s/g, '')))
const phoneDisplay = computed(() => {
  const p = phone.value.replace(/\s/g, '')
  if (p.length < 11) return phone.value
  return `${p.slice(0, 3)} **** ${p.slice(-4)}`
})
const isUsernameValid = computed(() => {
  const u = username.value.trim()
  return u.length >= 3 && u.length <= 20
})
const isSetPasswordValid = computed(() => {
  const u = setUsername.value.trim()
  return u.length >= 3 && u.length <= 20 && setPassword.value.length >= 4 && setPassword.value === setPasswordConfirm.value
})

function startCountdown() {
  countdown.value = 60
  const t = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(t)
  }, 1000)
}

async function onPasswordLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.login(pwAccount.value, pwPassword.value)
    authStore.setFlash('欢迎回来！', 'success')
    router.push('/')
  } catch (e) {
    errorMsg.value = getApiErrorMessage(e, '登录失败')
  } finally {
    loading.value = false
  }
}

async function onSetPassword() {
  if (!isSetPasswordValid.value || loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.setPassword(setUsername.value.trim(), setPassword.value)
    await authStore.loadUser()
    authStore.setFlash('设置成功，下次可使用密码登录', 'success')
    router.push('/')
  } catch (e) {
    errorMsg.value = getApiErrorMessage(e, '设置失败')
  } finally {
    loading.value = false
  }
}

async function onSendCode() {
  if (!isPhoneValid.value || loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    const data = await authStore.sendSmsCode(phone.value.trim())
    userExists.value = data.user_exists
    step.value = 2
    code.value = ''
    startCountdown()
    await nextTick()
    codeInputRef.value?.focus()
  } catch (e) {
    errorMsg.value = getApiErrorMessage(e, '发送失败')
  } finally {
    loading.value = false
  }
}

function onCodeInput() {
  code.value = code.value.replace(/\D/g, '').slice(0, 6)
}

async function onResendCode() {
  if (countdown.value > 0) return
  await onSendCode()
}

async function onSmsLogin() {
  if (code.value.length !== 6 || loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.loginBySms(phone.value.trim(), code.value)
    authStore.setFlash('欢迎回来！', 'success')
    router.push('/')
  } catch (e) {
    errorMsg.value = getApiErrorMessage(e, '登录失败')
  } finally {
    loading.value = false
  }
}

async function onSmsRegister() {
  if (!isUsernameValid.value || loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.registerBySms(phone.value.trim(), code.value, username.value.trim())
    setUsername.value = authStore.user?.username ?? username.value.trim()
    setPassword.value = ''
    setPasswordConfirm.value = ''
    step.value = 4
  } catch (e) {
    errorMsg.value = getApiErrorMessage(e, '注册失败')
  } finally {
    loading.value = false
  }
}

watch(step, (s) => { if (s === 1) errorMsg.value = '' })
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 120px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}
.auth-card {
  width: 100%;
  max-width: 400px;
  background: linear-gradient(160deg, rgba(15, 15, 18, 0.95) 0%, rgba(24, 24, 28, 0.98) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 2rem;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(124, 58, 237, 0.08);
}
.auth-brand {
  text-align: center;
  margin-bottom: 1rem;
}
.auth-logo {
  height: 96px;
  width: auto;
  object-fit: contain;
}
.auth-title {
  margin: 0 0 0.25rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  text-align: center;
}
.auth-subtitle {
  margin: 0 0 1.5rem 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  text-align: center;
}
.auth-error {
  padding: 0.65rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-sm);
}
.auth-tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
  padding: 0.25rem;
  background: rgba(0, 0, 0, 0.35);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.auth-tab {
  flex: 1;
  padding: 0.6rem 1rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}
.auth-tab:hover {
  color: var(--text);
  background: rgba(124, 58, 237, 0.1);
}
.auth-tab.active {
  color: #fff;
  background: var(--primary);
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.35);
}
.auth-form {
  margin-bottom: 0.5rem;
}
.auth-field {
  margin-bottom: 1.1rem;
}
.auth-label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-muted);
}
.auth-input {
  width: 100%;
  padding: 0.7rem 1rem;
  font-size: 1rem;
  color: var(--text);
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.auth-input::placeholder {
  color: var(--text-muted);
  opacity: 0.8;
}
.auth-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
}
.auth-input-center {
  text-align: center;
  letter-spacing: 0.3em;
}
.auth-hint {
  margin: 0 0 1rem 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}
.auth-hint.success {
  color: var(--success);
}
.auth-err-text {
  margin: 0.35rem 0 0 0;
  font-size: 0.8rem;
  color: var(--danger);
}
.auth-submit {
  width: 100%;
  margin-top: 0.25rem;
  padding: 0.75rem 1.25rem;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  background: var(--primary);
  border: none;
  border-radius: var(--radius-sm);
  box-shadow: 0 2px 10px rgba(124, 58, 237, 0.3);
  cursor: pointer;
  transition: background 0.2s, transform 0.2s, box-shadow 0.2s;
}
.auth-submit:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
}
.auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.auth-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.auth-link {
  padding: 0.35rem 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}
.auth-link:hover:not(:disabled) {
  color: var(--primary);
}
.auth-link:disabled {
  cursor: not-allowed;
  opacity: 0.8;
}
.auth-row {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
.auth-row .auth-submit {
  flex: 1;
  margin-top: 0;
}
.auth-secondary {
  padding: 0.65rem 1.25rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-muted);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}
.auth-secondary:hover {
  color: var(--primary);
  border-color: var(--primary);
  background: rgba(124, 58, 237, 0.08);
}
.auth-footer-hint {
  margin: 1.25rem 0 0 0;
  padding-top: 1rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  text-align: center;
  border-top: 1px solid var(--border);
}
</style>
