import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

const TOKEN_KEY = 'aircomp_token'
const USER_KEY = 'aircomp_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY))
  const user = ref(null)
  const userJson = localStorage.getItem(USER_KEY)
  if (userJson) {
    try {
      user.value = JSON.parse(userJson)
    } catch (_) {}
  }

  const flash = ref({ message: '', class: 'alert-info' })

  const isLoggedIn = computed(() => !!token.value)

  function setFlash(msg, type = 'info') {
    const cls = type === 'success' ? 'alert-success' : type === 'danger' ? 'alert-danger' : 'alert-info'
    flash.value = { message: msg, class: cls }
  }

  function clearFlash() {
    flash.value = { message: '', class: 'alert-info' }
  }

  async function loadUser() {
    if (!token.value) return
    try {
      const res = await api.get('auth/me')
      user.value = res.data
      localStorage.setItem(USER_KEY, JSON.stringify(res.data))
    } catch (_) {
      token.value = null
      user.value = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  }

  /** 手机号或用户名 + 密码登录 */
  async function login(account, password) {
    const res = await api.post('auth/login', { account: account.trim(), password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem(TOKEN_KEY, res.data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.data.user))
    return res.data
  }

  /** 设置/修改密码（可选同时设置用户名，如注册后设置） */
  async function setPassword(usernameOrNull, password) {
    const body = usernameOrNull != null && usernameOrNull !== '' ? { username: usernameOrNull.trim(), password } : { password }
    await api.post('auth/set-password', body)
  }

  /** 更新个人资料（用户名、头像） */
  async function updateProfile(username, avatarImg = null) {
    const body = { username: username.trim() }
    if (avatarImg != null) body.avatar_img = avatarImg
    const res = await api.patch('auth/me', body)
    user.value = res.data
    localStorage.setItem(USER_KEY, JSON.stringify(res.data))
  }

  async function register(username, password) {
    const res = await api.post('auth/register', { username, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem(TOKEN_KEY, res.data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.data.user))
    return res.data
  }

  /** 发送验证码，返回 { message, user_exists } */
  async function sendSmsCode(phone) {
    const res = await api.post('auth/sms/send', { phone })
    return res.data
  }

  /** 验证码登录 */
  async function loginBySms(phone, code) {
    const res = await api.post('auth/sms/login', { phone, code })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem(TOKEN_KEY, res.data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.data.user))
    return res.data
  }

  /** 验证码注册 */
  async function registerBySms(phone, code, username) {
    const res = await api.post('auth/sms/register', { phone, code, username })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem(TOKEN_KEY, res.data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.data.user))
    return res.data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return {
    token,
    user,
    flash,
    isLoggedIn,
    setFlash,
    clearFlash,
    loadUser,
    login,
    register,
    setPassword,
    updateProfile,
    sendSmsCode,
    loginBySms,
    registerBySms,
    logout,
  }
})
