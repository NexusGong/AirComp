/**
 * 从 axios 错误中取出可展示给用户的消息
 * 兼容 FastAPI 400 的 detail 字符串 与 422 的 detail 数组
 */
export function getApiErrorMessage(err, fallback = '请求失败') {
  if (!err || !err.response) return err?.message || fallback
  const d = err.response.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) return d.map((x) => x.msg || JSON.stringify(x)).join('；')
  return fallback
}
