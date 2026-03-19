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
    submitting: false
  },

  onLoad() {
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
      const res = await post('/ticket/create', formData)

      wx.showToast({ title: '工单创建成功', icon: 'success' })

      setTimeout(() => {
        const ticketId = res.data && res.data.id
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
