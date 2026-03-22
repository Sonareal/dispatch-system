const { getToken, clearAuth } = require('./utils/auth')
const { get } = require('./utils/request')

App({
  onLaunch() {
    this.checkLogin()
  },

  globalData: {
    userInfo: null,
    baseUrl: 'https://168heima.cn/api/v1'
    //baseUrl: 'http://localhost:9999/api/v1'
  },

  checkLogin() {
    const token = getToken()
    if (!token) {
      wx.redirectTo({
        url: '/pages/login/login'
      })
      return false
    }
    // Validate token by calling a lightweight endpoint
    this.validateToken()
    return true
  },

  async validateToken() {
    try {
      await get('/base/userinfo', {}, { showLoading: false })
    } catch (err) {
      // If 401, the request interceptor already handles redirect
      // For other errors, token might still be valid (e.g., network issue)
      console.warn('Token validation failed:', err)
    }
  },

  getUserInfo() {
    return this.globalData.userInfo
  },

  setUserInfo(info) {
    this.globalData.userInfo = info
  }
})
