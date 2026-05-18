<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="brand">竞赛管理系统</div>
      <div class="right">
        <span v-if="auth.user" class="user">{{ auth.user.username }}（{{ roleLabel }}）</span>
        <el-button v-if="auth.user" type="primary" link @click="onLogout">退出</el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside v-if="auth.user" width="220px" class="aside">
        <el-menu :default-active="menuActivePath" router>
          <template v-if="auth.user?.role === 'student'">
            <el-menu-item index="/student/competitions">竞赛列表</el-menu-item>
            <el-menu-item index="/student/teams">队伍管理</el-menu-item>
            <el-menu-item index="/student/registrations">我的报名</el-menu-item>
            <el-menu-item index="/student/submissions">我的作品</el-menu-item>
            <el-menu-item index="/student/announcements">
              <span class="menu-ann-row">
                <span>公告</span>
                <span
                  v-if="(auth.user?.unread_announcement_count ?? 0) > 0"
                  class="menu-ann-dot"
                  aria-hidden="true"
                />
              </span>
            </el-menu-item>
          </template>
          <template v-else-if="auth.user?.role === 'expert'">
            <el-menu-item index="/expert/competitions">评审任务</el-menu-item>
          </template>
          <template v-else-if="auth.user?.role === 'admin'">
            <el-menu-item index="/admin/competitions">竞赛管理</el-menu-item>
            <el-menu-item index="/admin/registrations">报名审核</el-menu-item>
            <el-menu-item index="/admin/submissions">作品评分</el-menu-item>
            <el-menu-item index="/admin/announcements">公告管理</el-menu-item>
          </template>
        </el-menu>
      </el-aside>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const menuActivePath = computed(() => {
  if (auth.user?.role === 'student') {
    if (route.path.match(/^\/student\/announcements\/\d+$/)) {
      return '/student/announcements'
    }
  }
  if (auth.user?.role === 'admin') {
    if (route.path.match(/^\/admin\/announcements\/\d+$/)) {
      return '/admin/announcements'
    }
  }
  return route.path
})

const roleLabel = computed(() => {
  const r = auth.user?.role
  if (r === 'admin') return '管理员'
  if (r === 'expert') return '专家'
  return '学生'
})

async function onLogout() {
  await auth.logout()
  ElMessage.success('已退出')
  router.push({ name: 'login' })
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
}
.brand {
  font-weight: 600;
}
.right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user {
  color: #666;
  font-size: 14px;
}
.aside {
  border-right: 1px solid #eee;
}
.main {
  background: #fafafa;
  min-height: calc(100vh - 60px);
}
.menu-ann-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.menu-ann-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-color-danger);
  flex-shrink: 0;
}
</style>
