const { getToken } = require('./utils/auth')

App({
  onLaunch() {
    this.checkLogin()
  },

  globalData: {
    userInfo: null,
    baseUrl: 'http://localhost:9999/api/v1'
  },

  checkLogin() {
    const token = getToken()
    if (!token) {
      wx.redirectTo({
        url: '/pages/login/login'
      })
      return false
    }
    return true
  },

  getUserInfo() {
    return this.globalData.userInfo
  },

  setUserInfo(info) {
    this.globalData.userInfo = info
  }
})
