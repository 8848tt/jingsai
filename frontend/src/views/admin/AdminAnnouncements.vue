<template>
  <el-card>
    <template #header>
      <span>公告管理</span>
      <el-select v-model="filterComp" placeholder="全部公告" clearable style="margin-left: 12px; width: 220px">
        <el-option label="全局公告" :value="FILTER_GLOBAL_ONLY" />
        <el-option v-for="c in competitions" :key="c.id" :label="c.title" :value="c.id" />
      </el-select>
      <el-button type="primary" style="float: right" @click="openCreate">新建</el-button>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="编号" width="70" />
      <el-table-column prop="competition" label="竞赛编号" width="110">
        <template #default="{ row }">{{ row.competition != null ? row.competition : '—' }}</template>
      </el-table-column>
      <el-table-column label="标题" min-width="160">
        <template #default="{ row }">
          <router-link class="title-link" :to="{ name: 'admin-announcement-detail', params: { id: row.id } }">
            {{ row.title }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="is_published" label="已发布" width="90">
        <template #default="{ row }">{{ row.is_published ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column prop="published_at" label="发布时间" width="180">
        <template #default="{ row }">{{ fmt(row.published_at) }}</template>
      </el-table-column>
      <el-table-column label="附件" width="100">
        <template #default="{ row }">
          <span v-if="(row.attachments || []).length">{{ row.attachments.length }} 个</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" :title="form.id ? '编辑公告' : '新建公告'" width="620px" destroy-on-close @closed="onDialogClosed">
      <el-form :model="form" label-width="100px">
        <el-form-item label="竞赛">
          <el-select
            v-model="form.competition"
            filterable
            clearable
            placeholder="请选择：全局公告或某一竞赛"
            style="width: 100%"
          >
            <el-option label="全局公告（不关联竞赛，全体可见）" :value="null" />
            <el-option v-for="c in competitions" :key="c.id" :label="c.title" :value="c.id" />
          </el-select>
          <div class="hint">选择「全局公告」或清空后保存，即发布为全体学生可见的全局通知。</div>
        </el-form-item>
        <el-form-item label="红点提醒">
          <el-radio-group v-model="form.remind_scope">
            <el-radio label="none">不提醒</el-radio>
            <el-radio label="all_students">全体学生</el-radio>
            <el-radio label="competition_registrants" :disabled="!hasCompetitionScope">
              本竞赛已报名学生
            </el-radio>
          </el-radio-group>
          <div class="hint">
            开启后学生端侧栏「公告」出现红点；学生打开该公告详情页后视为已读。修改提醒范围会重新向未读用户显示红点。
          </div>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="正文" required>
          <el-input v-model="form.body" type="textarea" rows="6" />
        </el-form-item>
        <el-form-item label="附件">
          <template v-if="form.id && keptAttachments.length">
            <div v-for="a in keptAttachments" :key="a.id" class="attach-row">
              <el-link type="primary" :href="attachmentUrl(a.file)" target="_blank" rel="noopener noreferrer">
                {{ a.original_name || '文件' }}
              </el-link>
              <el-button type="danger" link @click="removeKeptAttachment(a)">移除</el-button>
            </div>
          </template>
          <div class="file-row">
            <input :key="fileInputKey" type="file" multiple @change="onPickFiles" />
          </div>
          <div v-for="(f, i) in newFiles" :key="i + f.name" class="new-file">
            <span>{{ f.name }}</span>
            <el-button type="danger" link @click="removeNewFile(i)">去掉</el-button>
          </div>
        </el-form-item>
        <el-form-item label="发布">
          <el-switch v-model="form.is_published" />
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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'

const route = useRoute()
const router = useRouter()

/** 列表筛选：仅全局公告 */
const FILTER_GLOBAL_ONLY = '__global_only__'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const competitions = ref([])
const visible = ref(false)
const newFiles = ref([])
const keptAttachments = ref([])
const pendingDeleteIds = ref([])
const fileInputKey = ref(0)
const form = ref({
  id: null,
  competition: null,
  title: '',
  body: '',
  is_published: false,
  remind_scope: 'none',
})

const hasCompetitionScope = computed(
  () => form.value.competition != null && form.value.competition !== '',
)

watch(
  () => form.value.competition,
  () => {
    if (form.value.remind_scope === 'competition_registrants' && !hasCompetitionScope.value) {
      form.value.remind_scope = 'none'
    }
  },
)

const filterComp = ref(null)

const rows = computed(() => {
  if (!filterComp.value) return list.value
  if (filterComp.value === FILTER_GLOBAL_ONLY) {
    return list.value.filter((a) => a.competition == null)
  }
  return list.value.filter((a) => a.competition === filterComp.value)
})

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

function attachmentUrl(fileField) {
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

async function loadCompetitions() {
  const { data } = await api.get('/competitions/')
  competitions.value = data.results ?? data
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/announcements/')
    list.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

function resetDialogFiles() {
  keptAttachments.value = []
  pendingDeleteIds.value = []
  newFiles.value = []
  fileInputKey.value += 1
}

function openCreate() {
  resetDialogFiles()
  form.value = {
    id: null,
    competition: null,
    title: '',
    body: '',
    is_published: false,
    remind_scope: 'none',
  }
  visible.value = true
}

function openEdit(row) {
  resetDialogFiles()
  form.value = {
    id: row.id,
    competition: row.competition,
    title: row.title,
    body: row.body,
    is_published: row.is_published,
    remind_scope: row.remind_scope ?? 'none',
  }
  keptAttachments.value = [...(row.attachments || [])]
  visible.value = true
}

function onPickFiles(e) {
  const list = e.target.files ? Array.from(e.target.files) : []
  if (list.length) newFiles.value = [...newFiles.value, ...list]
  fileInputKey.value += 1
}

function removeNewFile(i) {
  newFiles.value.splice(i, 1)
  newFiles.value = [...newFiles.value]
}

function removeKeptAttachment(a) {
  keptAttachments.value = keptAttachments.value.filter((x) => x.id !== a.id)
  pendingDeleteIds.value = [...pendingDeleteIds.value, a.id]
}

function onDialogClosed() {
  router.replace({ query: {} })
}

async function save() {
  if (!form.value.title?.trim() || !form.value.body?.trim()) {
    ElMessage.warning('请填写标题与正文')
    return
  }
  saving.value = true
  try {
    const isEdit = !!form.value.id
    const hasFileOps = newFiles.value.length > 0 || pendingDeleteIds.value.length > 0
    const comp = form.value.competition

    if (hasFileOps || !isEdit) {
      const fd = new FormData()
      if (comp != null && comp !== '') {
        fd.append('competition', String(comp))
      }
      fd.append('title', form.value.title)
      fd.append('body', form.value.body)
      fd.append('is_published', form.value.is_published ? 'true' : 'false')
      fd.append('remind_scope', form.value.remind_scope || 'none')
      if (pendingDeleteIds.value.length) {
        fd.append('delete_attachment_ids', pendingDeleteIds.value.join(','))
      }
      for (const f of newFiles.value) {
        fd.append('attachments', f)
      }
      if (isEdit) {
        await api.patch(`/announcements/${form.value.id}/`, fd)
      } else {
        await api.post('/announcements/', fd)
      }
    } else {
      const payload = {
        competition: comp != null && comp !== '' ? comp : null,
        title: form.value.title,
        body: form.value.body,
        is_published: form.value.is_published,
        remind_scope: form.value.remind_scope || 'none',
      }
      if (isEdit) {
        await api.patch(`/announcements/${form.value.id}/`, payload)
      } else {
        await api.post('/announcements/', payload)
      }
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
  await ElMessageBox.confirm(`确定删除公告「${row.title}」？`, '确认')
  await api.delete(`/announcements/${row.id}/`)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await loadCompetitions()
  await load()
  tryOpenEditFromQuery()
})

function tryOpenEditFromQuery() {
  const eid = route.query.edit
  if (!eid) return
  const row = list.value.find((a) => String(a.id) === String(eid))
  if (row) openEdit(row)
  router.replace({ query: {} })
}
</script>

<style scoped>
.title-link {
  color: var(--el-color-primary);
  text-decoration: none;
}
.title-link:hover {
  text-decoration: underline;
}
.attach-row,
.file-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.new-file {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}
.hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
}
</style>
