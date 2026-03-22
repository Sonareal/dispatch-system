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
    isEdit: false
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
