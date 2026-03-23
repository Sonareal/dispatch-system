const { post, get } = require('../../../utils/request')
const { isValidPhone, isValidIdCard } = require('../../../utils/util')

Page({
  data: {
    form: {
      customer_name: '',
      customer_phone: '',
      id_card: '',
      apply_amount: '',
      repayment_method: '',
      address: '',
      province: '',
      city: '',
      district: '',
      salesman: '',
      inspection_fee: '',
      remark: ''
    },
    repaymentMethods: ['等额本息', '等额本金', '先息后本', '一次性还本付息'],
    repaymentIndex: -1,
    cityText: '',
    submitting: false,
    editId: null,
    isEdit: false,
    ocrPreview: null,
  },

  onLoad(options) {
    if (options.edit_id) {
      this.setData({ editId: options.edit_id, isEdit: true })
      wx.setNavigationBarTitle({ title: '编辑工单' })
      this.loadTicketData(options.edit_id)
    } else {
      // Default salesman to current user
      const { getUserInfo } = require('../../../utils/auth')
      const userInfo = getUserInfo()
      if (userInfo) {
        this.setData({
          'form.salesman': userInfo.alias && userInfo.alias !== userInfo.username
            ? `${userInfo.alias}(${userInfo.username})`
            : (userInfo.alias || userInfo.name || userInfo.username || '')
        })
      }
    }
  },

  async loadTicketData(ticketId) {
    try {
      const res = await get('/ticket/get', { ticket_id: ticketId }, { showLoading: true })
      const t = res.data || {}
      const repaymentIndex = this.data.repaymentMethods.indexOf(t.repayment_method)
      this.setData({
        form: {
          customer_name: t.customer_name || '',
          customer_phone: t.customer_phone || '',
          id_card: t.id_card || '',
          apply_amount: t.apply_amount ? String(t.apply_amount) : '',
          repayment_method: t.repayment_method || '',
          address: t.address || '',
          province: '',
          city: '',
          district: '',
          salesman: t.salesman || '',
          inspection_fee: t.inspection_fee ? String(t.inspection_fee) : '',
          remark: t.remark || '',
        },
        repaymentIndex: repaymentIndex >= 0 ? repaymentIndex : -1,
        cityText: t.region_path || t.city_name || '',
      })
    } catch (e) {
      console.error('Failed to load ticket:', e)
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // ===== OCR 身份证识别 =====
  onScanIdCard() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath
        wx.showLoading({ title: '识别中...', mask: true })
        // Use WeChat OCR plugin or manual parsing
        this._ocrIdCard(tempFilePath)
      }
    })
  },

  _ocrIdCard(imagePath) {
    // Try WeChat's built-in OCR API (requires plugin or service)
    // Fallback: use wx.getImageInfo + upload to server for OCR
    // For now, use the simple approach: wx chooseImage -> let user confirm

    // Method: Use the image to extract text via backend OCR service
    const { getToken } = require('../../../utils/auth')
    const { BASE_URL } = require('../../../utils/request')
    const SERVER_BASE = BASE_URL.replace(/\/api\/v1\/?$/, '')
    const token = getToken()

    wx.uploadFile({
      url: SERVER_BASE + '/api/v1/ocr/id_card',
      filePath: imagePath,
      name: 'file',
      header: { 'token': token },
      success: (res) => {
        wx.hideLoading()
        if (res.statusCode === 200) {
          let data = res.data
          if (typeof data === 'string') {
            try { data = JSON.parse(data) } catch (e) { /* */ }
          }
          if (data && (data.code === 0 || data.code === 200) && data.data) {
            const result = data.data
            // Auto-fill form fields
            const updates = {}
            if (result.name) {
              updates['form.customer_name'] = result.name
            }
            if (result.id_number) {
              updates['form.id_card'] = result.id_number
            }
            // Note: 身份证上的地址通常与实际地址不符，不自动填入地址字段
            updates.ocrPreview = {
              name: result.name || '',
              id: result.id_number || '',
            }
            this.setData(updates)
            wx.showToast({ title: '识别成功', icon: 'success' })
          } else {
            wx.showToast({ title: (data && data.msg) || '识别失败，请手动输入', icon: 'none' })
          }
        } else if (res.statusCode === 404) {
          wx.hideLoading()
          // OCR API not available, use manual fallback
          this._ocrFallback(imagePath)
        } else {
          wx.showToast({ title: '识别失败', icon: 'none' })
        }
      },
      fail: () => {
        wx.hideLoading()
        this._ocrFallback(imagePath)
      }
    })
  },

  _ocrFallback(imagePath) {
    // Fallback: show the image and let user manually input
    wx.showModal({
      title: '提示',
      content: 'OCR服务暂不可用，请查看照片后手动输入身份证信息',
      confirmText: '查看照片',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          wx.previewImage({ urls: [imagePath] })
        }
      }
    })
  },

  onClearOcr() {
    this.setData({ ocrPreview: null })
  },

  // ===== 位置获取 =====
  onGetLocation() {
    // First try chooseLocation (shows map picker)
    wx.chooseLocation({
      success: (res) => {
        if (res.address || res.name) {
          const fullAddress = (res.address || '') + (res.name || '')
          this.setData({ 'form.address': fullAddress })
          wx.showToast({ title: '位置获取成功', icon: 'success' })
        }
      },
      fail: (err) => {
        console.log('chooseLocation failed:', err)
        // Fallback: try getLocation for coordinates then reverse geocode
        this._getLocationFallback()
      }
    })
  },

  _getLocationFallback() {
    wx.authorize({
      scope: 'scope.userLocation',
      success: () => {
        wx.getLocation({
          type: 'gcj02',
          success: (res) => {
            // Got coordinates, set as address
            const addr = '经度:' + res.longitude.toFixed(6) + ' 纬度:' + res.latitude.toFixed(6)
            this.setData({ 'form.address': addr })
            wx.showToast({ title: '已获取坐标', icon: 'success' })
          },
          fail: () => {
            wx.showToast({ title: '无法获取位置，请手动输入', icon: 'none' })
          }
        })
      },
      fail: () => {
        wx.showModal({
          title: '需要位置权限',
          content: '获取位置需要允许位置权限',
          confirmText: '去设置',
          cancelText: '取消',
          success: (res) => {
            if (res.confirm) {
              wx.openSetting()
            }
          }
        })
      }
    })
  },

  onInputChange(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({
      [`form.${field}`]: value
    })
  },

  onRepaymentChange(e) {
    const index = e.detail.value
    this.setData({
      repaymentIndex: index,
      'form.repayment_method': this.data.repaymentMethods[index]
    })
  },

  onCityChange(e) {
    const value = e.detail.value
    // value is [provinceIndex, cityIndex, districtIndex]
    // For region picker, e.detail.value is the selected text array
    const province = value[0] || ''
    const city = value[1] || ''
    const district = value[2] || ''

    this.setData({
      'form.province': province,
      'form.city': city,
      'form.district': district,
      cityText: [province, city, district].filter(Boolean).join(' ')
    })
  },

  validateForm() {
    const { form } = this.data

    if (!form.customer_name.trim()) {
      wx.showToast({ title: '请输入客户姓名', icon: 'none' })
      return false
    }

    if (!form.customer_phone.trim()) {
      wx.showToast({ title: '请输入联系电话', icon: 'none' })
      return false
    }

    if (!isValidPhone(form.customer_phone.trim())) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return false
    }

    if (form.id_card && !isValidIdCard(form.id_card.trim())) {
      wx.showToast({ title: '请输入正确的身份证号', icon: 'none' })
      return false
    }

    if (!form.apply_amount || parseFloat(form.apply_amount) <= 0) {
      wx.showToast({ title: '请输入有效的申请金额', icon: 'none' })
      return false
    }

    if (!form.repayment_method) {
      wx.showToast({ title: '请选择还款方式', icon: 'none' })
      return false
    }

    return true
  },

  async handleSubmit() {
    if (this.data.submitting) return
    if (!this.validateForm()) return

    this.setData({ submitting: true })

    try {
      const formData = { ...this.data.form }
      formData.customer_name = formData.customer_name.trim()
      formData.customer_phone = formData.customer_phone.trim()
      formData.id_card = formData.id_card.trim()
      formData.apply_amount = parseFloat(formData.apply_amount)
      formData.inspection_fee = formData.inspection_fee ? parseFloat(formData.inspection_fee) : 0
      formData.address = formData.address.trim()
      formData.salesman = formData.salesman.trim()
      formData.remark = formData.remark.trim()

      formData.city_id = 1  // Default city, should be from user selection

      let res
      if (this.data.isEdit && this.data.editId) {
        formData.id = parseInt(this.data.editId)
        res = await post('/ticket/update', formData)
        wx.showToast({ title: '工单已更新', icon: 'success' })
      } else {
        res = await post('/ticket/create', formData)
        wx.showToast({ title: '工单创建成功', icon: 'success' })
      }

      setTimeout(() => {
        const ticketId = (res.data && res.data.id) || this.data.editId
        if (ticketId) {
          wx.redirectTo({ url: '/pages/ticket/detail/detail?id=' + ticketId })
        } else {
          wx.navigateBack()
        }
      }, 1500)
    } catch (err) {
      console.error('Failed to create ticket:', err)
    } finally {
      this.setData({ submitting: false })
    }
  },

  handleReset() {
    wx.showModal({
      title: '提示',
      content: '确定要重置表单吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            form: {
              customer_name: '',
              customer_phone: '',
              id_card: '',
              apply_amount: '',
              repayment_method: '',
              address: '',
              province: '',
              city: '',
              district: '',
              salesman: '',
              inspection_fee: '',
              remark: ''
            },
            repaymentIndex: -1,
            cityText: ''
          })
        }
      }
    })
  }
})
