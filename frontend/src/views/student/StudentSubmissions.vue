<template>
  <el-card>
    <template #header>
      <span>我的作品</span>
      <el-button type="primary" style="float: right" @click="openCreate">新建提交</el-button>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="team_name" label="队伍" width="120" />
      <el-table-column prop="competition" label="竞赛编号" width="100" />
      <el-table-column prop="description" label="说明" min-width="160" show-overflow-tooltip />
      <el-table-column label="附件" min-width="200">
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
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑作品' : '新建作品'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="队伍" required>
          <el-select v-model="form.team" :disabled="!!editingId" style="width: 100%">
            <el-option v-for="t in availableTeams" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="竞赛" required>
          <el-select v-model="form.competition" :disabled="!!editingId" filterable style="width: 100%">
            <el-option
              v-for="c in availableCompetitions"
              :key="c.id"
              :label="`${c.title}（编号 ${c.id}）`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item v-if="editingId && keptAttachments.length" label="已有附件">
          <div v-for="a in keptAttachments" :key="a.id" class="att-row">
            <el-link type="primary" :href="mediaFileUrl(a.file)" target="_blank" rel="noopener noreferrer">
              {{ a.original_name || '文件' }}
            </el-link>
            <el-button type="danger" link @click="removeKeptAttachment(a)">移除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="添加附件">
          <input :key="fileInputKey" type="file" multiple @change="onPickFiles" />
          <div v-for="(f, i) in newFiles" :key="i + f.name" class="att-row new-file">
            <span>{{ f.name }}</span>
            <el-button type="danger" link @click="removeNewFile(i)">去掉</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'

const loading = ref(false)
const submissions = ref([])
const registrations = ref([])
const myTeams = ref([])
const competitions = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const form = ref({ team: null, competition: null, description: '' })
const keptAttachments = ref([])
const pendingDeleteIds = ref([])
const newFiles = ref([])
const fileInputKey = ref(0)

const rows = computed(() => submissions.value)

const approvedRegs = computed(() => registrations.value.filter((r) => r.status === 'approved'))

const availableTeams = computed(() => {
  const ids = new Set(approvedRegs.value.map((r) => r.team))
  return myTeams.value.filter((t) => ids.has(t.id))
})

const availableCompetitions = computed(() => {
  if (!form.value.team) return []
  const compIds = approvedRegs.value
    .filter((r) => r.team === form.value.team)
    .map((r) => r.competition)
  return competitions.value.filter(
    (c) => compIds.includes(c.id) && (c.status === 'published' || c.status === 'registration_closed'),
  )
})

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

async function load() {
  loading.value = true
  try {
    const [s, r, t, c] = await Promise.all([
      api.get('/submissions/'),
      api.get('/registrations/'),
      api.get('/teams/'),
      api.get('/competitions/'),
    ])
    submissions.value = s.data.results ?? s.data
    registrations.value = r.data.results ?? r.data
    myTeams.value = t.data.results ?? t.data
    competitions.value = c.data.results ?? c.data
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
  editingId.value = null
  form.value = { team: null, competition: null, description: '' }
  resetDialogFiles()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = {
    team: row.team,
    competition: row.competition,
    description: row.description || '',
  }
  keptAttachments.value = [...(row.attachments || [])]
  pendingDeleteIds.value = []
  newFiles.value = []
  fileInputKey.value += 1
  dialogVisible.value = true
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

async function save() {
  if (!editingId.value) {
    if (!form.value.team) return ElMessage.warning('请选择队伍')
    if (!form.value.competition) return ElMessage.warning('请选择竞赛')
  }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('description', form.value.description || '')
    if (pendingDeleteIds.value.length) {
      fd.append('delete_attachment_ids', pendingDeleteIds.value.join(','))
    }
    for (const f of newFiles.value) {
      fd.append('attachments', f)
    }
    if (editingId.value) {
      await api.patch(`/submissions/${editingId.value}/`, fd)
    } else {
      fd.append('team', String(form.value.team))
      fd.append('competition', String(form.value.competition))
      await api.post('/submissions/', fd)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.att-line + .att-line {
  margin-top: 4px;
}
.att-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.new-file {
  font-size: 13px;
  color: var(--el-text-color-regular);
}
</style>
