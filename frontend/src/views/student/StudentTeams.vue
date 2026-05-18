<template>
  <el-card>
    <template #header>
      <span>队伍管理</span>
      <el-button type="primary" style="float: right" @click="openCreate">创建队伍</el-button>
    </template>

    <el-form :inline="true" style="margin-bottom: 16px" @submit.prevent="searchTeam">
      <el-form-item label="队伍ID">
        <el-input v-model="searchId" placeholder="输入队伍ID搜索" style="width: 200px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="searching" @click="searchTeam">搜索</el-button>
      </el-form-item>
    </el-form>

    <el-card v-if="foundTeam" style="margin-bottom: 16px">
      <template #header>搜索结果</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="队伍ID">{{ foundTeam.id }}</el-descriptions-item>
        <el-descriptions-item label="队伍名称">{{ foundTeam.name }}</el-descriptions-item>
        <el-descriptions-item label="队长">{{ foundTeam.leader_username }}</el-descriptions-item>
        <el-descriptions-item label="成员数">{{ foundTeam.approved_count }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ fmt(foundTeam.created_at) }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 12px">
        <el-tag v-if="isAlreadyInTeam" type="info">您已是该队伍成员</el-tag>
        <el-button v-else type="success" :loading="joining" @click="joinFoundTeam">申请加入</el-button>
      </div>
    </el-card>

    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="队伍ID" width="80" />
      <el-table-column prop="name" label="队伍名称" min-width="160" />
      <el-table-column prop="leader_username" label="队长" width="120" />
      <el-table-column prop="approved_count" label="成员数" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="$router.push({ name: 'student-team-detail', params: { id: row.id } })">
            管理
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" title="创建队伍" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
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
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import api, { getErrorMessage } from '../../api/http'

const auth = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const visible = ref(false)
const form = ref({ name: '' })

const searchId = ref('')
const searching = ref(false)
const foundTeam = ref(null)
const joining = ref(false)

const rows = computed(() => list.value)

const isAlreadyInTeam = computed(() => {
  if (!foundTeam.value) return false
  return list.value.some((t) => t.id === foundTeam.value.id)
})

async function searchTeam() {
  const id = Number(searchId.value)
  if (!id) return ElMessage.warning('请输入队伍ID')
  searching.value = true
  foundTeam.value = null
  try {
    const { data } = await api.get(`/teams/${id}/`, { params: { all: '1' } })
    foundTeam.value = data
  } catch (e) {
    if (e.response?.status === 404) {
      ElMessage.warning('队伍不存在')
    } else {
      ElMessage.error('搜索失败')
    }
  } finally {
    searching.value = false
  }
}

async function joinFoundTeam() {
  if (!foundTeam.value) return
  joining.value = true
  try {
    await api.post('/memberships/', { team: foundTeam.value.id })
    ElMessage.success('申请已提交，请等待队长审核')
    foundTeam.value = null
    searchId.value = ''
    await load()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '申请失败'))
  } finally {
    joining.value = false
  }
}

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/teams/')
    list.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { name: '' }
  visible.value = true
}

async function save() {
  if (!form.value.name) return ElMessage.warning('请输入队伍名称')
  saving.value = true
  try {
    const { data: newTeam } = await api.post('/teams/', { name: form.value.name })
    ElMessage.success(`队伍「${newTeam.name}」已创建，队伍ID：${newTeam.id}`)
    visible.value = false
    await load()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '创建失败'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
