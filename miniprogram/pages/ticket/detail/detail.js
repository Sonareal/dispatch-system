const { get, post } = require('../../../utils/request')
const { getStatusInfo, formatTime, formatAmount, maskPhone, maskIdCard } = require('../../../utils/util')

Page({
  data: {
    id: null,
    ticket: null,
    flowRecords: [],
    auditRecords: [],
    messages: [],
    loading: true,
    statusInfo: {},
    showRemarkModal: false,
    actionType: '',
    actionRemark: '',
    assignableUsers: [],
    selectedUserId: null,
    msgContent: '',
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ id: options.id })
      this.fetchDetail()
    }
  },

  onPullDownRefresh() {
    this.fetchDetail().finally(() => wx.stopPullDownRefresh())
  },

  async fetchDetail() {
    this.setData({ loading: true })
    try {
      const res = await get('/ticket/get', { ticket_id: this.data.id }, { showLoading: false })
      const ticket = res.data || {}
      const statusInfo = getStatusInfo(ticket.status)

      this.setData({
        ticket: {
          ...ticket,
          apply_amount_fmt: formatAmount(ticket.apply_amount),
          inspection_fee_fmt: formatAmount(ticket.inspection_fee),
          phone_masked: maskPhone(ticket.customer_phone),
          id_card_masked: maskIdCard(ticket.id_card),
          created_at_fmt: formatTime(ticket.created_at),
          updated_at_fmt: formatTime(ticket.updated_at)
        },
        flowRecords: (ticket.flow_records || []).map(item => ({
          ...item, created_at_fmt: formatTime(item.created_at)
        })),
        auditRecords: (ticket.audit_records || []).map(item => ({
          ...item, created_at_fmt: formatTime(item.created_at)
        })),
        statusInfo,
        loading: false
      })

      this.fetchMessages()
    } catch (err) {
      console.error('Failed to fetch ticket detail:', err)
      this.setData({ loading: false })
    }
  },

  async fetchMessages() {
    try {
      const res = await get('/message/ticket_messages', { ticket_id: this.data.id }, { showLoading: false })
      this.setData({ messages: res.data || [] })
    } catch (e) {
      console.error('Failed to fetch messages:', e)
    }
  },

  onMsgInput(e) { this.setData({ msgContent: e.detail.value }) },

  async sendMessage() {
    const content = this.data.msgContent.trim()
    if (!content) return
    try {
      const ticket = this.data.ticket
      await post('/message/send', {
        ticket_id: parseInt(this.data.id),
        receiver_id: ticket.assignee_id || ticket.submitter_id,
        msg_type: 'text',
        content: content,
      })
      this.setData({ msgContent: '' })
      wx.showToast({ title: '发送成功', icon: 'success' })
      this.fetchMessages()
    } catch (e) {
      console.error('Send message failed:', e)
    }
  },

  // ===== Actions =====

  async loadAssignableUsers() {
    try {
      const res = await get('/ticket/assignable_users', { ticket_id: this.data.id }, { showLoading: false })
      const users = (res.data || []).map(u => ({
        ...u,
        role_text: (u.roles || []).join('/'),
        region_text: (u.regions || []).join('/'),
      }))
      const recommended = users.find(u => u.recommended)
      this.setData({
        assignableUsers: users,
        selectedUserId: recommended ? recommended.id : null,
      })
    } catch (e) {
      console.error('Failed to load assignable users:', e)
      this.setData({ assignableUsers: [], selectedUserId: null })
    }
  },

  selectAssignUser(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ selectedUserId: id })
  },

  async handleAuditApprove() {
    this.setData({ actionType: 'approve', showRemarkModal: true, actionRemark: '' })
    await this.loadAssignableUsers()
  },

  handleAuditReject() {
    this.setData({ actionType: 'reject', showRemarkModal: true, actionRemark: '', assignableUsers: [], selectedUserId: null })
  },

  async handleAssign() {
    this.setData({ actionType: 'assign', showRemarkModal: true, actionRemark: '' })
    await this.loadAssignableUsers()
  },

  async handleTransfer() {
    this.setData({ actionType: 'transfer', showRemarkModal: true, actionRemark: '' })
    await this.loadAssignableUsers()
  },

  handleUpdateStatus(e) {
    const status = e.currentTarget.dataset.status
    this.setData({ actionType: 'status_' + status, showRemarkModal: true, actionRemark: '', assignableUsers: [], selectedUserId: null })
  },

  onRemarkInput(e) { this.setData({ actionRemark: e.detail.value }) },

  closeRemarkModal() {
    this.setData({ showRemarkModal: false, actionType: '', actionRemark: '', assignableUsers: [], selectedUserId: null })
  },

  async confirmAction() {
    const { actionType, actionRemark, selectedUserId, id } = this.data
    try {
      if (actionType === 'approve') {
        if (!selectedUserId) { wx.showToast({ title: '请选择指派人员', icon: 'none' }); return }
        await post('/ticket/audit', {
          ticket_id: parseInt(id), result: 'approved',
          assign_to_id: selectedUserId, remark: actionRemark
        })
        wx.showToast({ title: '审核通过', icon: 'success' })
      } else if (actionType === 'reject') {
        if (!actionRemark.trim()) { wx.showToast({ title: '请输入驳回原因', icon: 'none' }); return }
        await post('/ticket/audit', { ticket_id: parseInt(id), result: 'rejected', reject_reason: actionRemark })
        wx.showToast({ title: '已驳回', icon: 'success' })
      } else if (actionType === 'assign') {
        if (!selectedUserId) { wx.showToast({ title: '请选择处理人', icon: 'none' }); return }
        await post('/ticket/assign', { ticket_id: parseInt(id), assignee_id: selectedUserId, remark: actionRemark })
        wx.showToast({ title: '指派成功', icon: 'success' })
      } else if (actionType === 'transfer') {
        if (!selectedUserId) { wx.showToast({ title: '请选择转派人', icon: 'none' }); return }
        await post('/ticket/transfer', { ticket_id: parseInt(id), transfer_to_id: selectedUserId, reason: actionRemark })
        wx.showToast({ title: '转派成功', icon: 'success' })
      } else if (actionType.startsWith('status_')) {
        const newStatus = actionType.replace('status_', '')
        await post('/ticket/update_status', { ticket_id: parseInt(id), status: newStatus, remark: actionRemark })
        wx.showToast({ title: '状态更新成功', icon: 'success' })
      }
      this.closeRemarkModal()
      setTimeout(() => this.fetchDetail(), 500)
    } catch (err) {
      console.error('Action failed:', err)
    }
  },

  makePhoneCall() {
    const phone = this.data.ticket && this.data.ticket.customer_phone
    if (phone) wx.makePhoneCall({ phoneNumber: phone })
  },

  copyTicketNo() {
    const no = this.data.ticket && this.data.ticket.ticket_no
    if (no) wx.setClipboardData({ data: String(no) })
  }
})
