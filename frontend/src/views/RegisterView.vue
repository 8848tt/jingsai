<template>
  <div class="wrap">
    <el-card class="card" header="注册（学生）">
      <el-form :model="form" label-width="120px" class="register-form" @submit.prevent="onSubmit">
        <el-form-item label="用户名（学号）">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" type="email" autocomplete="email" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading">注册并登录</el-button>
          <el-button link type="primary" @click="$router.push({ name: 'login' })">返回登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '', email: '' })

async function onSubmit() {
  loading.value = true
  try {
    await auth.register({
      username: form.username,
      password: form.password,
      email: form.email || undefined,
    })
    ElMessage.success('注册成功')
    router.push('/student/competitions')
  } catch (e) {
    const msg = e.response?.data
    ElMessage.error(
      typeof msg === 'object' ? JSON.stringify(msg) : msg || '注册失败',
    )
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.card {
  width: 440px;
}

.register-form :deep(.el-form-item__label) {
  white-space: nowrap;
}
</style>
