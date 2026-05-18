<template>
  <el-card>
    <template #header>我的报名</template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="team_name" label="队伍" min-width="140" />
      <el-table-column prop="competition" label="竞赛编号" width="100" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="申请时间" width="200">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/http'

const loading = ref(false)
const list = ref([])

const rows = computed(() => list.value)

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

function statusText(s) {
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[s] || '未知'
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/registrations/')
    list.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
