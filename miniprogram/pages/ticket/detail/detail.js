const { get, post, BASE_URL } = require('../../../utils/request')
const { getToken } = require('../../../utils/auth')
const { getStatusInfo, formatTime, formatAmount, maskPhone, maskIdCard } = require('../../../utils/util')

// Derive server origin from BASE_URL (strip /api/v1)
const SERVER_BASE = BASE_URL.replace(/\/api\/v1\/?$/, '')

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
    currentUserId: null,
    inputMode: 'text', // 'text' or 'voice'
    // Voice recording state
    isRecording: false,
    recordingDuration: 0,
    // Voice playback state
    playingMsgId: null,
    playingCurrentTime: 0,
    playingTimeText: '0:00',
    playingProgress: 0,
    playingDuration: 0,
    playingTotalText: '',
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ id: options.id })
      this.fetchDetail()
    }
    this._initRecorder()
    this._initAudioPlayer()
    // Get current user ID for call button logic
    this._loadCurrentUserId()
  },

  async _loadCurrentUserId() {
    try {
      const res = await get('/base/userinfo', {}, { showLoading: false })
      if (res.data && res.data.id) {
        this.setData({ currentUserId: res.data.id })
      }
    } catch (e) {}
  },

  onUnload() {
    // Cleanup on page unload - only stop if actually recording
    if (this._recorderManager && this.data.isRecording) {
      try { this._recorderManager.stop() } catch (e) { /* ignore */ }
    }
    if (this._audioContext) {
      try { this._audioContext.stop() } catch (e) { /* ignore */ }
      try { this._audioContext.destroy() } catch (e) { /* ignore */ }
    }
    if (this._recordingTimer) {
      clearInterval(this._recordingTimer)
    }
  },

  onPullDownRefresh() {
    this.fetchDetail().finally(() => wx.stopPullDownRefresh())
  },

  // ===== Voice Recorder Init =====

  _initRecorder() {
    const recorderManager = wx.getRecorderManager()

    recorderManager.onStart(() => {
      console.log('Recording started')
      this._recordingLock = false
      this.setData({ isRecording: true, recordingDuration: 0 })
      this._recordingStartTime = Date.now()
      this._recordingTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - this._recordingStartTime) / 1000)
        this.setData({ recordingDuration: elapsed })
      }, 1000)
    })

    recorderManager.onStop((res) => {
      console.log('Recording stopped', res)
      this.setData({ isRecording: false, recordingDuration: 0 })
      if (this._recordingTimer) {
        clearInterval(this._recordingTimer)
        this._recordingTimer = null
      }
      // Only upload if we have a valid recording (at least 1 second)
      const duration = res.duration // in ms
      if (duration && duration < 1000) {
        wx.showToast({ title: '录音时间太短', icon: 'none' })
        return
      }
      this._uploadVoice(res.tempFilePath, Math.round((duration || 0) / 1000))
    })

    recorderManager.onError((err) => {
      // Ignore harmless "not start" error (triggered by stop() when not recording)
      if (err && err.errMsg && err.errMsg.indexOf('not start') !== -1) {
        console.log('Recorder: ignored not-start error')
        return
      }
      console.error('Recorder error:', err)
      this._recordingLock = false
      this.setData({ isRecording: false, recordingDuration: 0 })
      if (this._recordingTimer) {
        clearInterval(this._recordingTimer)
        this._recordingTimer = null
      }
      wx.showToast({ title: '录音失败', icon: 'none' })
    })

    this._recorderManager = recorderManager
  },

  _initAudioPlayer() {
    const audioContext = wx.createInnerAudioContext()

    audioContext.onEnded(() => {
      this.setData({ playingMsgId: null, playingCurrentTime: 0, playingProgress: 0, playingTimeText: '0:00', playingTotalText: '', playingDuration: 0 })
    })

    audioContext.onError((err) => {
      if (err && err.errMsg && err.errMsg.indexOf('audioInstance') !== -1) return
      console.error('Audio playback error:', err)
      this.setData({ playingMsgId: null, playingCurrentTime: 0, playingProgress: 0, playingTimeText: '0:00', playingTotalText: '', playingDuration: 0 })
      wx.showToast({ title: '播放失败', icon: 'none' })
    })

    audioContext.onTimeUpdate(() => {
      const cur = audioContext.currentTime || 0
      // Use audio's own duration (most accurate), fallback to stored duration
      const audioDur = audioContext.duration
      const dur = (audioDur && audioDur > 0 && isFinite(audioDur)) ? audioDur : (this.data.playingDuration || 0)
      const sec = Math.floor(cur)
      const m = Math.floor(sec / 60)
      const s = sec % 60
      const progress = dur > 0 ? Math.min(100, Math.round(cur / dur * 100)) : 0

      // Also update total duration text if we now know it
      const updates = {
        playingCurrentTime: sec,
        playingTimeText: m + ':' + (s < 10 ? '0' : '') + s,
        playingProgress: progress,
      }
      if (dur > 0) {
        const totalSec = Math.floor(dur)
        if (!this.data.playingDuration || this.data.playingDuration !== totalSec) {
          updates.playingDuration = totalSec
          updates.playingTotalText = this._formatDurationText(totalSec)
        }
      }
      this.setData(updates)
    })

    audioContext.onStop(() => {
      this.setData({ playingMsgId: null, playingCurrentTime: 0, playingProgress: 0, playingTimeText: '0:00', playingTotalText: '', playingDuration: 0 })
    })

    this._audioContext = audioContext
  },

  // ===== Input Mode =====

  toggleInputMode() {
    const newMode = this.data.inputMode === 'text' ? 'voice' : 'text'
    if (newMode === 'voice') {
      // 切换到语音模式时预先请求权限
      wx.authorize({
        scope: 'scope.record',
        success: () => {
          this.setData({ inputMode: 'voice' })
        },
        fail: () => {
          wx.showModal({
            title: '需要录音权限',
            content: '使用语音功能需要允许录音权限',
            confirmText: '去设置',
            cancelText: '取消',
            success: (res) => {
              if (res.confirm) {
                wx.openSetting({
                  success: (settingRes) => {
                    if (settingRes.authSetting['scope.record']) {
                      this.setData({ inputMode: 'voice' })
                    }
                  }
                })
              }
            }
          })
        }
      })
    } else {
      this.setData({ inputMode: 'text' })
    }
  },

  // ===== Voice Recording =====

  onVoiceBtnTouchStart() {
    if (this.data.isRecording || this._recordingLock) return
    this._recordingLock = true
    this._startRecording()
  },

  _startRecording() {
    try {
      this._recorderManager.start({
        duration: 60000,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        format: 'mp3',
      })
    } catch (e) {
      console.error('Start recording failed:', e)
      this._recordingLock = false
      this.setData({ isRecording: false })
    }
  },

  onVoiceBtnTouchEnd() {
    this._recordingLock = false
    if (this.data.isRecording) {
      this._recorderManager.stop()
    }
  },

  _uploadVoice(filePath, duration) {
    const ticket = this.data.ticket
    if (!ticket) return

    wx.showLoading({ title: '发送语音中...', mask: true })
    const token = getToken()
    const uploadUrl = SERVER_BASE + '/api/v1/message/upload_voice'

    wx.uploadFile({
      url: uploadUrl,
      filePath: filePath,
      name: 'file',
      formData: {
        ticket_id: String(this.data.id),
        receiver_id: String(ticket.assignee_id || ticket.submitter_id),
        voice_duration: String(duration || 0),
      },
      header: {
        'token': token,
      },
      success: (res) => {
        wx.hideLoading()
        if (res.statusCode === 200) {
          let data = res.data
          if (typeof data === 'string') {
            try { data = JSON.parse(data) } catch (e) { /* ignore */ }
          }
          if (data && (data.code === 0 || data.code === 200)) {
            wx.showToast({ title: '发送成功', icon: 'success' })
            this.fetchMessages()
          } else {
            wx.showToast({ title: (data && data.msg) || '发送失败', icon: 'none' })
          }
        } else {
          wx.showToast({ title: '上传失败', icon: 'none' })
        }
      },
      fail: (err) => {
        wx.hideLoading()
        console.error('Upload voice failed:', err)
        wx.showToast({ title: '上传失败', icon: 'none' })
      }
    })
  },

  // ===== Voice Playback =====

  onPlayVoice(e) {
    const msgId = e.currentTarget.dataset.id
    const fileUrl = e.currentTarget.dataset.url

    // If tapping the currently playing message, stop it
    if (this.data.playingMsgId === msgId) {
      try { this._audioContext.stop() } catch (err) { /* ignore */ }
      this.setData({ playingMsgId: null, playingCurrentTime: 0, playingProgress: 0, playingTimeText: '0:00' })
      return
    }

    // Destroy old context and create fresh one to avoid "audioInstance is not set"
    if (this._audioContext) {
      try { this._audioContext.stop() } catch (err) { /* ignore */ }
      try { this._audioContext.destroy() } catch (err) { /* ignore */ }
    }
    this._initAudioPlayer()

    // Build full URL from file_url
    let fullUrl = fileUrl
    if (fileUrl && fileUrl.startsWith('/')) {
      fullUrl = SERVER_BASE + fileUrl
    }

    // Find duration from messages
    const msg = this.data.messages.find(m => m.id === msgId)
    const dur = (msg && msg.voice_duration) || 0

    this.setData({
      playingMsgId: msgId, playingCurrentTime: 0, playingProgress: 0,
      playingTimeText: '0:00', playingDuration: dur,
      playingTotalText: dur > 0 ? this._formatDurationText(dur) : '',
    })
    this._audioContext.src = fullUrl
    this._audioContext.play()
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

  _formatDurationText(sec) {
    if (!sec || sec <= 0) return ''
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return m + ':' + (s < 10 ? '0' : '') + s
  },

  async fetchMessages() {
    try {
      const res = await get('/message/ticket_messages', { ticket_id: this.data.id }, { showLoading: false })
      const messages = (res.data || []).map(msg => ({
        ...msg,
        durationText: msg.voice_duration ? this._formatDurationText(msg.voice_duration) : '',
        fullImageUrl: msg.msg_type === 'image' && msg.file_url
          ? (msg.file_url.startsWith('http') ? msg.file_url : SERVER_BASE + msg.file_url)
          : '',
      }))
      this.setData({ messages })
    } catch (e) {
      console.error('Failed to fetch messages:', e)
    }
  },

  onChooseImage() {
    const ticket = this.data.ticket
    if (!ticket) return
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFile = res.tempFiles[0]
        if (tempFile) {
          this._uploadImage(tempFile.tempFilePath)
        }
      }
    })
  },

  _uploadImage(filePath) {
    const ticket = this.data.ticket
    if (!ticket) return
    wx.showLoading({ title: '发送图片中...', mask: true })
    const token = getToken()
    const uploadUrl = SERVER_BASE + '/api/v1/message/upload_image'

    wx.uploadFile({
      url: uploadUrl,
      filePath: filePath,
      name: 'file',
      formData: {
        ticket_id: String(this.data.id),
        receiver_id: String(ticket.assignee_id || ticket.submitter_id),
      },
      header: { 'token': token },
      success: (res) => {
        wx.hideLoading()
        if (res.statusCode === 200) {
          let data = res.data
          if (typeof data === 'string') {
            try { data = JSON.parse(data) } catch (e) { /* ignore */ }
          }
          if (data && (data.code === 0 || data.code === 200)) {
            wx.showToast({ title: '发送成功', icon: 'success' })
            this.fetchMessages()
          } else {
            wx.showToast({ title: (data && data.msg) || '发送失败', icon: 'none' })
          }
        } else {
          wx.showToast({ title: '上传失败', icon: 'none' })
        }
      },
      fail: () => {
        wx.hideLoading()
        wx.showToast({ title: '上传失败', icon: 'none' })
      }
    })
  },

  onPreviewImage(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      wx.previewImage({ current: url, urls: [url] })
    }
  },

  onDeleteMessage(e) {
    const msgId = parseInt(e.currentTarget.dataset.id)
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条消息吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await post('/message/delete', { message_id: msgId })
            wx.showToast({ title: '已删除', icon: 'success' })
            this.fetchMessages()
          } catch (err) {
            console.error('Delete failed:', err)
          }
        }
      }
    })
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

  handleEditTicket() {
    const ticket = this.data.ticket
    if (!ticket) return
    wx.navigateTo({
      url: `/pages/ticket/create/create?edit_id=${ticket.id}`
    })
  },

  async handleSubmitTicket() {
    try {
      await post('/ticket/submit', { ticket_id: parseInt(this.data.id) })
      wx.showToast({ title: '已提交审核', icon: 'success' })
      setTimeout(() => this.fetchDetail(), 500)
    } catch (e) {
      console.error('Submit failed:', e)
    }
  },

  async handleWithdraw() {
    try {
      await post('/ticket/withdraw', { ticket_id: parseInt(this.data.id) })
      wx.showToast({ title: '已撤回', icon: 'success' })
      setTimeout(() => this.fetchDetail(), 500)
    } catch (e) {
      console.error('Withdraw failed:', e)
    }
  },

  async handleRevertToReview() {
    wx.showModal({
      title: '确认打回',
      content: '确定要将此工单打回重新审核吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await post('/ticket/revert_to_review', { ticket_id: parseInt(this.data.id) })
            wx.showToast({ title: '已打回重审', icon: 'success' })
            setTimeout(() => this.fetchDetail(), 500)
          } catch (e) {
            console.error('Revert failed:', e)
          }
        }
      }
    })
  },

  initiateCall() {
    const ticket = this.data.ticket
    const currentUserId = this.data.currentUserId
    if (!ticket || !currentUserId) return

    // Determine who to call: if I'm the submitter, call assignee; if I'm assignee, call submitter
    let calleeId, calleeName
    if (currentUserId === ticket.submitter_id) {
      calleeId = ticket.assignee_id
      calleeName = ticket.assignee_name || '处理人'
    } else {
      calleeId = ticket.submitter_id
      calleeName = ticket.submitter_name || '提交人'
    }

    if (!calleeId) {
      wx.showToast({ title: '暂无通话对象', icon: 'none' })
      return
    }

    wx.navigateTo({
      url: `/pages/call/call?ticket_id=${ticket.id}&callee_id=${calleeId}&callee_name=${encodeURIComponent(calleeName)}&mode=caller`
    })
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
