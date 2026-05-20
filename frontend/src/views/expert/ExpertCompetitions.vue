<template>
  <el-card>
    <template #header>分配给我的竞赛</template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'reviewing'"
            type="primary"
            link
            @click="go(row.id)"
          >
            查看作品并评审
          </el-button>
          <span v-else class="muted-hint">评审中开放</span>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api/http'

const router = useRouter()
const loading = ref(false)
const list = ref([])

const rows = computed(() => list.value)

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

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/competitions/')
    list.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

function go(id) {
  router.push({ name: 'expert-submissions', params: { id: String(id) } })
}

onMounted(load)
</script>

<style scoped>
.muted-hint {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
