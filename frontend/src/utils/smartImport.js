import * as XLSX from 'xlsx'

/**
 * 解析 CSV 文本为带表头的行数据
 * @param {string} text - 原始文本（支持逗号、制表符分隔）
 * @returns {{ headers: string[], rows: Record<string, string>[] }}
 */
export function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter((line) => line.trim())
  if (lines.length === 0) return { headers: [], rows: [] }

  const sep = lines[0].includes('\t') ? '\t' : ','
  const parseLine = (line) => {
    const out = []
    let cur = ''
    let inQuote = false
    for (let i = 0; i < line.length; i++) {
      const c = line[i]
      if (c === '"') {
        inQuote = !inQuote
      } else if (c === sep && !inQuote) {
        out.push(cur.trim())
        cur = ''
      } else {
        cur += c
      }
    }
    out.push(cur.trim())
    return out
  }

  const rawRows = lines.map((line) => parseLine(line))
  const maxCols = Math.max(...rawRows.map((r) => r.length))
  const pad = (row) => (row.length >= maxCols ? row : [...row, ...Array(maxCols - row.length).fill('')])

  const first = pad(rawRows[0])
  const headers = first.map((h) => String(h || '').trim())
  const rows = rawRows.slice(1).map((row) => {
    const padded = pad(row)
    const obj = {}
    headers.forEach((h, i) => {
      if (h) obj[h] = String(padded[i] ?? '').trim()
    })
    return obj
  })
  return { headers, rows }
}

/**
 * 解析 Excel 文件（.xlsx / .xls）为带表头的行数据
 * @param {ArrayBuffer} arrayBuffer
 * @returns {{ headers: string[], rows: Record<string, string>[] }}
 */
export function parseExcel(arrayBuffer) {
  const wb = XLSX.read(arrayBuffer, { type: 'array', cellDates: false })
  const firstSheet = wb.SheetNames[0]
  if (!firstSheet) return { headers: [], rows: [] }
  const sheet = wb.Sheets[firstSheet]
  const data = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '', raw: false })
  if (!data.length) return { headers: [], rows: [] }

  const rawRows = data.map((row) => row.map((c) => (c != null ? String(c).trim() : '')))
  const maxCols = Math.max(...rawRows.map((r) => r.length))
  const pad = (row) => (row.length >= maxCols ? [...row] : [...row, ...Array(maxCols - row.length).fill('')])

  const first = pad(rawRows[0])
  const headers = first.map((h) => String(h || '').trim())
  const rows = rawRows.slice(1).map((row) => {
    const padded = pad(row)
    const obj = {}
    headers.forEach((h, i) => {
      if (h) obj[h] = String(padded[i] ?? '').trim()
    })
    return obj
  })
  return { headers, rows }
}

/**
 * 从行对象中按多种可能的列名取值（兼容中英文表头）
 * @param {Record<string, string>} row
 * @param {string[]} keys - 候选列名，按顺序尝试
 * @returns {string}
 */
export function getCell(row, keys) {
  for (const k of keys) {
    const v = row[k]
    if (v !== undefined && v !== null && String(v).trim() !== '') return String(v).trim()
  }
  return ''
}

/**
 * 从行对象中取数字
 */
export function getNum(row, keys, defaultValue = 0) {
  const s = getCell(row, keys)
  if (!s) return defaultValue
  const n = parseFloat(String(s).replace(/[^\d.-]/g, ''))
  return Number.isFinite(n) ? n : defaultValue
}

/**
 * 读取文件为文本
 */
export function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = () => reject(new Error('文件读取失败'))
    r.readAsText(file, 'UTF-8')
  })
}

/**
 * 读取文件为 ArrayBuffer（用于 Excel）
 */
export function readFileAsArrayBuffer(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = () => reject(new Error('文件读取失败'))
    r.readAsArrayBuffer(file)
  })
}
