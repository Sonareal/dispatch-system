const { get, post } = require('../../utils/request')
const { getUserInfo, setUserInfo, clearAuth, isLoggedIn } = require('../../utils/auth')

Page({
  data: {
    userInfo: null,
    cityText: '',
    loading: false,
    // WeChat binding
    wxBound: false,
    wxOpenid: '',
    wxBindLoading: false,
    // Notification settings
    notifyNewTicket: true,
    notifyStatusChange: true,
    notifyMessage: true
  },

  onLoad() {
    this.loadUserInfo()
    this.loadNotificationSettings()
  },

  onShow() {
    this.loadUserInfo()
    this.fetchWxBindStatus()
  },

  loadUserInfo() {
    const userInfo = getUserInfo()
    if (userInfo) {
      this.setData({
        userInfo,
        cityText: userInfo.default_city_name || '未设置'
      })
    } else if (isLoggedIn()) {
      this.fetchUserInfo()
    }
  },

  async fetchUserInfo() {
    try {
      const res = await get('/base/userinfo', {}, { showLoading: false })
      const user = res.data || res
      const info = {
        id: user.id,
        username: user.username,
        name: user.alias || user.username,
        alias: user.alias,
        phone: user.phone,
        is_superuser: user.is_superuser,
        default_city_id: user.default_city_id,
        default_city_name: user.default_city_name,
        role_names: user.role_names,
      }
      setUserInfo(info)

      this.setData({
        userInfo: info,
        cityText: user.default_city_name || '未设置'
      })
    } catch (err) {
      console.error('Failed to fetch user info:', err)
    }
  },

  // === WeChat Binding ===
  async fetchWxBindStatus() {
    try {
      const res = await get('/base/wx_bindstatus', {}, { showLoading: false })
      const data = res.data || res
      this.setData({
        wxBound: !!(data.is_bound || data.bound),
        wxOpenid: data.openid || ''
      })
    } catch (err) {
      console.error('Failed to fetch wx bind status:', err)
    }
  },

  async handleBindWechat() {
    if (this.data.wxBindLoading) return
    this.setData({ wxBindLoading: true })

    try {
      // Get WeChat login code first
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        })
      })

      if (!loginRes.code) {
        wx.showToast({ title: '获取微信信息失败', icon: 'none' })
        this.setData({ wxBindLoading: false })
        return
      }

      // Call backend to bind
      const res = await post('/base/wx_binduser', {
        openid: loginRes.code
      })

      wx.showToast({ title: '绑定成功', icon: 'success' })
      this.fetchWxBindStatus()
    } catch (err) {
      console.error('WeChat binding failed:', err)
    } finally {
      this.setData({ wxBindLoading: false })
    }
  },

  maskOpenid(openid) {
    if (!openid || openid.length < 8) return openid || ''
    return openid.substring(0, 4) + '****' + openid.substring(openid.length - 4)
  },

  // === Notification Settings ===
  loadNotificationSettings() {
    try {
      const settings = wx.getStorageSync('notification_settings')
      if (settings) {
        const parsed = JSON.parse(settings)
        this.setData({
          notifyNewTicket: parsed.notifyNewTicket !== false,
          notifyStatusChange: parsed.notifyStatusChange !== false,
          notifyMessage: parsed.notifyMessage !== false
        })
      }
    } catch (e) {
      console.error('Failed to load notification settings:', e)
    }
  },

  onNotifyToggle(e) {
    const field = e.currentTarget.dataset.field
    const newValue = !this.data[field]
    this.setData({ [field]: newValue })
    this.saveNotificationSettings()
  },

  saveNotificationSettings() {
    try {
      const settings = {
        notifyNewTicket: this.data.notifyNewTicket,
        notifyStatusChange: this.data.notifyStatusChange,
        notifyMessage: this.data.notifyMessage
      }
      wx.setStorageSync('notification_settings', JSON.stringify(settings))
    } catch (e) {
      console.error('Failed to save notification settings:', e)
    }
  },

  // === Existing methods ===
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
      const cityName = city || province
      await post('/base/update_profile', { city: cityName })
      // Update local storage
      const userInfo = getUserInfo() || {}
      userInfo.default_city_name = cityName
      setUserInfo(userInfo)
      wx.showToast({ title: '城市已更新', icon: 'success' })
    } catch (err) {
      console.error('Failed to update city:', err)
      wx.showToast({ title: '更新失败', icon: 'none' })
    }
  },

  navigateToAdmin() {
    wx.navigateTo({ url: '/pages/admin/admin' })
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
