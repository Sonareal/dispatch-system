<template>
  <div class="login-page">
    <!-- Left visual panel - Horse/黑马 themed -->
    <div class="login-visual" hidden md:flex>
      <div class="visual-content">
        <!-- Horse silhouette background - emoji 🐎 style -->
        <div class="horse-bg">
          <svg viewBox="0 0 200 200" fill="rgba(255,255,255,0.1)" xmlns="http://www.w3.org/2000/svg" class="horse-svg">
            <path d="M 130 25 C 125 20, 115 18, 110 22 C 105 26, 108 32, 112 35 L 108 38 C 100 35, 90 38, 85 45 C 78 55, 72 70, 68 85 C 64 100, 62 115, 65 130 C 67 140, 72 148, 78 155 C 82 160, 88 163, 95 165 L 110 170 C 115 171, 118 168, 118 164 L 118 158 C 120 155, 118 150, 115 148 C 112 145, 108 140, 105 135 L 105 125 C 115 130, 125 128, 132 122 C 138 116, 142 108, 144 100 C 146 90, 145 80, 140 72 C 135 62, 128 58, 125 55 C 128 50, 132 45, 138 42 C 142 40, 145 35, 142 30 C 140 27, 135 25, 130 25 Z"/>
            <path d="M 112 35 C 115 28, 120 22, 118 18 C 116 14, 110 16, 108 20 C 106 24, 108 30, 112 35 Z"/>
            <path d="M 130 25 C 135 30, 140 40, 138 50 C 136 55, 130 58, 128 62 C 140 55, 150 52, 155 48 C 148 58, 140 65, 135 72 C 145 68, 152 66, 158 65 C 152 72, 144 78, 138 82 C 146 80, 152 80, 156 82 C 150 88, 144 92, 140 95 Z" opacity="0.7"/>
          </svg>
        </div>

        <div class="visual-info">
          <div class="visual-logo-row">
            <svg viewBox="0 0 200 200" fill="white" xmlns="http://www.w3.org/2000/svg" class="logo-icon">
              <path d="M 130 25 C 125 20, 115 18, 110 22 C 105 26, 108 32, 112 35 L 108 38 C 100 35, 90 38, 85 45 C 78 55, 72 70, 68 85 C 64 100, 62 115, 65 130 C 67 140, 72 148, 78 155 C 82 160, 88 163, 95 165 L 110 170 C 115 171, 118 168, 118 164 L 118 158 C 120 155, 118 150, 115 148 C 112 145, 108 140, 105 135 L 105 125 C 115 130, 125 128, 132 122 C 138 116, 142 108, 144 100 C 146 90, 145 80, 140 72 C 135 62, 128 58, 125 55 C 128 50, 132 45, 138 42 C 142 40, 145 35, 142 30 C 140 27, 135 25, 130 25 Z"/>
              <path d="M 112 35 C 115 28, 120 22, 118 18 C 116 14, 110 16, 108 20 C 106 24, 108 30, 112 35 Z"/>
              <circle cx="108" cy="72" r="6" fill="#1565c0"/>
              <circle cx="109" cy="71" r="3" fill="white"/>
              <path d="M 130 25 C 135 30, 140 40, 138 50 C 136 55, 130 58, 128 62 C 140 55, 150 52, 155 48 C 148 58, 140 65, 135 72 C 145 68, 152 66, 158 65 C 152 72, 144 78, 138 82 C 146 80, 152 80, 156 82 C 150 88, 144 92, 140 95 Z" opacity="0.7"/>
            </svg>
            <h1 class="visual-title">{{ $t('app_name') }}</h1>
          </div>
          <p class="visual-subtitle">{{ $t('views.login.subtitle') }}</p>

          <div class="visual-features">
            <div class="feature-item">
              <TheIcon icon="mdi:clipboard-check-outline" :size="20" color="rgba(255,255,255,0.9)" />
              <span>{{ locale === 'cn' ? '智能派单调度' : 'Smart Dispatch' }}</span>
            </div>
            <div class="feature-item">
              <TheIcon icon="mdi:map-marker-radius" :size="20" color="rgba(255,255,255,0.9)" />
              <span>{{ locale === 'cn' ? '多城市区域管理' : 'Multi-city Management' }}</span>
            </div>
            <div class="feature-item">
              <TheIcon icon="mdi:shield-check" :size="20" color="rgba(255,255,255,0.9)" />
              <span>{{ locale === 'cn' ? '全流程权限控制' : 'Full RBAC Control' }}</span>
            </div>
            <div class="feature-item">
              <TheIcon icon="mdi:message-text-outline" :size="20" color="rgba(255,255,255,0.9)" />
              <span>{{ locale === 'cn' ? '实时沟通协作' : 'Real-time Communication' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right login form -->
    <div class="login-form-panel">
      <div class="login-form-wrapper">
        <!-- Language switch -->
        <div class="lang-switch">
          <n-button quaternary size="small" @click="toggleLocale">
            <TheIcon icon="mdi:translate" :size="16" style="margin-right: 4px" />
            {{ locale === 'cn' ? 'English' : '中文' }}
          </n-button>
        </div>

        <div class="form-header">
          <svg viewBox="0 0 200 200" fill="#1976d2" xmlns="http://www.w3.org/2000/svg" class="form-logo">
            <path d="M 130 25 C 125 20, 115 18, 110 22 C 105 26, 108 32, 112 35 L 108 38 C 100 35, 90 38, 85 45 C 78 55, 72 70, 68 85 C 64 100, 62 115, 65 130 C 67 140, 72 148, 78 155 C 82 160, 88 163, 95 165 L 110 170 C 115 171, 118 168, 118 164 L 118 158 C 120 155, 118 150, 115 148 C 112 145, 108 140, 105 135 L 105 125 C 115 130, 125 128, 132 122 C 138 116, 142 108, 144 100 C 146 90, 145 80, 140 72 C 135 62, 128 58, 125 55 C 128 50, 132 45, 138 42 C 142 40, 145 35, 142 30 C 140 27, 135 25, 130 25 Z"/>
            <path d="M 112 35 C 115 28, 120 22, 118 18 C 116 14, 110 16, 108 20 C 106 24, 108 30, 112 35 Z"/>
            <circle cx="108" cy="72" r="6" fill="white"/>
            <circle cx="109" cy="71" r="3" fill="#1976d2"/>
            <path d="M 130 25 C 135 30, 140 40, 138 50 C 136 55, 130 58, 128 62 C 140 55, 150 52, 155 48 C 148 58, 140 65, 135 72 C 145 68, 152 66, 158 65 C 152 72, 144 78, 138 82 C 146 80, 152 80, 156 82 C 150 88, 144 92, 140 95 Z" opacity="0.6"/>
          </svg>
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
            class="login-btn"
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
import { useAppStore } from '@/store'
import api from '@/api'
import { addDynamicRoutes } from '@/router'
import { useI18n } from 'vue-i18n'
import TheIcon from '@/components/icon/TheIcon.vue'

const router = useRouter()
const { query } = useRoute()
const { t, locale } = useI18n({ useScope: 'global' })
const appStore = useAppStore()

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
  const newLocale = locale.value === 'cn' ? 'en' : 'cn'
  appStore.setLocale(newLocale)
  window.location.reload()
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
  background: #f5f7fa;
}

.login-visual {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #0d47a1 0%, #1565c0 25%, #1976d2 50%, #2196f3 75%, #42a5f5 100%);
  position: relative;
  overflow: hidden;
}

/* Animated floating circles */
.login-visual::before {
  content: '';
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
  top: -150px;
  right: -80px;
  animation: float 8s ease-in-out infinite;
}

.login-visual::after {
  content: '';
  position: absolute;
  width: 350px;
  height: 350px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
  bottom: -80px;
  left: -40px;
  animation: float 10s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.visual-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.horse-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  max-width: 500px;
}

.horse-svg {
  width: 100%;
  height: auto;
}

.visual-info {
  position: relative;
  z-index: 2;
  text-align: center;
  color: white;
  padding: 40px;
}

.visual-logo-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.logo-icon {
  width: 56px;
  height: 56px;
}

.visual-title {
  font-size: 30px;
  font-weight: 800;
  color: white;
  margin: 0;
  letter-spacing: 2px;
}

.visual-subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0 0 48px 0;
}

.visual-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 24px;
  max-width: 360px;
  margin: 0 auto;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.08);
  padding: 10px 14px;
  border-radius: 8px;
  backdrop-filter: blur(4px);
}

/* Right panel */
.login-form-panel {
  width: 460px;
  min-width: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  box-shadow: -4px 0 30px rgba(0, 0, 0, 0.08);
}

.login-form-wrapper {
  width: 100%;
  max-width: 340px;
  padding: 40px 36px;
}

.lang-switch {
  text-align: right;
  margin-bottom: 16px;
}

.form-header {
  text-align: center;
  margin-bottom: 36px;
}

.form-logo {
  width: 52px;
  height: 52px;
  margin-bottom: 4px;
}

.form-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 10px 0 4px;
}

.form-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  font-size: 13px;
  font-weight: 500;
  color: #555;
}

.login-btn {
  margin-top: 6px;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
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
