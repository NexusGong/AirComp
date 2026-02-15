<template>
  <div class="chat-page">
    <div class="chat-main">
      <!-- 空状态：标题 + 输入框整体居中 -->
      <template v-if="messages.length === 0">
        <div class="chat-center">
          <div class="chat-welcome">
            <p class="chat-welcome-title">空压机能效分析</p>
            <p class="chat-welcome-desc">输入消息开始对话。可粘贴设备表格、上传文件，或直接描述需求（如计算某客户某几台机的节能量）。</p>
          </div>
          <div class="chat-input-wrap chat-input-wrap--center">
            <div class="chat-input-box">
              <textarea
                v-model="inputText"
                class="chat-input-area"
                placeholder="描述你想分析的内容 (Enter 发送，Shift+Enter 换行)"
                rows="3"
                @keydown.enter="onKeydownEnter"
              />
              <div v-if="attachment" class="chat-attachment">
                <span class="chat-attachment-name">已上传：{{ attachment.fileName }}</span>
                <button type="button" class="chat-attachment-remove" title="移除附件" aria-label="移除附件" @click="attachment = null">×</button>
              </div>
              <div class="chat-input-bar">
                <div class="chat-input-pills">
                  <span class="chat-pill chat-pill--active">文本</span>
                  <label class="chat-pill chat-pill-upload" title="上传表格">
                    <input ref="fileInputRef" type="file" accept=".csv,.xlsx,.xls" @change="onFileSelect" />
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
                    <span>上传表格</span>
                  </label>
                </div>
                <div class="chat-input-actions">
                  <span class="chat-input-sep"></span>
                  <button
                    v-if="sending || parseLoading"
                    type="button"
                    class="chat-btn-stop"
                    @click="abortRequest"
                    title="停止"
                    aria-label="停止请求"
                  >
                    停止
                  </button>
                  <button
                    type="button"
                    class="chat-send"
                    @click="onSend"
                    :disabled="(!inputText.trim() && !attachment) || sending || parseLoading"
                    title="发送"
                    aria-label="发送"
                  >
                    <span v-if="sending || parseLoading" class="chat-spinner"></span>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
                  </button>
                </div>
              </div>
              <p v-if="sending || parseLoading" class="chat-center-waiting">{{ parseLoading ? '正在识别设备信息…' : '正在分析…' }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- 有消息：对话列表 + 底部输入 -->
      <template v-else>
        <div class="chat-messages" ref="messagesEl">
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="chat-msg"
            :class="'chat-msg--' + msg.role"
          >
            <div class="chat-msg-avatar">
              <span v-if="msg.role === 'user'">我</span>
              <span v-else>助手</span>
            </div>
            <div class="chat-msg-body">
              <div v-if="msg.role === 'assistant' && isLastMsg(i) && !msg.content" class="chat-msg-waiting">
                <span class="chat-msg-waiting-dots">
                  <span></span><span></span><span></span>
                </span>
                <span class="chat-msg-waiting-text">{{ parseLoading ? '正在识别设备信息…' : (sending ? '正在分析…' : '正在思考…') }}</span>
              </div>
              <div v-else class="chat-msg-text">{{ msg.payload?.intent === 'run_energy_calculation' ? getEnergyCalcDisplayContent(msg) : msg.content }}</div>
              <template v-if="msg.role === 'assistant' && msg.payload?.intent === 'run_energy_calculation' && msg.payload?.company_name && !msg.payload?.selection_confirmed">
                <div class="chat-msg-caliber">
                  <span class="chat-msg-caliber-label">组合上限依据</span>
                  <div class="chat-msg-caliber-pills">
                    <button type="button" class="chat-caliber-pill" :class="{ 'chat-caliber-pill--on': getCaliberOn(msg, true) }" @click="setCaliberForMsg(msg, true)">实际用气量</button>
                    <button type="button" class="chat-caliber-pill" :class="{ 'chat-caliber-pill--on': getCaliberOn(msg, false) }" @click="setCaliberForMsg(msg, false)">额定用气量</button>
                  </div>
                </div>
                <div class="chat-msg-btns">
                  <button type="button" class="chat-btn chat-btn-primary" :disabled="recommendLoading" @click="onConfirmSelection(msg)">
                    {{ recommendLoading ? '获取中…' : '确认选型' }}
                  </button>
                </div>
              </template>
              <template v-else-if="msg.role === 'assistant' && msg.payload?.intent === 'run_energy_calculation' && msg.payload?.company_name && msg.payload?.selection_confirmed && !msg.payload?.filename">
                <div class="chat-msg-btns">
                  <button type="button" class="chat-btn chat-btn-secondary" @click="onResetSelection(msg)">重新选型</button>
                  <button type="button" class="chat-btn chat-btn-primary" :disabled="!canOpenParamsModal(msg)" @click="openParamsModal(msg)">
                    确认参数
                  </button>
                </div>
              </template>
              <template v-else-if="msg.role === 'assistant' && msg.payload?.intent === 'run_energy_calculation' && msg.payload?.company_name && msg.payload?.filename">
                <div v-if="msg.payload?.energy_savings_kwh != null" class="chat-msg-energy">
                  <span class="chat-msg-energy-label">节能量（年总节电）</span>
                  <span class="chat-msg-energy-value">{{ msg.payload.energy_savings_kwh.toLocaleString() }} kWh</span>
                  <template v-if="msg.payload?.energy_savings_cost != null">
                    <span class="chat-msg-energy-label">年节约电费</span>
                    <span class="chat-msg-energy-value">{{ msg.payload.energy_savings_cost.toLocaleString() }} 元</span>
                  </template>
                </div>
                <div class="chat-msg-btns">
                  <button type="button" class="chat-btn chat-btn-secondary" @click="onResetSelection(msg)">重新选型</button>
                  <button type="button" class="chat-btn chat-btn-primary" @click="doDownload(msg.payload.filename)">下载 Excel 报告</button>
                </div>
              </template>
            </div>
          </div>
        </div>

        <div v-if="parseLoading" class="chat-parse-hint">
          <span class="chat-parse-spinner"></span>
          <span>正在识别设备信息，请稍候…</span>
        </div>
        <div class="chat-input-wrap">
        <div class="chat-input-box">
          <textarea
            v-model="inputText"
            class="chat-input-area"
            placeholder="描述你想分析的内容 (Enter 发送，Shift+Enter 换行)"
            rows="3"
            @keydown.enter="onKeydownEnter"
          />
          <div v-if="attachment" class="chat-attachment">
            <span class="chat-attachment-name">已上传：{{ attachment.fileName }}</span>
            <button type="button" class="chat-attachment-remove" title="移除附件" aria-label="移除附件" @click="attachment = null">×</button>
          </div>
          <div class="chat-input-bar">
            <div class="chat-input-pills">
              <span class="chat-pill chat-pill--active">文本</span>
              <label class="chat-pill chat-pill-upload" title="上传表格">
                <input ref="fileInputRef" type="file" accept=".csv,.xlsx,.xls" @change="onFileSelect" />
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
                <span>上传表格</span>
              </label>
            </div>
            <div class="chat-input-actions">
              <span class="chat-input-sep"></span>
              <button
                v-if="sending || parseLoading"
                type="button"
                class="chat-btn-stop"
                @click="abortRequest"
                title="停止"
                aria-label="停止请求"
              >
                停止
              </button>
              <button
                type="button"
                class="chat-send"
                @click="onSend"
                :disabled="(!inputText.trim() && !attachment) || sending || parseLoading"
                title="发送"
                aria-label="发送"
              >
                <span v-if="sending || parseLoading" class="chat-spinner"></span>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
              </button>
            </div>
          </div>
        </div>
        </div>
      </template>
    </div>

    <!-- 解析结果弹窗：挂载到 body 避免被父级遮挡，与设备录入页一致 -->
    <Teleport to="body">
      <div v-if="showParsedModal" class="parsed-modal-overlay" @click.self="closeParsedModal">
      <div class="parsed-modal" @click.stop>
        <div class="parsed-modal-header">
          <h3 class="parsed-modal-title">{{ parsedType === 'supplier' ? '供应商' : '客户' }}设备解析结果 · 共 {{ parsedRecords.length }} 条</h3>
          <button type="button" class="parsed-modal-close" aria-label="关闭" @click="onParsedModalCancel">×</button>
        </div>
        <p class="parsed-modal-target" :class="parsedType === 'supplier' ? 'parsed-modal-target--supplier' : 'parsed-modal-target--client'">
          {{ parsedType === 'supplier' ? '将写入【供应商设备】' : '将写入【客户设备】' }}
        </p>
        <p class="parsed-modal-hint">请核对并编辑下方记录，可勾选要添加的条目，点击下方按钮写入对应模块。</p>
        <div class="parsed-modal-body">
          <div class="parsed-table-wrap">
            <!-- 客户设备 -->
            <table v-if="parsedType === 'client'" class="parsed-table parsed-table-editable">
              <thead>
                <tr>
                  <th class="col-check"><input type="checkbox" :checked="allSelected" @change="toggleSelectAll" /></th>
                  <th>公司名称</th>
                  <th>编号</th>
                  <th>型号</th>
                  <th>功率</th>
                  <th>气量</th>
                  <th>品牌</th>
                  <th>变频</th>
                  <th>额定压力</th>
                  <th>实际压力</th>
                  <th>采集日期</th>
                  <th class="col-action">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, idx) in parsedRecords" :key="idx">
                  <td class="col-check"><input type="checkbox" :checked="selectedIndexes.has(idx)" @change="toggleSelect(idx)" /></td>
                  <td><input v-model="r.name" type="text" class="parsed-cell-input" /></td>
                  <td><input v-model.number="r.no" type="number" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model="r.model" type="text" class="parsed-cell-input" /></td>
                  <td><input v-model.number="r.ori_power" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model.number="r.air" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td>
                    <select v-model="r.brand" class="parsed-cell-select">
                      <option v-for="b in brands" :key="b" :value="b">{{ b }}</option>
                    </select>
                  </td>
                  <td>
                    <select v-model="r.is_FC" class="parsed-cell-select">
                      <option :value="true">是</option>
                      <option :value="false">否</option>
                    </select>
                  </td>
                  <td><input v-model.number="r.origin_pre" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model.number="r.actual_pre" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model="r.collect_time" type="date" class="parsed-cell-input" /></td>
                  <td class="col-action"><button type="button" class="btn-parsed-del" @click="removeParsedRow(idx)">删除</button></td>
                </tr>
              </tbody>
            </table>
            <!-- 供应商设备 -->
            <table v-else class="parsed-table parsed-table-editable">
              <thead>
                <tr>
                  <th class="col-check"><input type="checkbox" :checked="allSelected" @change="toggleSelectAll" /></th>
                  <th>供应商/公司</th>
                  <th>编号</th>
                  <th>型号</th>
                  <th>功率</th>
                  <th>气量</th>
                  <th>比功率</th>
                  <th>品牌</th>
                  <th>变频</th>
                  <th>额定压力</th>
                  <th>采集日期</th>
                  <th class="col-action">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, idx) in parsedRecords" :key="idx">
                  <td class="col-check"><input type="checkbox" :checked="selectedIndexes.has(idx)" @change="toggleSelect(idx)" /></td>
                  <td><input v-model="r.name" type="text" class="parsed-cell-input" /></td>
                  <td><input v-model.number="r.no" type="number" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model="r.model" type="text" class="parsed-cell-input" /></td>
                  <td><input v-model.number="r.ori_power" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model.number="r.air" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model.number="r.energy_con" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td>
                    <select v-model="r.brand" class="parsed-cell-select">
                      <option v-for="b in brands" :key="b" :value="b">{{ b }}</option>
                    </select>
                  </td>
                  <td>
                    <select v-model="r.is_FC" class="parsed-cell-select">
                      <option :value="true">是</option>
                      <option :value="false">否</option>
                    </select>
                  </td>
                  <td><input v-model.number="r.origin_pre" type="number" step="0.01" class="parsed-cell-input parsed-cell-num" /></td>
                  <td><input v-model="r.collect_time" type="date" class="parsed-cell-input" /></td>
                  <td class="col-action"><button type="button" class="btn-parsed-del" @click="removeParsedRow(idx)">删除</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="parsed-modal-footer">
          <button type="button" class="btn btn-acc" :disabled="batchLoading || selectedCount === 0" @click="batchAddSelected">
            {{ batchLoading ? '添加中…' : (parsedType === 'supplier' ? `确定添加为供应商设备（已选 ${selectedCount} 条）` : `确定添加为客户设备（已选 ${selectedCount} 条）`) }}
          </button>
          <button type="button" class="btn btn-ghost" @click="onParsedModalCancel">取消</button>
        </div>
      </div>
    </div>
    </Teleport>

    <!-- 确认参数弹窗：与项目解析弹窗风格一致 -->
    <Teleport to="body">
      <div v-if="showParamsModal" class="parsed-modal-overlay" @click.self="closeParamsModal">
        <div class="parsed-modal params-modal" @click.stop>
          <div class="parsed-modal-header">
            <h3 class="parsed-modal-title">确认计算参数</h3>
            <button type="button" class="parsed-modal-close" aria-label="关闭" @click="closeParamsModal">×</button>
          </div>
          <div class="parsed-modal-body params-modal-body">
            <section class="params-block params-block--global">
              <h3 class="params-block-title">全局计算参数</h3>
              <p class="params-block-desc">以下参数可按实际工况修改；变频加载比例、空载浪费系数、压降浪费系数由系统按公式计算，无需填写。</p>
              <div class="params-grid">
                <label class="params-field">
                  <span class="params-field-label">年运行时间（小时）</span>
                  <input v-model.number="paramsForm.running_hours_per_year" type="number" min="1" class="params-field-input" />
                  <span class="params-field-hint">用于折算年节电量，常用 8000</span>
                </label>
                <label class="params-field">
                  <span class="params-field-label">电费（元/kWh）</span>
                  <input v-model.number="paramsForm.electricity_price" type="number" min="0" step="0.01" class="params-field-input" placeholder="选填" />
                  <span class="params-field-hint">选填，用于计算年节约电费</span>
                </label>
                <label class="params-field">
                  <span class="params-field-label">服务系数默认值</span>
                  <input v-model.number="paramsForm.default_ser_p" type="number" min="0" step="0.01" class="params-field-input" placeholder="1.2" />
                  <span class="params-field-hint">未设则按品牌：阿特拉斯/凯撒 1.15，英格索兰 1.2，复盛 1.3</span>
                </label>
              </div>
            </section>

            <section class="params-block">
              <h3 class="params-block-title">原有设备（客户设备）</h3>
              <p class="params-block-desc">编号、型号、运行/加载时间、功率、气量、品牌、变频、额定/实际压力等，均参与能耗与比功率计算。</p>
              <div class="params-table-wrap">
                <table class="params-table">
                  <thead>
                    <tr>
                      <th>编号</th>
                      <th>型号</th>
                      <th>运行时间</th>
                      <th>加载时间</th>
                      <th>额定功率<br>(kW)</th>
                      <th>气量<br>(m³/min)</th>
                      <th>品牌</th>
                      <th>变频</th>
                      <th>额定压力<br>(MPa)</th>
                      <th>实际压力<br>(MPa)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in paramsForm.machines" :key="idx">
                      <td><input v-model.number="row.no" type="number" class="params-cell" /></td>
                      <td><input v-model="row.model" type="text" class="params-cell" /></td>
                      <td><input v-model.number="row.run_time" type="number" class="params-cell" /></td>
                      <td><input v-model.number="row.load_time" type="number" class="params-cell" /></td>
                      <td><input v-model.number="row.ori_power" type="number" class="params-cell" /></td>
                      <td><input v-model.number="row.air" type="number" step="0.01" class="params-cell" /></td>
                      <td><input v-model="row.brand" type="text" class="params-cell" /></td>
                      <td>
                        <select v-model="row.isFC" class="params-cell params-select">
                          <option :value="true">是</option>
                          <option :value="false">否</option>
                        </select>
                      </td>
                      <td><input v-model.number="row.origin_pre" type="number" step="0.01" class="params-cell" /></td>
                      <td><input v-model.number="row.actucal_pre" type="number" step="0.01" class="params-cell" /></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section class="params-block">
              <h3 class="params-block-title">选型设备（推荐新机）</h3>
              <p class="params-block-desc">品牌、型号、功率、气量、变频、比功率与均每立方耗电，用于与原有设备对比得出节能量。</p>
              <div class="params-table-wrap">
                <table class="params-table">
                  <thead>
                    <tr>
                      <th>品牌</th>
                      <th>型号</th>
                      <th>额定功率<br>(kW)</th>
                      <th>气量<br>(m³/min)</th>
                      <th>变频</th>
                      <th>比功率</th>
                      <th>均每立方耗电</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in paramsForm.new_eq" :key="idx">
                      <td><input v-model="row.brand" type="text" class="params-cell" /></td>
                      <td><input v-model="row.model" type="text" class="params-cell" /></td>
                      <td><input v-model.number="row.ori_power" type="number" class="params-cell" /></td>
                      <td><input v-model.number="row.air" type="number" step="0.01" class="params-cell" /></td>
                      <td>
                        <select v-model="row.isFC" class="params-cell params-select">
                          <option :value="true">是</option>
                          <option :value="false">否</option>
                        </select>
                      </td>
                      <td><input v-model.number="row.energy_con" type="number" step="0.01" class="params-cell" /></td>
                      <td><input v-model.number="row.energy_con_min" type="number" step="0.0001" class="params-cell" /></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>
          <div class="parsed-modal-footer">
            <button type="button" class="btn btn-acc" :disabled="paramsCalcLoading" @click="submitParamsCalculation">
              {{ paramsCalcLoading ? '计算中…' : '确认计算' }}
            </button>
            <button type="button" class="btn btn-ghost" @click="closeParamsModal">取消</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnalysisStore } from '../stores/analysis'
import api from '../api'
import { parseExcel, readFileAsText, readFileAsArrayBuffer } from '../utils/smartImport'

const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()

const messagesEl = ref(null)
const inputText = ref('')
const messages = ref([])
const currentId = ref(null)
const sending = ref(false)
const recommendLoading = ref(false)
const fileInputRef = ref(null)
/** 当前消息是否选中「实际用气量」（用于对话内组合上限依据展示） */
function getCaliberOn(msg, isActual) {
  if (!msg?.payload) return isActual === true
  const v = msg.payload.use_actual_flow
  return v === undefined ? isActual === true : v === isActual
}
function setCaliberForMsg(msg, isActual) {
  if (!msg) return
  if (!msg.payload) msg.payload = {}
  msg.payload.use_actual_flow = isActual
}
/** 选型/计算消息的展示文案：未完成计算时统一为「确认选型」/「确认参数」提示，避免旧文案「确认计算」造成歧义 */
function getEnergyCalcDisplayContent(msg) {
  const raw = msg?.content ?? ''
  if (!msg?.payload || msg.payload.intent !== 'run_energy_calculation' || msg.payload.filename) return raw
  const oldPhrase = '请点击「确认计算」生成节能方案与报告。'
  const newPhrase = '请先点击「确认选型」获取方案，再点击「确认参数」进行节能计算与报告生成。'
  if (raw.includes(oldPhrase)) return raw.replace(oldPhrase, newPhrase)
  return raw
}
const showParsedModal = ref(false)
const parsedRecords = ref([])
const parsedType = ref('client')
const selectedIndexes = ref(new Set())
const pendingSendText = ref('')
const parseLoading = ref(false)
const batchLoading = ref(false)
const brands = ['英格索兰', '阿特拉斯', '寿力', '凯撒', '捷豹', '开山', '复盛', '其他']
const abortControllerRef = ref(null)
/** 当前上传的表格附件（不写入输入框，发送时通过 attachments 传递） */
const attachment = ref(null)

function tableToText(headers, rows) {
  const line = (row) => headers.map((h) => row[h] ?? '').join('\t')
  return [headers.join('\t'), ...rows.map(line)].join('\n')
}

/** 上传表格：作为附件，不写入输入框；发送时随 message 一并传给后端 */
async function onFileSelect(e) {
  const file = e.target?.files?.[0]
  if (!file) return
  e.target.value = ''
  const name = (file.name || '').toLowerCase()
  let text = ''
  try {
    if (name.endsWith('.csv')) {
      text = await readFileAsText(file)
    } else if (name.endsWith('.xlsx') || name.endsWith('.xls')) {
      const buf = await readFileAsArrayBuffer(file)
      const { headers, rows } = parseExcel(buf)
      if (headers.length && rows.length) text = tableToText(headers, rows)
      else text = (await readFileAsText(file).catch(() => '')) || ''
    }
  } catch (_) {
    return
  }
  if (!(text && text.trim())) return
  attachment.value = { fileName: file.name, tableText: text }
}

function loadAnalysis(id) {
  const item = analysisStore.get(id)
  if (item) {
    currentId.value = id
    messages.value = Array.isArray(item.messages) ? [...item.messages] : []
  } else {
    currentId.value = null
    messages.value = []
  }
}

let scrollToBottomRafId = null
function scrollToBottom() {
  if (scrollToBottomRafId != null) return
  scrollToBottomRafId = requestAnimationFrame(() => {
    scrollToBottomRafId = null
    nextTick(() => {
      if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    })
  })
}

/** 流式回复节流：按帧合并 content 更新与滚动，避免卡顿 */
let streamContentBuffer = ''
let streamFlushRafId = null
function flushStreamContent(msg) {
  if (streamContentBuffer === '') return
  msg.content = (msg.content || '') + streamContentBuffer
  streamContentBuffer = ''
  commitLastMessageContent()
  scrollToBottom()
}
function appendStreamContent(msg, data) {
  streamContentBuffer += data
  if (streamFlushRafId == null) {
    streamFlushRafId = requestAnimationFrame(() => {
      streamFlushRafId = null
      flushStreamContent(msg)
    })
  }
}
function endStreamContent(msg) {
  if (streamFlushRafId != null) {
    cancelAnimationFrame(streamFlushRafId)
    streamFlushRafId = null
  }
  flushStreamContent(msg)
}

/** 强制把最后一条消息同步到响应式数组，避免直接改 plain 对象导致视图不更新 */
function commitLastMessageContent() {
  const last = messages.value.length - 1
  if (last >= 0) messages.value[last] = { ...messages.value[last] }
}

function isLastMsg(index) {
  return messages.value.length > 0 && index === messages.value.length - 1
}

function abortRequest() {
  abortControllerRef.value?.abort()
}

const allSelected = computed(() => parsedRecords.value.length > 0 && selectedIndexes.value.size === parsedRecords.value.length)
const selectedCount = computed(() => {
  const n = selectedIndexes.value.size
  const total = parsedRecords.value.length
  return n > 0 ? n : total
})
function toggleSelectAll() {
  if (selectedIndexes.value.size === parsedRecords.value.length) {
    selectedIndexes.value = new Set()
  } else {
    selectedIndexes.value = new Set(parsedRecords.value.map((_, i) => i))
  }
}
function toggleSelect(idx) {
  const next = new Set(selectedIndexes.value)
  if (next.has(idx)) next.delete(idx)
  else next.add(idx)
  selectedIndexes.value = next
}
function removeParsedRow(idx) {
  parsedRecords.value = parsedRecords.value.filter((_, i) => i !== idx)
  const next = new Set()
  selectedIndexes.value.forEach((i) => {
    if (i < idx) next.add(i)
    else if (i > idx) next.add(i - 1)
  })
  selectedIndexes.value = next
  if (parsedRecords.value.length === 0) showParsedModal.value = false
}
function getItemsToAdd() {
  const list = parsedRecords.value
  const indexes = selectedIndexes.value.size ? selectedIndexes.value : new Set(list.map((_, i) => i))
  return list.filter((_, i) => indexes.has(i))
}
function closeParsedModal() {
  showParsedModal.value = false
  parsedRecords.value = []
  selectedIndexes.value = new Set()
  if (currentId.value && route.params.id !== currentId.value) {
    router.replace({ path: '/analysis/' + currentId.value })
  }
}
async function onParsedModalCancel() {
  closeParsedModal()
  if (!pendingSendText.value) return
  const text = pendingSendText.value
  pendingSendText.value = ''
  sending.value = true
  const history = messages.value.slice(0, -1).map((m) => ({ role: m.role, content: m.content }))
  const sessionId = currentId.value ? analysisStore.get(currentId.value)?.sessionId : null
  const assistantMsg = { role: 'assistant', content: '', payload: undefined }
  messages.value.push(assistantMsg)
  if (currentId.value) {
    if (typeof analysisStore.pushMessage === 'function') analysisStore.pushMessage(currentId.value, assistantMsg)
    else analysisStore.appendMessage(currentId.value, 'assistant', '')
  }
  scrollToBottom()
  const baseURL = import.meta.env.VITE_API_BASE || '/api/'
  const url = (baseURL.replace(/\/$/, '') + '/analysis/chat').replace(/([^:]\/)\/+/g, '$1')
  const token = localStorage.getItem('aircomp_token')
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ message: text, session_id: sessionId ?? undefined, history }),
      credentials: 'include',
    })
    if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`)
    const data = await res.json()
    assistantMsg.content = data.reply ?? ''
    const payload = {}
    if (data.intent) payload.intent = data.intent
    if (data.company_name) payload.company_name = data.company_name
    if (data.client_nos) payload.client_nos = data.client_nos
    if (data.client_list) payload.client_list = data.client_list
    if (Object.keys(payload).length) assistantMsg.payload = payload
    if (currentId.value) {
      analysisStore.save()
      if (data.session_id != null) analysisStore.updateSessionId(currentId.value, data.session_id)
    }
    commitLastMessageContent()
    scrollToBottom()
  } catch (err) {
    assistantMsg.content = '抱歉：' + (err?.message ?? '请求失败')
    if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', assistantMsg.content)
    commitLastMessageContent()
    scrollToBottom()
  } finally {
    sending.value = false
  }
}
async function batchAddSelected() {
  const items = getItemsToAdd()
  if (!items.length) return
  const target = parsedType.value
  if (target !== 'client' && target !== 'supplier') return
  if (target === 'client') {
    const payload = items.map((r) => ({
      name: r.name,
      no: Number(r.no) || 0,
      model: r.model || '',
      run_time: Number(r.run_time) || 0,
      load_time: Number(r.load_time) || 0,
      ori_power: Number(r.ori_power) || 0,
      air: Number(r.air) || 0,
      brand: r.brand || '其他',
      is_FC: !!r.is_FC,
      origin_pre: Number(r.origin_pre) || 0.8,
      actual_pre: Number(r.actual_pre) != null ? Number(r.actual_pre) : (Number(r.origin_pre) || 0.8),
      collect_time: (r.collect_time || new Date().toISOString().slice(0, 10)).toString().slice(0, 10),
    }))
    batchLoading.value = true
    try {
      const { data } = await api.post('machines/clients/batch', { items: payload })
      const reply = `已录入 ${data.created} 条客户设备` + (data.skipped ? `，${data.skipped} 条已存在已跳过。` : '。') + ' 接下来可以进行能耗计算，请告诉我您要计算哪家客户的设备节能量。'
      const assistantMsg = { role: 'assistant', content: reply, payload: undefined }
      messages.value.push(assistantMsg)
      if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', reply)
      scrollToBottom()
      closeParsedModal()
    } catch (e) {
      const msg = e.response?.data?.detail || '批量添加失败'
      messages.value.push({ role: 'assistant', content: '添加失败：' + msg })
      if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', '添加失败：' + msg)
      scrollToBottom()
    } finally {
      batchLoading.value = false
    }
  } else if (target === 'supplier') {
    const payload = items.map((r) => ({
      name: r.name,
      no: Number(r.no) || 0,
      model: r.model || '',
      ori_power: Number(r.ori_power) || 0,
      air: Number(r.air) || 0,
      brand: r.brand || '其他',
      is_FC: !!r.is_FC,
      origin_pre: Number(r.origin_pre) || 0.8,
      energy_con: Number(r.energy_con) || 0,
      collect_time: (r.collect_time || new Date().toISOString().slice(0, 10)).toString().slice(0, 10),
    }))
    batchLoading.value = true
    try {
      const { data } = await api.post('machines/suppliers/batch', { items: payload })
      const reply = `已录入 ${data.created} 条供应商设备` + (data.skipped ? `，${data.skipped} 条已存在已跳过。` : '。')
      const assistantMsg = { role: 'assistant', content: reply, payload: undefined }
      messages.value.push(assistantMsg)
      if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', reply)
      scrollToBottom()
      closeParsedModal()
    } catch (e) {
      const msg = e.response?.data?.detail || '批量添加失败'
      messages.value.push({ role: 'assistant', content: '添加失败：' + msg })
      if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', '添加失败：' + msg)
      scrollToBottom()
    } finally {
      batchLoading.value = false
    }
  }
}

function onKeydownEnter(e) {
  if (e.shiftKey) return
  e.preventDefault()
  onSend()
}

/** 解析 SSE 流：按 event/data 回调，返回 { onEvent(event, data), onError(err) } */
function parseSSE(reader, decoder, onEvent, onError) {
  let buffer = ''
  let currentEvent = null
  let currentData = []
  const processLine = (line) => {
    if (line.startsWith('event:')) {
      if (currentEvent != null && currentData.length) {
        onEvent(currentEvent, currentData.join('\n'))
      }
      currentEvent = line.slice(6).trim()
      currentData = []
    } else if (line.startsWith('data:')) {
      currentData.push(line.slice(5).trim())
    } else if (line === '') {
      if (currentEvent != null && currentData.length) {
        onEvent(currentEvent, currentData.join('\n'))
      }
      currentEvent = null
      currentData = []
    }
  }
  return (function pump() {
    return reader.read().then(({ done, value }) => {
      if (done) {
        if (currentEvent != null && currentData.length) onEvent(currentEvent, currentData.join('\n'))
        return
      }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split(/\r?\n/)
      buffer = lines.pop() || ''
      lines.forEach(processLine)
      return pump()
    }).catch(onError)
  })()
}

async function doDownload(filename) {
  if (!filename) return
  try {
    const { data } = await api.get('calculate/download', { params: { filename }, responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch (_) {}
}

async function onSend() {
  const text = inputText.value.trim()
  const att = attachment.value
  if (!(text || att) || sending.value || parseLoading.value) return
  const fullText = (text + (att ? '\n\n' + att.tableText : '')).trim()
  const displayContent = (text + (att ? '\n[已附表格：' + att.fileName + ']' : '')).trim() || '（附表格）'
  inputText.value = ''
  attachment.value = null
  await nextTick()

  const addUserMessageAndSession = (content, skipRouterReplace = false) => {
    const userMsg = { role: 'user', content }
    if (currentId.value) {
      analysisStore.appendMessage(currentId.value, 'user', content)
      messages.value.push(userMsg)
    } else {
      const id = analysisStore.createFromFirstMessage(content)
      if (id) {
        currentId.value = id
        messages.value = [userMsg]
        if (!skipRouterReplace) router.replace({ path: '/analysis/' + id })
      }
    }
    scrollToBottom()
  }

  addUserMessageAndSession(displayContent, true)
  const assistantMsg = { role: 'assistant', content: '', payload: undefined }
  messages.value.push(assistantMsg)
  if (currentId.value) {
    if (typeof analysisStore.pushMessage === 'function') analysisStore.pushMessage(currentId.value, assistantMsg)
    else analysisStore.appendMessage(currentId.value, 'assistant', '')
  }
  sending.value = true
  streamContentBuffer = ''
  scrollToBottom()
  await nextTick()

  if (currentId.value && route.params.id !== currentId.value) {
    router.replace({ path: '/analysis/' + currentId.value })
  }

  const streamController = new AbortController()
  abortControllerRef.value = streamController
  const history = messages.value.slice(0, -1).map((m) => ({ role: m.role, content: m.content }))
  const sessionId = currentId.value ? analysisStore.get(currentId.value)?.sessionId : null
  scrollToBottom()
  await nextTick()

  const baseURL = import.meta.env.VITE_API_BASE || '/api/'
  const url = (baseURL.replace(/\/$/, '') + '/analysis/chat').replace(/([^:]\/)\/+/g, '$1')
  const token = localStorage.getItem('aircomp_token')

  try {
    const res = await fetch(url, {
      method: 'POST',
      signal: streamController.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        message: text,
        session_id: sessionId ?? undefined,
        history,
        attachments: att ? [{ type: 'text', content: att.tableText }] : undefined,
      }),
      credentials: 'include',
    })
    if (!res.ok) {
      const errText = await res.text()
      let detail = errText
      try {
        const j = JSON.parse(errText)
        detail = j.detail || errText
      } catch (_) {}
      throw new Error(detail || `HTTP ${res.status}`)
    }
    const data = await res.json()
    assistantMsg.content = data.reply ?? ''
    const payload = {}
    if (data.intent) payload.intent = data.intent
    if (data.company_name) payload.company_name = data.company_name
    if (data.client_nos) payload.client_nos = data.client_nos
    if (data.client_list) payload.client_list = data.client_list
    if (Object.keys(payload).length) assistantMsg.payload = payload
    if (currentId.value) {
      analysisStore.save()
      if (data.session_id != null) analysisStore.updateSessionId(currentId.value, data.session_id)
    }
    commitLastMessageContent()
    scrollToBottom()
  } catch (err) {
    if (err?.name === 'AbortError') {
      assistantMsg.content = assistantMsg.content || '已取消'
    } else {
      assistantMsg.content = '抱歉：' + (err?.message ?? '请求失败')
    }
    if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', assistantMsg.content)
    commitLastMessageContent()
    scrollToBottom()
  } finally {
    sending.value = false
    abortControllerRef.value = null
  }
}

async function onConfirmSelection(msg) {
  const payload = msg?.payload
  if (recommendLoading.value || !payload?.company_name) return
  recommendLoading.value = true
  try {
    const { data } = await api.post('calculate/recommend', {
      company_name: payload.company_name,
      client_nos: payload.client_nos && payload.client_nos.length ? payload.client_nos : null,
      use_actual_flow: payload?.use_actual_flow !== false,
      schemes_only: true,
    })
    if (msg?.role === 'assistant') {
      msg.content = (msg.content || '') + '\n\n已生成选型方案：' + (data.summary || '')
      msg.payload = {
        ...msg.payload,
        selection_confirmed: true,
        summary: data.summary,
        recommended_scheme: data.recommended_scheme,
        recommended_schemes: data.recommended_schemes,
        machines: data.machines || [],
        new_eq: data.new_eq || [],
      }
      if (currentId.value) analysisStore.save()
    }
    if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', '已生成选型方案')
    scrollToBottom()
  } catch (err) {
    const errMsg = err.response?.data?.detail || err.message || '获取选型失败'
    messages.value.push({ role: 'assistant', content: '获取选型失败：' + errMsg })
    if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', '获取选型失败：' + errMsg)
    scrollToBottom()
  } finally {
    recommendLoading.value = false
  }
}

const showParamsModal = ref(false)
const paramsModalMsg = ref(null)
const paramsCalcLoading = ref(false)
const paramsForm = ref({
  company_name: '',
  running_hours_per_year: 8000,
  electricity_price: null,
  default_ser_p: null,
  machines: [],
  new_eq: [],
})

function canOpenParamsModal(msg) {
  const p = msg?.payload
  if (!p?.machines?.length || !p?.new_eq?.length) return false
  return p.machines.length === p.new_eq.length
}

function openParamsModal(msg) {
  if (!canOpenParamsModal(msg)) return
  const p = msg.payload
  paramsModalMsg.value = msg
  paramsForm.value = {
    company_name: p.company_name || '',
    running_hours_per_year: 8000,
    electricity_price: p.electricity_price ?? null,
    default_ser_p: p.default_ser_p ?? null,
    machines: JSON.parse(JSON.stringify(p.machines)),
    new_eq: JSON.parse(JSON.stringify(p.new_eq)),
  }
  showParamsModal.value = true
}

function closeParamsModal() {
  showParamsModal.value = false
  paramsModalMsg.value = null
}

async function submitParamsCalculation() {
  if (paramsCalcLoading.value || !paramsModalMsg.value) return
  const msg = paramsModalMsg.value
  const form = paramsForm.value
  if (!form.machines.length || form.machines.length !== form.new_eq.length) return
  paramsCalcLoading.value = true
  try {
    const body = {
      company_name: form.company_name,
      machines: form.machines,
      new_eq: form.new_eq,
      running_hours_per_year: form.running_hours_per_year || 8000,
    }
    if (form.electricity_price != null && form.electricity_price !== '') body.electricity_price = Number(form.electricity_price)
    if (form.default_ser_p != null && form.default_ser_p !== '') body.default_ser_p = Number(form.default_ser_p)
    const { data } = await api.post('calculate/run-with-params', body)
    if (msg?.role === 'assistant') {
      let extra = '\n\n节能量（年总节电）：' + (data.energy_savings_kwh ?? 0).toLocaleString() + ' kWh'
      if (data.energy_savings_cost != null) {
        extra += '；年节约电费：' + data.energy_savings_cost.toLocaleString() + ' 元'
      }
      msg.content = (msg.content || '') + extra
      msg.payload = {
        ...msg.payload,
        filename: data.filename,
        energy_savings_kwh: data.energy_savings_kwh ?? null,
        energy_savings_cost: data.energy_savings_cost ?? null,
      }
      if (currentId.value) analysisStore.save()
    }
    if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', '已生成节能计算报告，可下载 Excel。')
    closeParamsModal()
    scrollToBottom()
  } catch (err) {
    const errMsg = err.response?.data?.detail || err.message || '计算失败'
    messages.value.push({ role: 'assistant', content: '计算失败：' + errMsg })
    if (currentId.value) analysisStore.appendMessage(currentId.value, 'assistant', '计算失败：' + errMsg)
    scrollToBottom()
  } finally {
    paramsCalcLoading.value = false
  }
}

function onResetSelection(msg) {
  if (!msg?.payload) return
  const p = msg.payload
  delete p.selection_confirmed
  delete p.filename
  delete p.summary
  delete p.recommended_scheme
  delete p.recommended_schemes
  delete p.machines
  delete p.new_eq
  delete p.energy_savings_kwh
  delete p.energy_savings_cost
  let content = (msg.content || '').trim()
  const idx = content.indexOf('\n\n已生成选型方案：')
  if (idx !== -1) content = content.slice(0, idx).trim()
  const idx2 = content.indexOf('\n\n节能量（年总节电）：')
  if (idx2 !== -1) content = content.slice(0, idx2).trim()
  msg.content = content
  if (currentId.value) analysisStore.save()
  scrollToBottom()
}

onMounted(() => {
  const id = route.params.id
  if (id) loadAnalysis(id)
  else {
    currentId.value = null
    messages.value = []
  }
})
watch(
  () => route.params.id,
  (id) => {
    if (id) {
      if ((sending.value || parseLoading.value || showParsedModal.value) && currentId.value === id) return
      loadAnalysis(id)
    } else {
      currentId.value = null
      messages.value = []
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 3.25rem);
  min-height: 400px;
  max-width: 800px;
  margin: 0 auto;
  padding: 0 1rem;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 空状态：标题 + 输入框整体在画面中央，略偏上 */
.chat-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  padding-bottom: 30%;
  min-height: 0;
}

.chat-center .chat-welcome {
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}

.chat-center .chat-input-wrap--center {
  width: 100%;
  max-width: 560px;
  padding: 0;
  flex-shrink: 0;
}

.chat-center-waiting {
  margin: 0.5rem 0 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0 0.5rem;
  scrollbar-width: thin;
  scrollbar-color: var(--border, #e0e0e0) transparent;
}
.chat-messages::-webkit-scrollbar {
  width: 6px;
}
.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border, #e0e0e0);
  border-radius: 3px;
}
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted, #999);
}

.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0;
  text-align: center;
}

.chat-welcome-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 0.5rem;
}

.chat-welcome-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0;
  max-width: 420px;
  line-height: 1.5;
}

.chat-msg {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  align-items: flex-start;
}

.chat-msg--user {
  flex-direction: row-reverse;
}

.chat-msg-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 50%;
  color: var(--text-muted);
  background: var(--surface-elevated);
  border: 1px solid var(--border);
}

.chat-msg--user .chat-msg-avatar {
  color: #fff;
  background: var(--primary);
  border-color: var(--primary);
}

.chat-msg-body {
  max-width: 78%;
  min-width: 0;
}

.chat-msg--user .chat-msg-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.chat-msg-text {
  padding: 0.65rem 1rem;
  font-size: 0.95rem;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 14px;
}

.chat-msg--user .chat-msg-text {
  background: var(--primary);
  color: #fff;
  border-radius: 14px 14px 4px 14px;
}

.chat-msg--assistant .chat-msg-text {
  background: var(--surface-elevated);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 14px 14px 14px 4px;
}

.chat-msg-btns {
  margin-top: 0.6rem;
}

.chat-msg--user .chat-msg-btns {
  align-self: flex-end;
}

.chat-btn {
  padding: 0.45rem 0.9rem;
  font-size: 0.875rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: var(--font);
  border: none;
  transition: opacity 0.2s;
}

.chat-btn-primary {
  background: var(--primary);
  color: #fff;
}

.chat-btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.chat-btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-btn-secondary {
  background: var(--surface-elevated);
  color: var(--text);
  border: 1px solid var(--border);
}

.chat-btn-secondary:hover {
  opacity: 0.9;
}

.chat-msg-energy {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--surface-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.chat-msg-energy-label {
  color: var(--text-muted, #666);
}

.chat-msg-energy-value {
  font-weight: 600;
  color: var(--primary);
}

.chat-input-wrap {
  flex-shrink: 0;
  padding: 0.75rem 0 1.25rem;
}

.chat-msg-caliber {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.8125rem;
  color: var(--text-muted, #666);
}
.chat-msg-caliber-label {
  flex-shrink: 0;
}
.chat-msg-caliber-pills {
  display: inline-flex;
  background: var(--surface-elevated, #f5f5f5);
  border-radius: var(--radius-sm, 6px);
  padding: 2px;
  border: 1px solid var(--border, #e0e0e0);
}
.chat-msg-caliber .chat-caliber-pill {
  padding: 0.25rem 0.6rem;
  font-size: 0.8125rem;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted, #666);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.chat-msg-caliber .chat-caliber-pill:hover {
  color: var(--text, #333);
}
.chat-msg-caliber .chat-caliber-pill--on {
  background: var(--bg, #fff);
  color: var(--primary, #2563eb);
  box-shadow: 0 0 0 1px var(--border);
}

.chat-input-box {
  background: var(--surface-elevated);
  border: 1px solid var(--border);
  border-radius: 20px;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.chat-input-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow-soft);
}

.chat-input-area {
  width: 100%;
  min-height: 88px;
  padding: 1rem 1.25rem 0.5rem;
  background: none;
  border: none;
  color: var(--text);
  font-size: 0.95rem;
  line-height: 1.5;
  resize: none;
  outline: none;
  font-family: var(--font);
  display: block;
}

.chat-input-area::placeholder {
  color: var(--text-muted);
}

.chat-input-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem 0.75rem 1.25rem;
  border-top: 1px solid var(--border);
  gap: 0.75rem;
}

.chat-input-pills {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.chat-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: 999px;
  cursor: default;
  font-family: var(--font);
  transition: color 0.2s, background 0.2s;
}

.chat-pill--active {
  color: #fff;
  background: var(--primary);
  cursor: default;
}

.chat-pill-upload {
  cursor: pointer;
}

.chat-pill-upload:hover {
  color: var(--primary);
  background: rgba(124, 58, 237, 0.12);
}

.chat-pill-upload input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
}

.chat-attachment {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.chat-attachment-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chat-attachment-remove {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-size: 1.1rem;
  line-height: 1;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}
.chat-attachment-remove:hover {
  color: var(--text);
  background: rgba(239, 68, 68, 0.12);
}

.chat-input-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.chat-input-sep {
  width: 1px;
  height: 20px;
  background: var(--border);
}

.chat-btn-stop {
  padding: 0 0.75rem;
  height: 36px;
  font-size: 0.875rem;
  color: var(--text-muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  cursor: pointer;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.chat-btn-stop:hover {
  color: var(--text);
  border-color: rgba(239, 68, 68, 0.5);
  background: rgba(239, 68, 68, 0.08);
}

.chat-send {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-muted);
  border-radius: 50%;
  cursor: pointer;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}

.chat-send:hover:not(:disabled) {
  color: var(--primary);
  border-color: var(--primary);
  background: rgba(124, 58, 237, 0.12);
}

.chat-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: chat-spin 0.7s linear infinite;
}

@keyframes chat-spin {
  to { transform: rotate(360deg); }
}

/* 分析等待：气泡内动画，避免出现空白气泡 */
.chat-msg-waiting {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  min-height: 2rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}
.chat-msg-waiting-dots {
  display: inline-flex;
  gap: 4px;
}
.chat-msg-waiting-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  opacity: 0.7;
  animation: chat-dot 1.4s ease-in-out infinite both;
}
.chat-msg-waiting-dots span:nth-child(1) { animation-delay: 0s; }
.chat-msg-waiting-dots span:nth-child(2) { animation-delay: 0.2s; }
.chat-msg-waiting-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes chat-dot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}
.chat-msg-waiting-text {
  flex-shrink: 0;
}

/* 解析中提示条 */
.chat-parse-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: var(--text-muted);
  background: rgba(124, 58, 237, 0.08);
  border-top: 1px solid var(--border);
}
.chat-parse-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: chat-spin 0.7s linear infinite;
}

/* 确认参数弹窗：复用 parsed-modal 风格，仅补充内容区样式 */
.params-modal.parsed-modal {
  max-width: 920px;
}
.params-modal-body.parsed-modal-body {
  padding: 1rem 1.25rem;
}
.params-block {
  margin-bottom: 1.5rem;
}
.params-block:last-child {
  margin-bottom: 0;
}
.params-block--global {
  padding: 1rem 1.25rem;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.params-block-title {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
}
.params-block-desc {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  color: var(--text-muted);
  line-height: 1.45;
}
.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.75rem 1.25rem;
}
.params-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.params-field-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text);
}
.params-field-input {
  padding: 0.4rem 0.5rem;
  font-size: 0.9rem;
  color: var(--text);
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  min-width: 0;
}
.params-field-input::placeholder {
  color: var(--text-muted);
}
.params-field-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow-soft, rgba(124, 58, 237, 0.2));
}
.params-field-hint {
  font-size: 0.8125rem;
  color: var(--text-muted);
  line-height: 1.35;
}
.params-table-wrap {
  overflow-x: auto;
  margin-top: 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.params-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.params-table th,
.params-table td {
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: middle;
  color: var(--text);
}
.params-table th {
  background: rgba(0, 0, 0, 0.2);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}
.params-table th br {
  display: block;
  margin-top: 2px;
}
.params-table tbody tr:hover td {
  background: rgba(255, 255, 255, 0.03);
}
.params-table tr:last-child td {
  border-bottom: none;
}
.params-cell {
  width: 100%;
  min-width: 52px;
  padding: 0.35rem 0.45rem;
  font-size: 0.875rem;
  color: var(--text);
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
  border-radius: 4px;
  transition: border-color 0.2s;
}
.params-cell:focus {
  outline: none;
  border-color: var(--primary);
}
.params-select {
  cursor: pointer;
}
</style>
