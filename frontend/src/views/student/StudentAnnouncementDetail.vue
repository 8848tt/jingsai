<template>
  <div class="page">
    <div class="toolbar">
      <el-button type="primary" link @click="goBack">
        <span class="back-icon">‹</span> 返回
      </el-button>
    </div>

    <el-card v-loading="loading" class="main-card" shadow="hover">
      <template v-if="detail">
        <h1 class="title">{{ detail.title }}</h1>
        <div class="meta">
          <el-tag v-if="detail.competition != null" size="small" type="info">竞赛 {{ detail.competition }}</el-tag>
          <el-tag v-else size="small" type="success">全局</el-tag>
          <span class="meta-dot">·</span>
          <span>{{ fmt(detail.published_at) }}</span>
        </div>
        <el-divider class="divider" />
        <div class="body">{{ detail.body }}</div>
        <div class="att-section">
          <h2 class="att-heading">附件</h2>
          <ul v-if="detail.attachments?.length" class="att-list">
            <li v-for="a in detail.attachments" :key="a.id">
              <a class="file-a" :href="absMediaUrl(fileUrl(a.file))" target="_blank" rel="noopener noreferrer">
                {{ a.original_name || '打开附件' }}
              </a>
            </li>
          </ul>
          <p v-else class="muted">暂无附件</p>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const detail = ref(null)

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

function goBack() {
  if (route.query.from === 'competitions') {
    router.push({ name: 'student-competitions' })
  } else {
    router.push({ name: 'student-announcements' })
  }
}

async function load() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const { data } = await api.get(`/announcements/${id}/`)
    detail.value = data
    try {
      await api.post(`/announcements/${id}/mark_read/`)
      await auth.fetchMe()
    } catch {
      /* 已读接口失败不影响阅读 */
    }
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '加载失败'))
    detail.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(
  () => route.params.id,
  () => load(),
)
</script>

<style scoped>
.page {
  max-width: 880px;
  margin: 0 auto;
}
.toolbar {
  margin-bottom: 12px;
}
.back-icon {
  margin-right: 2px;
  font-size: 18px;
  line-height: 1;
}
.main-card {
  border-radius: 12px;
}
.title {
  margin: 0 0 14px;
  font-size: 24px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--el-text-color-primary);
}
.meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.meta-dot {
  margin: 0 4px;
  opacity: 0.5;
}
.divider {
  margin: 20px 0;
}
.body {
  white-space: pre-wrap;
  line-height: 1.75;
  font-size: 15px;
  color: var(--el-text-color-regular);
}
.att-section {
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.att-heading {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 600;
}
.att-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.att-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  border-left: 3px solid var(--el-color-primary);
}
.file-a {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
}
.file-a:hover {
  text-decoration: underline;
}
.muted {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
</style>
