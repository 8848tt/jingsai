<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="hdr">
        <el-button type="primary" link @click="goBack">← 返回公告列表</el-button>
        <el-button type="primary" link @click="goEdit">编辑</el-button>
      </div>
    </template>
    <template v-if="detail">
      <h1 class="title">{{ detail.title }}</h1>
      <div class="meta">
        {{ detail.competition != null ? `竞赛编号 ${detail.competition}` : '全局公告' }} · {{ detail.is_published ? '已发布' : '未发布' }}
        <template v-if="detail.published_at"> · {{ fmt(detail.published_at) }}</template>
        · {{ remindScopeLabel(detail.remind_scope) }}
      </div>
      <div class="body">{{ detail.body }}</div>
      <div class="att-block">
        <h2 class="att-title">附件</h2>
        <ul v-if="(detail.attachments || []).length" class="att-list">
          <li v-for="a in detail.attachments" :key="a.id">
            <el-link type="primary" :href="absMediaUrl(fileUrl(a.file))" target="_blank" rel="noopener noreferrer">
              {{ a.original_name || '下载' }}
            </el-link>
          </li>
        </ul>
        <p v-else class="muted">暂无附件</p>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref(null)

function fmt(s) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

function remindScopeLabel(scope) {
  if (scope === 'all_students') return '红点提醒：全体学生'
  if (scope === 'competition_registrants') return '红点提醒：本竞赛已报名学生'
  return '红点提醒：关闭'
}

function absMediaUrl(path) {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const p = path.startsWith('/') ? path : `/${path}`
  return `${window.location.origin}${p}`
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

async function load() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const { data } = await api.get(`/announcements/${id}/`)
    detail.value = data
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '加载失败'))
    detail.value = null
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'admin-announcements' })
}

function goEdit() {
  router.push({ name: 'admin-announcements', query: { edit: String(route.params.id) } })
}

onMounted(load)
watch(
  () => route.params.id,
  () => load(),
)
</script>

<style scoped>
.hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 600;
}
.meta {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 20px;
}
.body {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 15px;
  margin-bottom: 28px;
}
.att-block {
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 20px;
}
.att-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}
.att-list {
  margin: 0;
  padding-left: 20px;
}
.att-list li {
  margin-bottom: 8px;
}
.muted {
  color: var(--el-text-color-secondary);
  margin: 0;
}
</style>
