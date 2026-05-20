<template>
  <el-card>
    <template #header>
      <span>公告（已发布）</span>
      <el-select v-model="filterComp" placeholder="全部公告" clearable style="margin-left: 12px; width: 220px">
        <el-option label="全局公告" :value="FILTER_GLOBAL_ONLY" />
        <el-option v-for="c in competitions" :key="c.id" :label="c.title" :value="c.id" />
      </el-select>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="competition" label="竞赛编号" width="100">
        <template #default="{ row }">{{ row.competition != null ? row.competition : '—' }}</template>
      </el-table-column>
      <el-table-column label="竞赛名称" min-width="140">
        <template #default="{ row }">
          {{ row.competition != null ? (row.competition_title || '—') : '全局' }}
        </template>
      </el-table-column>
      <el-table-column label="公告标题" min-width="160">
        <template #default="{ row }">
          <span class="title-with-dot">
            <router-link class="title-link" :to="{ name: 'student-announcement-detail', params: { id: row.id } }">
              {{ row.title }}
            </router-link>
            <span v-if="row.is_reminder_unread" class="title-unread-dot" aria-hidden="true" title="未读提醒" />
          </span>
        </template>
      </el-table-column>
      <el-table-column label="附件" min-width="140">
        <template #default="{ row }">
          <template v-if="row.attachments?.length">
            <div v-for="a in row.attachments" :key="a.id" class="att-line">
              <a class="file-a" :href="absMediaUrl(fileUrl(a.file))" target="_blank" rel="noopener noreferrer">
                {{ a.original_name || '下载' }}
              </a>
            </div>
          </template>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="published_at" label="发布时间" width="200">
        <template #default="{ row }">{{ fmt(row.published_at) }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/http'

/** 筛选：仅显示未关联竞赛的全局公告（与竞赛 id 不会冲突） */
const FILTER_GLOBAL_ONLY = '__global_only__'

const loading = ref(false)
const list = ref([])
const competitions = ref([])
const filterComp = ref(null)

/** 同一竞赛聚在一起，组内按发布时间从新到旧；全局公告排在最后 */
function sortByCompetitionThenTime(items) {
  return [...items].sort((a, b) => {
    const gA = a.competition ?? Number.MAX_SAFE_INTEGER
    const gB = b.competition ?? Number.MAX_SAFE_INTEGER
    if (gA !== gB) return gA - gB
    const tA = Date.parse(a.published_at || a.created_at || '') || 0
    const tB = Date.parse(b.published_at || b.created_at || '') || 0
    return tB - tA
  })
}

const rows = computed(() => {
  let data = list.value
  if (filterComp.value === FILTER_GLOBAL_ONLY) {
    data = data.filter((a) => a.competition == null)
  } else if (filterComp.value) {
    data = data.filter((a) => a.competition === filterComp.value)
  }
  return sortByCompetitionThenTime(data)
})

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

function fileUrl(fileField) {
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

function absMediaUrl(path) {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const p = path.startsWith('/') ? path : `/${path}`
  return `${window.location.origin}${p}`
}

async function load() {
  loading.value = true
  try {
    const [a, c] = await Promise.all([
      api.get('/announcements/'),
      api.get('/competitions/'),
    ])
    list.value = a.data.results ?? a.data
    competitions.value = c.data.results ?? c.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.title-with-dot {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.title-unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-color-danger);
  flex-shrink: 0;
}
.title-link {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
}
.title-link:hover {
  text-decoration: underline;
}
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
</style>
