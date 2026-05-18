<template>
  <el-card>
    <template #header>报名审核</template>
    <el-form inline style="margin-bottom: 12px">
      <el-form-item label="竞赛">
        <el-select v-model="filterCompetition" clearable placeholder="全部" style="width: 220px">
          <el-option v-for="c in competitions" :key="c.id" :label="c.title" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">筛选</el-button>
      </el-form-item>
    </el-form>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="编号" width="70" />
      <el-table-column label="队伍" width="160">
        <template #default="{ row }">
          <el-button type="primary" link @click="openTeamDetail(row)">{{ row.team_name }}</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="competition" label="竞赛编号" width="100" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending'"
            type="success"
            link
            @click="setStatus(row, 'approved')"
          >
            通过
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            type="danger"
            link
            @click="setStatus(row, 'rejected')"
          >
            拒绝
          </el-button>
          <el-button type="danger" link @click="remove(row)">删除记录</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="teamDialogVisible"
      :title="teamDetail?.name ? `队伍：${teamDetail.name}` : '队伍详情'"
      width="640px"
      destroy-on-close
      @closed="onTeamDialogClosed"
    >
      <div v-loading="teamDialogLoading">
        <template v-if="teamDetail && registrationContext">
          <el-alert
            v-if="registrationContext.status === 'pending'"
            type="info"
            :closable="false"
            show-icon
            class="reg-hint"
            title="当前为「竞赛报名」待审核：「本竞赛资格」在管理员通过报名前均为待审核；「队内已通过成员」表示队长侧已通过入队的人数。"
          />
          <el-descriptions border :column="2" class="team-desc">
            <el-descriptions-item label="队伍名称">{{ teamDetail.name }}</el-descriptions-item>
            <el-descriptions-item label="队长">{{ teamDetail.leader_username }}（用户 ID {{ teamDetail.leader }}）</el-descriptions-item>
            <el-descriptions-item label="队内已通过成员">{{ teamDetail.approved_count }}</el-descriptions-item>
            <el-descriptions-item label="本竞赛报名状态">{{ statusText(registrationContext.status) }}</el-descriptions-item>
            <el-descriptions-item label="创建时间" :span="2">{{ fmt(teamDetail.created_at) }}</el-descriptions-item>
          </el-descriptions>
          <div class="mem-title">成员名单</div>
          <el-table :data="teamMemberships" border size="small" max-height="320">
            <el-table-column prop="student_username" label="用户名" width="140" />
            <el-table-column label="用户 ID" width="90">
              <template #default="{ row }">{{ row.student }}</template>
            </el-table-column>
            <el-table-column label="角色" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.student === teamDetail.leader" type="warning" size="small">队长</el-tag>
                <span v-else>成员</span>
              </template>
            </el-table-column>
            <el-table-column label="本竞赛资格" width="110">
              <template #default="{ row }">{{ registrationQualificationText(row) }}</template>
            </el-table-column>
            <el-table-column label="申请/加入时间" min-width="170">
              <template #default="{ row }">{{ fmt(row.joined_at) }}</template>
            </el-table-column>
          </el-table>
        </template>
      </div>
      <template #footer>
        <el-button @click="teamDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'

const loading = ref(false)
const list = ref([])
const competitions = ref([])
const filterCompetition = ref(null)

const teamDialogVisible = ref(false)
const teamDialogLoading = ref(false)
const teamDetail = ref(null)
const teamMemberships = ref([])
/** 打开弹窗时的报名记录，用于展示「本竞赛资格」与报名状态 */
const registrationContext = ref(null)

const rows = computed(() => list.value)

function statusText(s) {
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[s] || '未知'
}

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

/** 与当前报名记录一致：管理员通过前为待审核，通过后为已通过 */
function registrationQualificationText(_membershipRow) {
  const reg = registrationContext.value
  if (!reg) return '—'
  return statusText(reg.status)
}

function onTeamDialogClosed() {
  registrationContext.value = null
  teamDetail.value = null
  teamMemberships.value = []
}

async function openTeamDetail(row) {
  const tid = row.team
  if (tid == null) return
  registrationContext.value = row
  teamDialogVisible.value = true
  teamDetail.value = null
  teamMemberships.value = []
  teamDialogLoading.value = true
  try {
    const [t, m] = await Promise.all([
      api.get(`/teams/${tid}/`),
      api.get('/memberships/', { params: { team: tid } }),
    ])
    const raw = m.data.results ?? m.data
    teamDetail.value = t.data
    const lid = t.data.leader
    teamMemberships.value = [...raw].sort((a, b) => {
      if (a.student === lid && b.student !== lid) return -1
      if (b.student === lid && a.student !== lid) return 1
      return 0
    })
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '加载队伍信息失败'))
    teamDialogVisible.value = false
    registrationContext.value = null
  } finally {
    teamDialogLoading.value = false
  }
}

async function loadCompetitions() {
  const { data } = await api.get('/competitions/')
  competitions.value = data.results ?? data
}

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filterCompetition.value) params.competition = filterCompetition.value
    const { data } = await api.get('/registrations/', { params })
    list.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

async function setStatus(row, status) {
  try {
    await api.patch(`/registrations/${row.id}/`, { status })
    ElMessage.success('已更新')
    await load()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '失败'))
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm('删除后可重新报名（如竞赛仍开放报名）。确定删除？', '确认')
    await api.delete(`/registrations/${row.id}/`)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  await loadCompetitions()
  await load()
})
</script>

<style scoped>
.team-desc {
  margin-bottom: 16px;
}
.mem-title {
  font-weight: 600;
  margin-bottom: 10px;
  font-size: 14px;
}
.reg-hint {
  margin-bottom: 12px;
}
</style>
