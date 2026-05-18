<template>
  <el-card>
    <template #header>
      <span>作品评分</span>
      <span style="margin-left: 16px">
        <el-select v-model="filterCompetition" placeholder="全部竞赛" clearable style="width: 200px" @change="onFilter">
          <el-option v-for="c in competitions" :key="c.id" :label="c.title" :value="c.id" />
        </el-select>
        <el-button style="margin-left: 8px" @click="toggleSort">
          平均分 {{ sortDir === 'desc' ? '↓' : '↑' }}
        </el-button>
        <el-button type="primary" style="margin-left: 8px" @click="openExportDialog">导出 Excel</el-button>
      </span>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="作品编号" width="90" />
      <el-table-column prop="team_name" label="队伍" width="140" />
      <el-table-column label="竞赛" width="120">
        <template #default="{ row }">{{ compTitle(row.competition) }}</template>
      </el-table-column>
      <el-table-column prop="description" label="说明" min-width="160" show-overflow-tooltip />
      <el-table-column label="附件" min-width="220">
        <template #default="{ row }">
          <template v-if="row.attachments?.length">
            <div v-for="a in row.attachments" :key="a.id" class="att-line">
              <el-link type="primary" :href="mediaFileUrl(a.file)" target="_blank" rel="noopener noreferrer">
                {{ a.original_name || '下载' }}
              </el-link>
            </div>
          </template>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="平均分" width="100">
        <template #default="{ row }">
          {{ row.average_score != null ? Number(row.average_score).toFixed(2) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="review_count" label="评审数" width="80" />
    </el-table>

    <el-dialog v-model="exportVisible" title="导出评分与奖项" width="720px" destroy-on-close @open="onExportOpen">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="按平均分从高到低排名；名次落在某一区间内即获得对应奖项。导出列为：队伍编号、队伍名称、奖项。下载为 .xls 表格，可直接用 Microsoft Excel 或 WPS 打开。"
        style="margin-bottom: 12px"
      />
      <div class="section-title">奖项规则（名次含起止边界）</div>
      <el-table :data="awardRules" border size="small" style="margin-bottom: 12px">
        <el-table-column label="名次起" width="110">
          <template #default="{ $index }">
            <el-input-number v-model="awardRules[$index].rankStart" :min="1" :max="9999" size="small" controls-position="right" />
          </template>
        </el-table-column>
        <el-table-column label="名次止" width="110">
          <template #default="{ $index }">
            <el-input-number v-model="awardRules[$index].rankEnd" :min="1" :max="99999" size="small" controls-position="right" />
          </template>
        </el-table-column>
        <el-table-column label="奖项名称" min-width="160">
          <template #default="{ $index }">
            <el-input v-model="awardRules[$index].name" placeholder="如：一等奖" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ $index }">
            <el-button type="danger" link :disabled="awardRules.length <= 1" @click="removeRule($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" link @click="addRule">+ 添加奖项区间</el-button>

      <div class="section-title" style="margin-top: 16px">预览（与导出顺序一致，按平均分从高到低排名）</div>
      <el-table :data="exportPreview" border max-height="280" size="small">
        <el-table-column prop="rank" label="名次" width="70" />
        <el-table-column prop="team" label="队伍编号" width="100" />
        <el-table-column prop="team_name" label="队伍名称" width="120" />
        <el-table-column prop="award" label="奖项" min-width="120" />
      </el-table>

      <template #footer>
        <el-button @click="exportVisible = false">取消</el-button>
        <el-button type="primary" @click="doExportExcel">导出</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api/http'

const loading = ref(false)
const submissions = ref([])
const competitions = ref([])
const filterCompetition = ref(null)
const sortDir = ref('desc')

const exportVisible = ref(false)
const awardRules = ref([])

const rows = computed(() => {
  let list = submissions.value
  if (filterCompetition.value) {
    list = list.filter((s) => s.competition === filterCompetition.value)
  }
  list = [...list].sort((a, b) => {
    const sa = a.average_score ?? -1
    const sb = b.average_score ?? -1
    return sortDir.value === 'desc' ? sb - sa : sa - sb
  })
  return list
})

/** 导出用：固定按平均分降序，无平均分排后 */
function sortedForExport(list) {
  return [...list].sort((a, b) => {
    const ha = a.average_score != null
    const hb = b.average_score != null
    if (ha && hb) return Number(b.average_score) - Number(a.average_score)
    if (ha && !hb) return -1
    if (!ha && hb) return 1
    return (a.team || 0) - (b.team || 0)
  })
}

const exportPreview = computed(() => {
  const list = sortedForExport(rows.value)
  const sortedRules = [...awardRules.value].sort((a, b) => a.rankStart - b.rankStart)
  return list.map((row, i) => {
    const rank = i + 1
    let award = ''
    for (const r of sortedRules) {
      if (rank >= r.rankStart && rank <= r.rankEnd) {
        award = r.name || ''
        break
      }
    }
    return {
      rank,
      team: row.team,
      team_name: row.team_name || '',
      award,
    }
  })
})

function defaultAwardRules() {
  return [
    { rankStart: 1, rankEnd: 1, name: '一等奖' },
    { rankStart: 2, rankEnd: 3, name: '二等奖' },
    { rankStart: 4, rankEnd: 9999, name: '三等奖' },
  ]
}

function onExportOpen() {
  if (!awardRules.value.length) awardRules.value = defaultAwardRules()
}

function openExportDialog() {
  if (!rows.value.length) {
    ElMessage.warning('当前没有可导出的作品，请调整筛选或确认已有评分数据')
    return
  }
  awardRules.value = defaultAwardRules()
  exportVisible.value = true
}

function addRule() {
  const last = awardRules.value[awardRules.value.length - 1]
  const start = last ? Math.min(last.rankEnd + 1, 9999) : 1
  awardRules.value.push({ rankStart: start, rankEnd: start + 4, name: '' })
}

function removeRule(i) {
  if (awardRules.value.length <= 1) return
  awardRules.value.splice(i, 1)
}

function validateAwardRules() {
  for (let i = 0; i < awardRules.value.length; i++) {
    const r = awardRules.value[i]
    if (!r.name || !String(r.name).trim()) return `第 ${i + 1} 行奖项名称不能为空`
    if (r.rankStart == null || r.rankEnd == null) return `第 ${i + 1} 行名次起止须填写`
    if (r.rankStart < 1 || r.rankEnd < 1) return `第 ${i + 1} 行名次须 ≥ 1`
    if (r.rankStart > r.rankEnd) return `第 ${i + 1} 行名次起不能大于名次止`
  }
  const sorted = [...awardRules.value].sort((a, b) => a.rankStart - b.rankStart)
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i].rankStart <= sorted[i - 1].rankEnd) {
      return '名次区间不能重叠，请调整后再导出'
    }
  }
  return ''
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function doExportExcel() {
  const err = validateAwardRules()
  if (err) {
    ElMessage.error(err)
    return
  }
  const list = sortedForExport(rows.value)
  const sortedRules = [...awardRules.value].sort((a, b) => a.rankStart - b.rankStart)
  const compPart = filterCompetition.value
    ? competitions.value.find((c) => c.id === filterCompetition.value)?.title || String(filterCompetition.value)
    : '全部竞赛'
  const safe = String(compPart).replace(/[\\/:*?"<>|]/g, '_')

  const head =
    '<tr><td>队伍编号</td><td>队伍名称</td><td>奖项</td></tr>'
  const body = list
    .map((row, i) => {
      const rank = i + 1
      let award = ''
      for (const r of sortedRules) {
        if (rank >= r.rankStart && rank <= r.rankEnd) {
          award = (r.name || '').trim()
          break
        }
      }
      const id = escapeHtml(String(row.team ?? ''))
      const name = escapeHtml(row.team_name || '')
      const aw = escapeHtml(award)
      return `<tr><td style="mso-number-format:'\\@'">${id}</td><td>${name}</td><td>${aw}</td></tr>`
    })
    .join('')

  const html =
    '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">' +
    '<head><meta charset="UTF-8"></head><body><table border="1">' +
    head +
    body +
    '</table></body></html>'

  const blob = new Blob(['\ufeff' + html], { type: 'application/vnd.ms-excel;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `作品评分_${safe}_${Date.now()}.xls`
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success('已导出')
  exportVisible.value = false
}

function compTitle(id) {
  const c = competitions.value.find((c) => c.id === id)
  return c ? c.title : id
}

function mediaFileUrl(fileField) {
  if (!fileField) return ''
  const u = String(fileField).trim()
  if (!u) return ''
  if (u.startsWith('http://') || u.startsWith('https://')) {
    try {
      const parsed = new URL(u)
      const path = parsed.pathname + parsed.search
      if (path.startsWith('/media')) return path
    } catch {
      /* ignore */
    }
    return u
  }
  if (u.startsWith('/')) return u
  return `/${u.replace(/^\/+/, '')}`
}

function toggleSort() {
  sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
}

function onFilter() {}

onMounted(async () => {
  loading.value = true
  try {
    const [s, c] = await Promise.all([
      api.get('/submissions/'),
      api.get('/competitions/'),
    ])
    submissions.value = s.data.results ?? s.data
    competitions.value = c.data.results ?? c.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.att-line + .att-line {
  margin-top: 4px;
}
.section-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}
</style>
