const { get } = require('../../utils/request')
const { isLoggedIn, getUserInfo } = require('../../utils/auth')

Page({
  data: {
    userInfo: null,
    stats: {
      draft: 0,
      pending_review: 0,
      processing: 0,
      completed: 0,
      rejected: 0,
      assigned: 0,
      total: 0
    },
    recentTickets: [],
    unreadCount: 0,
    loading: true
  },

  _pollTimer: null,

  onLoad() {
    if (!isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    const userInfo = getUserInfo()
    this.setData({ userInfo })
  },

  onShow() {
    if (isLoggedIn()) {
      this.fetchDashboard()
      this.fetchUnread()
      this.startPolling()
    }
  },

  onHide() {
    this.stopPolling()
  },

  onUnload() {
    this.stopPolling()
  },

  startPolling() {
    this.stopPolling()
    this._pollTimer = setInterval(() => {
      this.fetchUnread()
    }, 15000)
  },

  stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer)
      this._pollTimer = null
    }
  },

  async fetchUnread() {
    try {
      const res = await get('/message/unread_count', {}, { showLoading: false })
      const count = (res.data && res.data.count) || 0
      const prevCount = this.data.unreadCount
      this.setData({ unreadCount: count })

      if (count > prevCount && prevCount >= 0) {
        wx.showTabBarRedDot({ index: 0 })
        if (count > 0) {
          wx.vibrateLong()
        }
      }
      if (count === 0) {
        wx.hideTabBarRedDot({ index: 0 })
      }
    } catch (e) {
      // ignore
    }
  },

  onPullDownRefresh() {
    this.fetchDashboard().then(() => {
      wx.stopPullDownRefresh()
    }).catch(() => {
      wx.stopPullDownRefresh()
    })
  },

  async fetchDashboard() {
    this.setData({ loading: true })
    try {
      const [statsRes, recentRes] = await Promise.all([
        get('/ticket/statistics', {}, { showLoading: false }),
        get('/ticket/list', { page: 1, page_size: 5, my_tickets: true }, { showLoading: false })
      ])

      const stats = statsRes.data || {}
      const recentTickets = recentRes.data || []

      this.setData({
        stats: {
          draft: stats.draft || 0,
          pending_review: stats.pending_review || 0,
          processing: stats.processing || 0,
          completed: stats.completed || 0,
          rejected: stats.rejected || 0,
          assigned: stats.assigned || 0,
          total: stats.total || 0
        },
        recentTickets,
        loading: false
      })
    } catch (err) {
      console.error('Failed to fetch dashboard:', err)
      this.setData({ loading: false })
    }
  },

  navigateToCreate() {
    wx.navigateTo({ url: '/pages/ticket/create/create' })
  },

  navigateToList(e) {
    wx.switchTab({ url: '/pages/ticket/list/list' })
  },

  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/ticket/detail/detail?id=' + id })
  },

  navigateToTickets() {
    wx.switchTab({ url: '/pages/ticket/list/list' })
  },

  navigateToNotifications() {
    wx.navigateTo({ url: '/pages/mine/mine' })
  }
})
