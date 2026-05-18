<template>
  <el-card>
    <template #header>
      <span>竞赛列表</span>
      <el-input v-model="search" placeholder="搜索竞赛标题" clearable style="margin-left: 12px; width: 240px" />
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="竞赛编号" width="100" />
      <el-table-column prop="title" label="标题" min-width="160" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column label="报名起止" min-width="200">
        <template #default="{ row }">
          {{ fmt(row.registration_start) }} ~ {{ fmt(row.registration_end) }}
        </template>
      </el-table-column>
      <el-table-column label="比赛时间" min-width="200">
        <template #default="{ row }">
          {{ fmt(row.competition_start) }} ~ {{ fmt(row.competition_end) }}
        </template>
      </el-table-column>
      <el-table-column label="队伍上限" width="90">
        <template #default="{ row }">{{ row.max_team_members ?? '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="canRegister(row)"
            type="primary"
            link
            :loading="busyId === row.id"
            @click="openRegister(row)"
          >
            报名
          </el-button>
          <span v-else>{{ regLabel(row.id) }}</span>
          <el-button
            v-if="row.status !== 'draft'"
            type="warning"
            link
            @click="openAnnouncements(row)"
          >
            公告
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="teamDialogVisible" title="选择队伍报名" width="400px">
      <el-form label-width="80px">
        <el-form-item label="竞赛">
          <span>{{ regCompetition?.title }}</span>
        </el-form-item>
        <el-form-item label="选择队伍" required>
          <el-select v-model="selectedTeamId" style="width: 100%" placeholder="请选择队伍">
            <el-option
              v-for="t in myTeams"
              :key="t.id"
              :label="`${t.name}（${t.approved_count}人）`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="teamDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="doRegister">确认报名</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="annoDialogVisible" :title="`${annoCompetitionTitle} - 公告`" width="720px">
      <el-table :data="announcements" border max-height="400">
        <el-table-column label="标题" width="180">
          <template #default="{ row }">
            <router-link
              class="title-link"
              :to="{ name: 'student-announcement-detail', params: { id: row.id }, query: { from: 'competitions' } }"
              @click="annoDialogVisible = false"
            >
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="附件" min-width="120">
          <template #default="{ row }">
            <template v-if="row.attachments?.length">
              <div v-for="a in row.attachments" :key="a.id" class="att-line">
                <a class="file-a" :href="absMediaUrl(annFileUrl(a.file))" target="_blank" rel="noopener noreferrer">
                  {{ a.original_name || '下载' }}
                </a>
              </div>
            </template>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="published_at" label="发布时间" width="170">
          <template #default="{ row }">{{ fmt(row.published_at) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'

const loading = ref(false)
const competitions = ref([])
const registrations = ref([])
const myTeams = ref([])
const busyId = ref(null)
const teamDialogVisible = ref(false)
const selectedTeamId = ref(null)
const regCompetition = ref(null)
const submitting = ref(false)
const annoDialogVisible = ref(false)
const annoCompetitionTitle = ref('')
const announcements = ref([])

const regMap = computed(() => {
  const m = {}
  for (const r of registrations.value) m[r.competition] = r
  return m
})

const search = ref('')

const rows = computed(() => {
  if (!search.value) return competitions.value
  const kw = search.value.toLowerCase()
  return competitions.value.filter((c) => c.title.toLowerCase().includes(kw))
})

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

function statusText(s) {
  const map = {
    draft: '草稿',
    registering: '报名中',
    published: '进行中',
    registration_closed: '报名已截止',
    reviewing: '评审中',
    finished: '已结束',
  }
  return map[s] || '未知'
}

function regLabel(compId) {
  const r = regMap.value[compId]
  if (!r) return '-'
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return (r.team_name || '队伍') + ' - ' + (map[r.status] || '未知')
}

function canRegister(row) {
  if (row.status !== 'published' && row.status !== 'registering') return false
  const r = regMap.value[row.id]
  return !r || r.status === 'rejected'
}

async function load() {
  loading.value = true
  try {
    const [c, reg, t] = await Promise.all([
      api.get('/competitions/'),
      api.get('/registrations/'),
      api.get('/teams/'),
    ])
    competitions.value = c.data.results ?? c.data
    registrations.value = reg.data.results ?? reg.data
    myTeams.value = t.data.results ?? t.data
  } finally {
    loading.value = false
  }
}

function absMediaUrl(path) {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const p = path.startsWith('/') ? path : `/${path}`
  return `${window.location.origin}${p}`
}

function annFileUrl(fileField) {
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

async function openAnnouncements(row) {
  annoCompetitionTitle.value = row.title
  annoDialogVisible.value = true
  const { data } = await api.get('/announcements/', { params: { competition: row.id } })
  announcements.value = data.results ?? data
}

function openRegister(row) {
  regCompetition.value = row
  selectedTeamId.value = null
  teamDialogVisible.value = true
}

async function doRegister() {
  if (!selectedTeamId.value) return ElMessage.warning('请选择队伍')
  submitting.value = true
  try {
    await api.post('/registrations/', {
      team: selectedTeamId.value,
      competition: regCompetition.value.id,
    })
    ElMessage.success('报名已提交，请等待审核')
    teamDialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '报名失败'))
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.att-line + .att-line {
  margin-top: 4px;
}
.file-a {
  color: var(--el-color-primary);
  text-decoration: none;
}
.file-a:hover {
  text-decoration: underline;
}
.title-link {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
}
.title-link:hover {
  text-decoration: underline;
}
</style>
