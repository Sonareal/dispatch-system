<template>
  <div class="login-page">
    <!-- Left visual panel -->
    <div class="login-visual" hidden md:flex>
      <div class="visual-content">
        <div class="visual-logo">
          <icon-custom-logo text-60 color-white />
          <h1 class="visual-title">{{ $t('app_name') }}</h1>
        </div>
        <p class="visual-subtitle">{{ $t('views.login.subtitle') }}</p>
        <div class="visual-illustration">
          <icon-custom-front-page text-280 color-white style="opacity: 0.15" />
        </div>
      </div>
    </div>

    <!-- Right login form -->
    <div class="login-form-panel">
      <div class="login-form-wrapper">
        <!-- Language switch -->
        <div class="lang-switch">
          <n-button quaternary size="small" @click="toggleLocale">
            {{ locale === 'cn' ? 'EN' : '中文' }}
          </n-button>
        </div>

        <div class="form-header">
          <icon-custom-logo text-42 color-primary />
          <h2 class="form-title">{{ $t('views.login.text_welcome_back') }}</h2>
          <p class="form-subtitle">{{ $t('views.login.text_sign_in_to_continue') }}</p>
        </div>

        <div class="form-body">
          <div class="input-group">
            <label class="input-label">{{ $t('views.login.label_username') }}</label>
            <n-input
              v-model:value="loginInfo.username"
              autofocus
              size="large"
              :placeholder="$t('views.login.placeholder_username')"
              :maxlength="20"
            >
              <template #prefix>
                <TheIcon icon="mdi:account-outline" :size="18" color="#999" />
              </template>
            </n-input>
          </div>

          <div class="input-group">
            <label class="input-label">{{ $t('views.login.label_password') }}</label>
            <n-input
              v-model:value="loginInfo.password"
              size="large"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.login.placeholder_password')"
              :maxlength="20"
              @keypress.enter="handleLogin"
            >
              <template #prefix>
                <TheIcon icon="mdi:lock-outline" :size="18" color="#999" />
              </template>
            </n-input>
          </div>

          <n-button
            type="primary"
            size="large"
            block
            :loading="loading"
            style="margin-top: 8px; height: 44px; border-radius: 8px; font-size: 15px;"
            @click="handleLogin"
          >
            {{ $t('views.login.text_login') }}
          </n-button>
        </div>

        <div class="form-footer">
          <span class="copyright">&copy; {{ new Date().getFullYear() }} {{ $t('app_name') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { lStorage, setToken } from '@/utils'
import api from '@/api'
import { addDynamicRoutes } from '@/router'
import { useI18n } from 'vue-i18n'
import TheIcon from '@/components/icon/TheIcon.vue'

const router = useRouter()
const { query } = useRoute()
const { t, locale } = useI18n({ useScope: 'global' })

const loginInfo = ref({
  username: '',
  password: '',
})

initLoginInfo()

function initLoginInfo() {
  const localLoginInfo = lStorage.get('loginInfo')
  if (localLoginInfo) {
    loginInfo.value.username = localLoginInfo.username || ''
    loginInfo.value.password = localLoginInfo.password || ''
  }
}

function toggleLocale() {
  locale.value = locale.value === 'cn' ? 'en' : 'cn'
  localStorage.setItem('locale', locale.value)
}

const loading = ref(false)
async function handleLogin() {
  const { username, password } = loginInfo.value
  if (!username || !password) {
    $message.warning(t('views.login.message_input_username_password'))
    return
  }
  try {
    loading.value = true
    $message.loading(t('views.login.message_verifying'))
    const res = await api.login({ username, password: password.toString() })
    $message.success(t('views.login.message_login_success'))
    setToken(res.data.access_token)
    await addDynamicRoutes()
    if (query.redirect) {
      const path = query.redirect
      Reflect.deleteProperty(query, 'redirect')
      router.push({ path, query })
    } else {
      router.push('/')
    }
  } catch (e) {
    console.error('login error', e.error)
  }
  loading.value = false
}
</script>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

.login-visual {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a6dd1 0%, #2d8cf0 30%, #6366f1 70%, #8b5cf6 100%);
  position: relative;
  overflow: hidden;
}

.login-visual::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  top: -200px;
  right: -100px;
}

.login-visual::after {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  bottom: -100px;
  left: -50px;
}

.visual-content {
  position: relative;
  z-index: 1;
  text-align: center;
  color: white;
  padding: 40px;
}

.visual-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.visual-title {
  font-size: 28px;
  font-weight: 700;
  color: white;
  margin: 0;
}

.visual-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 40px 0;
}

.visual-illustration {
  margin-top: 20px;
}

.login-form-panel {
  width: 480px;
  min-width: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.05);
}

.login-form-wrapper {
  width: 100%;
  max-width: 360px;
  padding: 40px 40px;
}

.lang-switch {
  text-align: right;
  margin-bottom: 20px;
}

.form-header {
  text-align: center;
  margin-bottom: 36px;
}

.form-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin: 12px 0 4px;
}

.form-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.form-footer {
  margin-top: 40px;
  text-align: center;
}

.copyright {
  font-size: 12px;
  color: #ccc;
}

@media (max-width: 768px) {
  .login-form-panel {
    width: 100%;
    min-width: auto;
  }
}
</style>
