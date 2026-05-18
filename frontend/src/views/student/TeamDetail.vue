<template>
  <el-card>
    <template #header>
      <el-button link type="primary" @click="$router.push({ name: 'student-teams' })">返回</el-button>
      <span style="margin-left: 8px">{{ team?.name || '队伍详情' }}</span>
      <el-button v-if="isLeader" type="danger" style="float: right" @click="delTeam">删除队伍</el-button>
    </template>

    <el-descriptions v-if="team" border :column="2" style="margin-bottom: 16px">
      <el-descriptions-item label="队伍名称">{{ team.name }}</el-descriptions-item>
      <el-descriptions-item label="队长">{{ team.leader_username }}</el-descriptions-item>
      <el-descriptions-item label="已通过成员">{{ team.approved_count }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ fmt(team.created_at) }}</el-descriptions-item>
    </el-descriptions>

    <template v-if="!isMember && !isLeader">
      <el-button type="primary" :loading="joining" @click="joinTeam">申请加入</el-button>
    </template>

    <template v-if="isLeader">
      <el-divider>成员管理</el-divider>
      <el-table v-loading="memLoading" :data="memberships" border>
        <el-table-column prop="student_username" label="用户名" width="140" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'approved'" type="success">已通过</el-tag>
            <el-tag v-else-if="row.status === 'pending'" type="warning">待审核</el-tag>
            <el-tag v-else-if="row.status === 'rejected'" type="danger">已拒绝</el-tag>
            <span v-else>未知</span>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="180">
          <template #default="{ row }">{{ fmt(row.joined_at) }}</template>
        </el-table-column>
        <el-table-column v-if="isLeader" label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" type="success" link @click="approve(row)">通过</el-button>
            <el-button v-if="row.status === 'pending'" type="danger" link @click="reject(row)">拒绝</el-button>
            <el-button
              v-if="canRemoveMember(row)"
              type="danger"
              link
              @click="removeMember(row)"
            >
              移出
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const teamId = computed(() => route.params.id)

const team = ref(null)
const memberships = ref([])
const memLoading = ref(false)
const joining = ref(false)

const isLeader = computed(
  () => team.value && authStore.user && team.value.leader === authStore.user.id,
)

const isMember = computed(() =>
  memberships.value.some(
    (m) => m.student_username === authStore.user?.username && m.status === 'approved',
  ),
)

function canRemoveMember(row) {
  if (!team.value || !isLeader.value) return false
  if (row.student === team.value.leader) return false
  return true
}

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

async function loadTeam() {
  const { data } = await api.get(`/teams/${teamId.value}/`)
  team.value = data
}

async function loadMembers() {
  memLoading.value = true
  try {
    const { data } = await api.get('/memberships/', { params: { team: teamId.value } })
    memberships.value = data.results ?? data
  } finally {
    memLoading.value = false
  }
}

async function joinTeam() {
  joining.value = true
  try {
    await api.post('/memberships/', { team: Number(teamId.value) })
    ElMessage.success('申请已提交，请等待队长审核')
    await loadMembers()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '申请失败'))
  } finally {
    joining.value = false
  }
}

async function approve(row) {
  try {
    await api.patch(`/memberships/${row.id}/`, { status: 'approved' })
    ElMessage.success('已通过')
    await Promise.all([loadTeam(), loadMembers()])
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '操作失败'))
  }
}

async function reject(row) {
  try {
    await api.patch(`/memberships/${row.id}/`, { status: 'rejected' })
    ElMessage.success('已拒绝')
    await loadMembers()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '操作失败'))
  }
}

async function removeMember(row) {
  await ElMessageBox.confirm(
    `确定将「${row.student_username}」移出队伍？`,
    '确认移出',
    { type: 'warning' },
  )
  try {
    await api.delete(`/memberships/${row.id}/`)
    ElMessage.success('已移出')
    await Promise.all([loadTeam(), loadMembers()])
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '移出失败'))
  }
}

async function delTeam() {
  await ElMessageBox.confirm('删除后将无法恢复，确定删除该队伍？', '确认')
  try {
    await api.delete(`/teams/${teamId.value}/`)
    ElMessage.success('已删除')
    router.push({ name: 'student-teams' })
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '删除失败'))
  }
}

onMounted(async () => {
  await Promise.all([loadTeam(), loadMembers()])
})
</script>
