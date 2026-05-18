<template>
  <el-card>
    <template #header>
      <span>竞赛管理</span>
      <el-input v-model="search" placeholder="搜索竞赛标题" clearable style="margin-left: 12px; width: 240px" />
      <el-button type="primary" style="float: right" @click="openCreate">新建</el-button>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="编号" width="70" />
      <el-table-column prop="title" label="标题" min-width="160" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column label="专家" min-width="140">
        <template #default="{ row }">
          {{ (row.experts_read || []).map((e) => e.username).join(', ') || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button type="warning" link @click="openAnnouncement(row)">公告</el-button>
          <el-button type="danger" link @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="annoVisible" title="发布公告" width="620px" destroy-on-close @closed="onAnnoDialogClosed">
      <el-form :model="annoForm" label-width="100px">
        <el-form-item label="竞赛">
          <el-select
            v-model="annoForm.competition"
            filterable
            clearable
            placeholder="请选择：全局公告或某一竞赛"
            style="width: 100%"
          >
            <el-option label="全局公告（不关联竞赛，全体可见）" :value="null" />
            <el-option v-for="c in list" :key="c.id" :label="c.title" :value="c.id" />
          </el-select>
          <div class="hint">从本行打开时默认选中当前竞赛；可改为全局公告或其它竞赛。</div>
        </el-form-item>
        <el-form-item label="红点提醒">
          <el-radio-group v-model="annoForm.remind_scope">
            <el-radio label="none">不提醒</el-radio>
            <el-radio label="all_students">全体学生</el-radio>
            <el-radio label="competition_registrants" :disabled="!hasAnnoCompetitionScope">
              本竞赛已报名学生
            </el-radio>
          </el-radio-group>
          <div class="hint">
            开启后学生端侧栏「公告」出现红点；学生打开该公告详情页后视为已读。修改提醒范围会重新向未读用户显示红点。
          </div>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="annoForm.title" />
        </el-form-item>
        <el-form-item label="正文" required>
          <el-input v-model="annoForm.body" type="textarea" rows="6" />
        </el-form-item>
        <el-form-item label="附件">
          <div class="file-row">
            <input :key="annoFileInputKey" type="file" multiple @change="onAnnoPickFiles" />
          </div>
          <div v-for="(f, i) in annoNewFiles" :key="i + f.name" class="new-file">
            <span>{{ f.name }}</span>
            <el-button type="danger" link @click="removeAnnoNewFile(i)">去掉</el-button>
          </div>
        </el-form-item>
        <el-form-item label="发布">
          <el-switch v-model="annoForm.is_published" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="annoVisible = false">取消</el-button>
        <el-button type="primary" :loading="annoSaving" @click="saveAnnouncement">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="visible" :title="form.id ? '编辑竞赛' : '新建竞赛'" width="640px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="草稿" value="draft" />
            <el-option label="报名中" value="registering" />
            <el-option label="进行中" value="published" />
            <el-option label="报名已截止" value="registration_closed" />
            <el-option label="评审中" value="reviewing" />
            <el-option label="已结束" value="finished" />
          </el-select>
        </el-form-item>
        <el-form-item label="报名开始">
          <el-date-picker v-model="form.registration_start" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="报名结束">
          <el-date-picker v-model="form.registration_end" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="比赛开始">
          <el-date-picker v-model="form.competition_start" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="比赛结束">
          <el-date-picker v-model="form.competition_end" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="队伍人数上限">
          <el-input-number v-model="form.max_team_members" :min="1" style="width: 100%" placeholder="留空为不限制" />
        </el-form-item>
        <el-form-item label="分配专家">
          <el-select v-model="form.expert_ids" multiple filterable style="width: 100%">
            <el-option v-for="e in experts" :key="e.id" :label="e.username" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="每位作品评审次数">
          <el-input-number
            v-model="form.reviews_per_submission"
            :min="1"
            :max="reviewsPerSubmissionMax"
            style="width: 100%"
          />
          <div class="hint">进入「评审中」时，每份作品从已选专家中随机分配该数量的专家打分（不超过已选专家人数）。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'

const loading = ref(false)
const saving = ref(false)
const annoSaving = ref(false)
const list = ref([])
const experts = ref([])
const visible = ref(false)
const annoVisible = ref(false)
const annoForm = ref({
  competition: null,
  title: '',
  body: '',
  is_published: true,
  remind_scope: 'none',
})
const annoNewFiles = ref([])
const annoFileInputKey = ref(0)

const hasAnnoCompetitionScope = computed(
  () => annoForm.value.competition != null && annoForm.value.competition !== '',
)
const form = ref({
  id: null,
  title: '',
  description: '',
  status: 'draft',
  registration_start: null,
  registration_end: null,
  competition_start: null,
  competition_end: null,
  max_team_members: null,
  expert_ids: [],
  reviews_per_submission: 1,
})

const search = ref('')

const rows = computed(() => {
  if (!search.value) return list.value
  const kw = search.value.toLowerCase()
  return list.value.filter((c) => c.title.toLowerCase().includes(kw))
})

const reviewsPerSubmissionMax = computed(() => Math.max(1, form.value.expert_ids?.length || 1))

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

function toIso(d) {
  if (!d) return null
  return d instanceof Date ? d.toISOString() : d
}

async function loadExperts() {
  const { data } = await api.get('/experts/')
  experts.value = data.results ?? data
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/competitions/')
    list.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = {
    id: null,
    title: '',
    description: '',
    status: 'draft',
    registration_start: new Date(),
    registration_end: new Date(Date.now() + 7 * 86400000),
    competition_start: new Date(Date.now() + 7 * 86400000),
    competition_end: new Date(Date.now() + 14 * 86400000),
    max_team_members: null,
    expert_ids: [],
    reviews_per_submission: 1,
  }
  visible.value = true
}

function openAnnouncement(row) {
  annoForm.value = {
    competition: row.id,
    title: '',
    body: '',
    is_published: true,
    remind_scope: 'none',
  }
  annoNewFiles.value = []
  annoFileInputKey.value += 1
  annoVisible.value = true
}

function onAnnoPickFiles(e) {
  const picked = e.target.files ? Array.from(e.target.files) : []
  if (picked.length) annoNewFiles.value = [...annoNewFiles.value, ...picked]
  annoFileInputKey.value += 1
}

function removeAnnoNewFile(i) {
  annoNewFiles.value.splice(i, 1)
  annoNewFiles.value = [...annoNewFiles.value]
}

function onAnnoDialogClosed() {
  annoNewFiles.value = []
  annoFileInputKey.value += 1
}

async function saveAnnouncement() {
  if (!annoForm.value.title?.trim() || !annoForm.value.body?.trim()) {
    ElMessage.warning('请填写标题与正文')
    return
  }
  annoSaving.value = true
  try {
    const fd = new FormData()
    const comp = annoForm.value.competition
    if (comp != null && comp !== '') {
      fd.append('competition', String(comp))
    }
    fd.append('title', annoForm.value.title)
    fd.append('body', annoForm.value.body)
    fd.append('is_published', annoForm.value.is_published ? 'true' : 'false')
    fd.append('remind_scope', annoForm.value.remind_scope || 'none')
    for (const f of annoNewFiles.value) {
      fd.append('attachments', f)
    }
    await api.post('/announcements/', fd)
    ElMessage.success('已保存')
    annoVisible.value = false
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '保存失败'))
  } finally {
    annoSaving.value = false
  }
}

function openEdit(row) {
  form.value = {
    id: row.id,
    title: row.title,
    description: row.description || '',
    status: row.status,
    registration_start: row.registration_start ? new Date(row.registration_start) : null,
    registration_end: row.registration_end ? new Date(row.registration_end) : null,
    competition_start: row.competition_start ? new Date(row.competition_start) : null,
    competition_end: row.competition_end ? new Date(row.competition_end) : null,
    max_team_members: row.max_team_members ?? null,
    expert_ids: (row.experts_read || []).map((e) => e.id),
    reviews_per_submission: row.reviews_per_submission ?? 1,
  }
  visible.value = true
}

async function save() {
  saving.value = true
  try {
    const payload = {
      title: form.value.title,
      description: form.value.description,
      status: form.value.status,
      registration_start: toIso(form.value.registration_start),
      registration_end: toIso(form.value.registration_end),
      competition_start: toIso(form.value.competition_start),
      competition_end: toIso(form.value.competition_end),
      max_team_members: form.value.max_team_members || null,
      expert_ids: form.value.expert_ids,
      reviews_per_submission: Math.min(
        Math.max(1, form.value.reviews_per_submission || 1),
        Math.max(1, form.value.expert_ids?.length || 1),
      ),
    }
    if (form.value.id) {
      await api.patch(`/competitions/${form.value.id}/`, payload)
    } else {
      await api.post('/competitions/', payload)
    }
    ElMessage.success('已保存')
    visible.value = false
    await load()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除「${row.title}」？`, '确认')
  await api.delete(`/competitions/${row.id}/`)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await loadExperts()
  await load()
})

watch(
  () => form.value.expert_ids?.length,
  (len) => {
    const max = Math.max(1, len || 1)
    if (form.value.reviews_per_submission > max) {
      form.value.reviews_per_submission = max
    }
  },
)

watch(
  () => annoForm.value.competition,
  () => {
    if (annoForm.value.remind_scope === 'competition_registrants' && !hasAnnoCompetitionScope.value) {
      annoForm.value.remind_scope = 'none'
    }
  },
)
</script>

<style scoped>
.hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.45;
}
.file-row,
.new-file {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.new-file {
  font-size: 13px;
  color: var(--el-text-color-regular);
}
</style>
