<template>
  <main class="login-shell">
    <section class="login-panel">
      <div class="brand">
        <span class="mark">V</span>
        <div>
          <h1>Vitam 控制台</h1>
          <p>登录后查看你的设备与服务控制权限</p>
        </div>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <label>
          <span>账号</span>
          <input v-model.trim="username" autocomplete="username" placeholder="请输入账号" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="password" type="password" autocomplete="current-password" placeholder="请输入密码" />
        </label>
        <label v-if="mode === 'register'">
          <span>显示名称</span>
          <input v-model.trim="displayName" autocomplete="name" placeholder="可选" />
        </label>

        <p v-if="error" class="error">{{ error }}</p>
        <button class="primary-btn" :disabled="loading">
          {{ loading ? '处理中...' : mode === 'login' ? '登录' : '创建账号' }}
        </button>
      </form>

      <button class="text-btn" @click="toggleMode">
        {{ mode === 'login' ? '没有账号，创建一个' : '已有账号，返回登录' }}
      </button>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const auth = useAuth()
const mode = ref('login')
const username = ref('')
const password = ref('')
const displayName = ref('')
const error = ref('')
const loading = ref(false)

function toggleMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  error.value = ''
}

async function submit() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = '请输入账号和密码'
    return
  }
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(username.value, password.value)
    } else {
      await auth.register(username.value, password.value, displayName.value)
    }
    router.replace('/')
  } catch (err) {
    error.value = err.message || '认证失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}
.login-panel {
  width: min(420px, 100%);
  background: rgba(23, 19, 30, 0.92);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px;
  box-shadow: var(--shadow-lg);
}
.brand {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 26px;
}
.mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: var(--bg-elevated);
  color: var(--primary);
  font-weight: 800;
  border: 1px solid var(--border);
}
h1 {
  font-size: 22px;
  line-height: 1.2;
}
p {
  color: var(--text-muted);
  font-size: 13px;
}
.login-form {
  display: grid;
  gap: 14px;
}
label {
  display: grid;
  gap: 7px;
  color: var(--text-secondary);
  font-size: 13px;
}
input {
  width: 100%;
  border: 1px solid var(--border);
  background: var(--bg-body);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  padding: 11px 12px;
  outline: none;
}
input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
}
.primary-btn,
.text-btn {
  border: 0;
  cursor: pointer;
}
.primary-btn {
  margin-top: 4px;
  border-radius: var(--radius-sm);
  padding: 12px;
  background: var(--primary);
  color: white;
  font-weight: 700;
}
.primary-btn:disabled {
  opacity: 0.65;
  cursor: wait;
}
.text-btn {
  margin-top: 16px;
  width: 100%;
  background: transparent;
  color: var(--text-muted);
}
.error {
  color: var(--danger);
}
</style>
