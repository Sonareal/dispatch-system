const { get } = require('../../../utils/request')
const { getStatusInfo } = require('../../../utils/util')

Page({
  data: {
    tabs: [
      { key: '', label: '全部' },
      { key: 'draft', label: '草稿' },
      { key: 'pending_review', label: '待审核' },
      { key: 'assigned', label: '已指派' },
      { key: 'processing', label: '处理中' },
      { key: 'completed', label: '已完成' },
      { key: 'rejected', label: '已驳回' }
    ],
    activeTab: '',
    ticketList: [],
    page: 1,
    pageSize: 10,
    total: 0,
    hasMore: true,
    loading: false,
    refreshing: false,
    keyword: ''
  },

  onLoad(options) {
    if (options && options.status) {
      this.setData({ activeTab: options.status })
    }
    this.fetchList()
  },

  onShow() {
    // Refresh on show in case data changed
  },

  onPullDownRefresh() {
    this.setData({ refreshing: true })
    this.refreshList().finally(() => {
      wx.stopPullDownRefresh()
      this.setData({ refreshing: false })
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  onTabChange(e) {
    const key = e.currentTarget.dataset.key
    if (key === this.data.activeTab) return
    this.setData({ activeTab: key })
    this.refreshList()
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
  },

  onSearch() {
    this.refreshList()
  },

  onClearSearch() {
    this.setData({ keyword: '' })
    this.refreshList()
  },

  async refreshList() {
    this.setData({
      page: 1,
      ticketList: [],
      hasMore: true
    })
    await this.fetchList()
  },

  async loadMore() {
    const nextPage = this.data.page + 1
    this.setData({ page: nextPage })
    await this.fetchList(true)
  },

  async fetchList(append = false) {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const params = {
        page: this.data.page,
        page_size: this.data.pageSize
      }
      if (this.data.activeTab) {
        params.status = this.data.activeTab
      }
      if (this.data.keyword) {
        params.keyword = this.data.keyword
      }

      const res = await get('/ticket/list', params, { showLoading: false })
      const list = res.data || []
      const total = res.total || 0

      // Add status info to each ticket
      const processedList = list.map(item => {
        const statusInfo = getStatusInfo(item.status)
        return {
          ...item,
          statusText: statusInfo.text,
          statusTagClass: statusInfo.tagClass
        }
      })

      const newList = append
        ? [...this.data.ticketList, ...processedList]
        : processedList

      this.setData({
        ticketList: newList,
        total: total,
        hasMore: newList.length < total,
        loading: false
      })
    } catch (err) {
      console.error('Failed to fetch ticket list:', err)
      this.setData({ loading: false })
    }
  },

  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/ticket/detail/detail?id=' + id })
  },

  navigateToCreate() {
    wx.navigateTo({ url: '/pages/ticket/create/create' })
  }
})
