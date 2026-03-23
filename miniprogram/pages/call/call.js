const { getToken } = require('../../utils/auth')

const WS_BASE = 'wss://168heima.cn/api/v1/ws/signaling'
//const WS_BASE = 'ws://localhost:9999/api/v1/ws/signaling'
Page({
  data: {
    // Page params
    ticketId: '',
    calleeId: '',
    calleeName: '',
    callId: '',
    callerName: '',
    roomId: '',
    mode: 'caller', // 'caller' or 'callee'

    // UI state: 'calling' | 'incoming' | 'connected' | 'ended'
    state: 'calling',
    displayName: '',
    avatarChar: '',
    statusText: '呼叫中...',
    duration: 0,
    durationText: '00:00',
    endReason: ''
  },

  _ws: null,
  _timer: null,
  _startTime: 0,
  _closed: false,

  onLoad(options) {
    const {
      ticket_id = '',
      callee_id = '',
      callee_name = '',
      call_id = '',
      caller_name = '',
      room_id = '',
      mode = 'caller'
    } = options

    const isCaller = mode === 'caller'
    const decodedCalleeName = decodeURIComponent(callee_name || '')
    const decodedCallerName = decodeURIComponent(caller_name || '')
    const displayName = isCaller ? decodedCalleeName : decodedCallerName
    const avatarChar = displayName ? displayName.charAt(0) : '?'

    this.setData({
      ticketId: ticket_id,
      calleeId: callee_id,
      calleeName: decodedCalleeName,
      callId: call_id,
      callerName: decodedCallerName,
      roomId: room_id,
      mode: mode,
      displayName: displayName,
      avatarChar: avatarChar,
      state: isCaller ? 'calling' : 'incoming',
      statusText: isCaller ? '呼叫中...' : '来电...'
    })

    this._connectWebSocket()
  },

  // ---- WebSocket ----

  _connectWebSocket() {
    const token = getToken()
    if (!token) {
      wx.showToast({ title: '未登录', icon: 'none' })
      this._closePage()
      return
    }

    const url = `${WS_BASE}?token=${encodeURIComponent(token)}`

    const ws = wx.connectSocket({
      url: url,
      success: () => {
        console.log('[Call] WebSocket connecting...')
      },
      fail: (err) => {
        console.error('[Call] WebSocket connect failed:', err)
        this._handleCallFailed('网络连接失败')
      }
    })

    this._ws = ws

    ws.onOpen(() => {
      console.log('[Call] WebSocket opened')
      // If caller, initiate the call
      if (this.data.mode === 'caller') {
        this._sendMessage({
          type: 'call_initiate',
          ticket_id: parseInt(this.data.ticketId),
          callee_id: parseInt(this.data.calleeId)
        })
      }
    })

    ws.onMessage((res) => {
      try {
        const msg = JSON.parse(res.data)
        this._handleMessage(msg)
      } catch (e) {
        console.error('[Call] Failed to parse message:', e)
      }
    })

    ws.onError((err) => {
      console.error('[Call] WebSocket error:', err)
    })

    ws.onClose(() => {
      console.log('[Call] WebSocket closed')
      this._ws = null
    })
  },

  _sendMessage(data) {
    if (!this._ws) {
      console.warn('[Call] WebSocket not connected, cannot send:', data)
      return
    }
    try {
      this._ws.send({
        data: JSON.stringify(data),
        fail: (err) => {
          console.error('[Call] Send message failed:', err)
        }
      })
    } catch (e) {
      console.error('[Call] Send exception:', e)
    }
  },

  _handleMessage(msg) {
    console.log('[Call] Received message:', msg.type)

    switch (msg.type) {
      case 'call_created':
        // Server confirms call creation, save call_id
        this.setData({ callId: String(msg.call_id), roomId: msg.room_id || '' })
        break
      case 'call_accepted':
        this._onCallAccepted(msg)
        break
      case 'call_connected':
        // Callee side: server confirms connection
        this._startConnected()
        break
      case 'call_rejected':
        this._onCallRejected(msg)
        break
      case 'call_ended':
        this._onCallEnded(msg)
        break
      case 'call_failed':
        this._onCallFailed(msg)
        break
      case 'incoming_call':
        // This shouldn't happen on the call page itself (handled by index page polling)
        // But if it does, update call info
        this.setData({
          callId: String(msg.call_id),
          roomId: msg.room_id || '',
          callerName: msg.caller_name || '',
          displayName: msg.caller_name || '未知',
          avatarChar: (msg.caller_name || '?').charAt(0),
        })
        break
      case 'pong':
        break
      default:
        console.log('[Call] Unhandled message type:', msg.type)
    }
  },

  _onCallAccepted(msg) {
    if (msg.call_id) {
      this.setData({ callId: msg.call_id })
    }
    this._startConnected()
  },

  _onCallRejected(_msg) {
    this.setData({
      state: 'ended',
      statusText: '对方已拒绝'
    })
    this._autoClose(2000)
  },

  _onCallEnded(msg) {
    this._stopTimer()
    const duration = this.data.duration
    this.setData({
      state: 'ended',
      statusText: '通话结束',
      endReason: this._formatDuration(duration)
    })
    this._autoClose(2000)
  },

  _onCallFailed(msg) {
    const reason = msg.reason || '呼叫失败'
    this._handleCallFailed(reason)
  },

  _handleCallFailed(reason) {
    this._stopTimer()
    this.setData({
      state: 'ended',
      statusText: reason
    })
    this._autoClose(2000)
  },

  // ---- Connected state ----

  _startConnected() {
    this._startTime = Date.now()
    this.setData({
      state: 'connected',
      statusText: '通话中',
      duration: 0,
      durationText: '00:00'
    })
    this._startTimer()
  },

  _startTimer() {
    this._stopTimer()
    this._timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this._startTime) / 1000)
      this.setData({
        duration: elapsed,
        durationText: this._formatDuration(elapsed)
      })
    }, 1000)
  },

  _stopTimer() {
    if (this._timer) {
      clearInterval(this._timer)
      this._timer = null
    }
  },

  _formatDuration(seconds) {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  },

  // ---- User actions ----

  acceptCall() {
    this._sendMessage({
      type: 'call_answer',
      call_id: parseInt(this.data.callId)
    })
    this._startConnected()
  },

  rejectCall() {
    this._sendMessage({
      type: 'call_reject',
      call_id: parseInt(this.data.callId)
    })
    this._closePage()
  },

  hangupCall() {
    this._sendMessage({
      type: 'call_hangup',
      call_id: parseInt(this.data.callId)
    })

    if (this.data.state === 'connected') {
      const duration = this.data.duration
      this.setData({
        state: 'ended',
        statusText: '通话结束',
        endReason: this._formatDuration(duration)
      })
      this._stopTimer()
      this._autoClose(2000)
    } else {
      this._closePage()
    }
  },

  // ---- Helpers ----

  _autoClose(delay) {
    setTimeout(() => {
      this._closePage()
    }, delay)
  },

  _closePage() {
    if (this._closed) return
    this._closed = true
    this._cleanup()
    wx.navigateBack({ fail: () => {} })
  },

  _cleanup() {
    this._stopTimer()
    if (this._ws) {
      try {
        this._ws.close()
      } catch (e) {
        // ignore
      }
      this._ws = null
    }
  },

  onUnload() {
    // If still connected when leaving, send hangup
    if (this.data.state === 'connected' || this.data.state === 'calling') {
      this._sendMessage({
        type: 'call_hangup',
        call_id: this.data.callId
      })
    }
    this._cleanup()
  }
})
