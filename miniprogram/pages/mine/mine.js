const { get, put } = require('../../utils/request')
const { getUserInfo, setUserInfo, clearAuth, isLoggedIn } = require('../../utils/auth')

Page({
  data: {
    userInfo: null,
    cityText: '',
    loading: false
  },

  onLoad() {
    this.loadUserInfo()
  },

  onShow() {
    this.loadUserInfo()
  },

  loadUserInfo() {
    const userInfo = getUserInfo()
    if (userInfo) {
      const cityParts = [userInfo.province, userInfo.city, userInfo.district].filter(Boolean)
      this.setData({
        userInfo,
        cityText: cityParts.join(' ') || '未设置'
      })
    } else if (isLoggedIn()) {
      this.fetchUserInfo()
    }
  },

  async fetchUserInfo() {
    try {
      const res = await get('/auth/profile', {}, { showLoading: false })
      const user = res.data || res
      setUserInfo(user)
      getApp().setUserInfo(user)

      const cityParts = [user.province, user.city, user.district].filter(Boolean)
      this.setData({
        userInfo: user,
        cityText: cityParts.join(' ') || '未设置'
      })
    } catch (err) {
      console.error('Failed to fetch user info:', err)
    }
  },

  onCityChange(e) {
    const value = e.detail.value
    const province = value[0] || ''
    const city = value[1] || ''
    const district = value[2] || ''

    const cityText = [province, city, district].filter(Boolean).join(' ')
    this.setData({ cityText })

    this.updateCity(province, city, district)
  },

  async updateCity(province, city, district) {
    try {
      await put('/auth/profile', { province, city, district })

      const userInfo = { ...this.data.userInfo, province, city, district }
      setUserInfo(userInfo)
      getApp().setUserInfo(userInfo)
      this.setData({ userInfo })

      wx.showToast({ title: '城市已更新', icon: 'success' })
    } catch (err) {
      console.error('Failed to update city:', err)
    }
  },

  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      confirmColor: '#ed4014',
      success: (res) => {
        if (res.confirm) {
          clearAuth()
          getApp().setUserInfo(null)
          wx.redirectTo({ url: '/pages/login/login' })
        }
      }
    })
  },

  navigateToAbout() {
    wx.showModal({
      title: '关于',
      content: '派单管理系统 v1.0.0\n用于工单派发与管理',
      showCancel: false
    })
  },

  handleClearCache() {
    wx.showModal({
      title: '提示',
      content: '确定要清除缓存吗？清除后需要重新登录。',
      confirmColor: '#ed4014',
      success: (res) => {
        if (res.confirm) {
          try {
            wx.clearStorageSync()
            wx.showToast({ title: '缓存已清除', icon: 'success' })
            setTimeout(() => {
              wx.redirectTo({ url: '/pages/login/login' })
            }, 1500)
          } catch (e) {
            wx.showToast({ title: '清除失败', icon: 'none' })
          }
        }
      }
    })
  }
})
