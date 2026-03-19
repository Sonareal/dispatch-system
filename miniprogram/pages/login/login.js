const { post } = require('../../utils/request')
const { setToken, setUserInfo } = require('../../utils/auth')

Page({
  data: {
    username: '',
    password: '',
    loading: false,
    showPassword: false
  },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value.trim() })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },

  async handleLogin() {
    const { username, password, loading } = this.data

    if (loading) return

    if (!username) {
      wx.showToast({ title: '请输入用户名', icon: 'none' })
      return
    }
    if (!password) {
      wx.showToast({ title: '请输入密码', icon: 'none' })
      return
    }

    this.setData({ loading: true })

    try {
      const res = await post('/base/access_token', {
        username,
        password
      })

      const data = res.data || res
      if (data.access_token) {
        setToken(data.access_token)
      }

      wx.showToast({ title: '登录成功', icon: 'success' })

      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 1000)
    } catch (err) {
      console.error('Login failed:', err)
    } finally {
      this.setData({ loading: false })
    }
  }
})
