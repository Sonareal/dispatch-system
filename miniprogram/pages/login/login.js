const { post } = require('../../utils/request')
const { setToken, setUserInfo } = require('../../utils/auth')

Page({
  data: {
    username: '',
    password: '',
    loading: false,
    wxLoading: false,
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

  // WeChat one-click login
  async handleWxLogin() {
    if (this.data.wxLoading) return
    this.setData({ wxLoading: true })

    try {
      // Step 1: Get login code from WeChat
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        })
      })

      if (!loginRes.code) {
        wx.showToast({ title: '微信登录失败，请重试', icon: 'none' })
        this.setData({ wxLoading: false })
        return
      }

      // Step 2: Get user profile (nickname, avatar)
      let nickname = ''
      let avatarUrl = ''
      try {
        const profileRes = await new Promise((resolve, reject) => {
          wx.getUserProfile({
            desc: '用于登录和显示用户信息',
            success: resolve,
            fail: reject
          })
        })
        nickname = profileRes.userInfo.nickName || ''
        avatarUrl = profileRes.userInfo.avatarUrl || ''
      } catch (profileErr) {
        // User denied profile access, proceed without it
        console.warn('getUserProfile denied:', profileErr)
      }

      // Step 3: Call backend wx_login
      const res = await post('/base/wx_login', {
        code: loginRes.code,
        nickname: nickname,
        avatar_url: avatarUrl
      })

      const data = res.data || res
      if (data.access_token) {
        setToken(data.access_token)
        setUserInfo({
          username: data.username || nickname,
          nickname: nickname,
          avatar_url: avatarUrl,
          is_new_user: data.is_new_user || false
        })
        getApp().setUserInfo({
          username: data.username || nickname,
          nickname: nickname,
          avatar_url: avatarUrl,
          is_new_user: data.is_new_user || false
        })
      }

      wx.showToast({ title: '登录成功', icon: 'success' })

      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 1000)
    } catch (err) {
      console.error('WeChat login failed:', err)
    } finally {
      this.setData({ wxLoading: false })
    }
  },

  // Username/password login
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
