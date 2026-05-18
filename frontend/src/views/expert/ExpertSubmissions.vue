<template>
  <el-card>
    <template #header>
      <el-button link type="primary" @click="$router.push({ name: 'expert-competitions' })">
        返回
      </el-button>
      <span style="margin-left: 8px">竞赛编号 {{ competitionId }} 的作品</span>
    </template>
    <el-alert
      v-if="!reviewing"
      type="info"
      show-icon
      :closable="false"
      title="管理员需将竞赛状态设为「评审中」后，专家才可提交或修改评分。"
      style="margin-bottom: 12px"
    />
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="作品编号" width="90" />
      <el-table-column prop="team_name" label="队伍" width="140" />
      <el-table-column prop="description" label="说明" min-width="160" show-overflow-tooltip />
      <el-table-column label="附件" min-width="220">
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
      <el-table-column label="平均分" width="100">
        <template #default="{ row }">
          {{ row.average_score != null ? Number(row.average_score).toFixed(2) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openReview(row)">打分</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="评审" width="520px">
      <template v-if="currentSubmission?.attachments?.length">
        <div class="sub-attachments">
          <div class="lbl">作品附件</div>
          <div v-for="a in currentSubmission.attachments" :key="a.id" class="att-line">
            <el-link type="primary" :href="mediaFileUrl(a.file)" target="_blank" rel="noopener noreferrer">
              {{ a.original_name || '下载' }}
            </el-link>
          </div>
        </div>
      </template>
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item label="分数" required>
          <el-input-number v-model="reviewForm.score" :min="0" :max="100" :step="0.5" />
        </el-form-item>
        <el-form-item label="评语">
          <el-input v-model="reviewForm.comment" type="textarea" rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveReview">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { getErrorMessage } from '../../api/http'

const route = useRoute()
const competitionId = computed(() => route.params.id)
const loading = ref(false)
const submissions = ref([])
const competition = ref(null)
const dialogVisible = ref(false)
const saving = ref(false)
const currentSubmission = ref(null)
const existingReviewId = ref(null)
const reviewForm = ref({ score: 80, comment: '' })

const rows = computed(() => submissions.value)

const reviewing = computed(() => competition.value?.status === 'reviewing')

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

async function loadCompetition() {
  try {
    const { data } = await api.get(`/competitions/${competitionId.value}/`)
    competition.value = data
  } catch {
    competition.value = null
  }
}

async function loadSubmissions() {
  loading.value = true
  try {
    const { data } = await api.get('/submissions/', {
      params: { competition: competitionId.value },
    })
    submissions.value = data.results ?? data
  } finally {
    loading.value = false
  }
}

async function openReview(row) {
  currentSubmission.value = row
  existingReviewId.value = null
  reviewForm.value = { score: 80, comment: '' }
  try {
    const { data } = await api.get('/reviews/', { params: { submission: row.id } })
    const list = data.results ?? data
    if (list.length) {
      const r = list[0]
      existingReviewId.value = r.id
      reviewForm.value = { score: Number(r.score), comment: r.comment || '' }
    }
  } catch {
    /* 忽略 */
  }
  dialogVisible.value = true
}

async function saveReview() {
  if (!currentSubmission.value) return
  saving.value = true
  try {
    const payload = {
      submission: currentSubmission.value.id,
      score: reviewForm.value.score,
      comment: reviewForm.value.comment || '',
    }
    if (existingReviewId.value) {
      await api.patch(`/reviews/${existingReviewId.value}/`, payload)
    } else {
      await api.post('/reviews/', payload)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    await loadSubmissions()
  } catch (e) {
    ElMessage.error(getErrorMessage(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

watch(
  () => route.params.id,
  async () => {
    await loadCompetition()
    await loadSubmissions()
  },
)

onMounted(async () => {
  await loadCompetition()
  await loadSubmissions()
})
</script>

<style scoped>
.sub-attachments {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
}
.sub-attachments .lbl {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.att-line + .att-line {
  margin-top: 6px;
}
</style>
