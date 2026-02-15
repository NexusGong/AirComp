import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'aircomp_analysis_list'

function loadList() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const list = raw ? JSON.parse(raw) : []
    return list.map((item) => {
      if (item.messages) return item
      if (item.content != null && item.content !== '') {
        return { ...item, messages: [{ role: 'user', content: item.content }] }
      }
      return { ...item, messages: item.messages || [] }
    })
  } catch {
    return []
  }
}

function saveList(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

function genId() {
  return 'a_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9)
}

function titleFromContent(content) {
  const t = (content || '').trim()
  const firstLine = t.split(/\n/)[0] || t
  return firstLine.slice(0, 28) || '未命名分析'
}

export const useAnalysisStore = defineStore('analysis', () => {
  const list = ref(loadList())

  const analysisList = computed(() => {
    return [...list.value]
      .filter((a) => (a.messages && a.messages.length > 0) || (a.content != null && String(a.content).trim() !== ''))
      .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
  })

  function save() {
    saveList(list.value)
  }

  /** 有内容时才创建并加入历史；返回新 id */
  function createFromFirstMessage(userContent) {
    const text = (userContent || '').trim()
    if (!text) return null
    const id = genId()
    const title = titleFromContent(text)
    const item = {
      id,
      title,
      createdAt: Date.now(),
      messages: [{ role: 'user', content: text }],
    }
    list.value.push(item)
    save()
    return id
  }

  function get(id) {
    return list.value.find((a) => a.id === id)
  }

  function appendMessage(id, role, content) {
    const item = list.value.find((a) => a.id === id)
    if (!item) return
    if (!item.messages) item.messages = []
    item.messages.push({ role, content: String(content || '').trim() })
    if (item.messages.length === 1) item.title = titleFromContent(content)
    save()
  }

  /** 追加同一条消息对象引用，用于选型/计算等需持久化 payload 的场景；与 appendMessage 二选一 */
  function pushMessage(id, message) {
    const item = list.value.find((a) => a.id === id)
    if (!item) return
    if (!item.messages) item.messages = []
    item.messages.push(message)
    if (item.messages.length === 1) item.title = titleFromContent(message.content)
    save()
  }

  function updateTitle(id, title) {
    const item = list.value.find((a) => a.id === id)
    if (item) {
      item.title = (title || '').trim() || '未命名分析'
      save()
    }
  }

  function updateSessionId(id, sessionId) {
    const item = list.value.find((a) => a.id === id)
    if (item) {
      item.sessionId = sessionId
      save()
    }
  }

  function remove(id) {
    list.value = list.value.filter((a) => a.id !== id)
    save()
  }

  return {
    list,
    analysisList,
    createFromFirstMessage,
    get,
    appendMessage,
    pushMessage,
    updateTitle,
    updateSessionId,
    remove,
    save,
  }
})
