const { getToken, clearAuth } = require('./auth')

// 生产环境（备案完成后切回域名）
// const BASE_URL = 'https://168heima.cn/api/v1'
// 临时用 IP 访问（开发者工具需勾选"不校验合法域名"）
const BASE_URL = 'http://124.223.62.202:9999/api/v1'

function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    showLoading = true,
    loadingText = '加载中...'
  } = options

  if (showLoading) {
    wx.showLoading({ title: loadingText, mask: true })
  }

  const token = getToken()
  const requestHeader = {
    'Content-Type': 'application/json',
    ...header
  }

  if (token) {
    requestHeader['token'] = token
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method: method,
      data: data,
      header: requestHeader,
      success(res) {
        if (showLoading) {
          wx.hideLoading()
        }

        const statusCode = res.statusCode

        if (statusCode === 200) {
          const responseData = res.data
          if (responseData.code === 0 || responseData.code === 200) {
            resolve(responseData)
          } else {
            const errMsg = responseData.msg || responseData.message || '请求失败'
            wx.showToast({ title: errMsg, icon: 'none', duration: 2000 })
            reject(new Error(errMsg))
          }
        } else if (statusCode === 401) {
          clearAuth()
          wx.showToast({ title: '登录已过期，请重新登录', icon: 'none', duration: 2000 })
          setTimeout(() => {
            wx.redirectTo({ url: '/pages/login/login' })
          }, 1500)
          reject(new Error('Unauthorized'))
        } else if (statusCode === 403) {
          const detail = (res.data && res.data.msg) || url
          wx.showToast({ title: '无权限: ' + detail, icon: 'none', duration: 3000 })
          reject(new Error('Forbidden: ' + detail))
        } else if (statusCode === 404) {
          const detail = (res.data && res.data.msg) || url
          wx.showToast({ title: '未找到: ' + detail, icon: 'none', duration: 3000 })
          reject(new Error('Not Found: ' + detail))
        } else if (statusCode === 422) {
          const detail = (res.data && res.data.msg) || '参数错误'
          wx.showToast({ title: detail, icon: 'none', duration: 3000 })
          reject(new Error('Validation: ' + detail))
        } else if (statusCode >= 500) {
          const detail = (res.data && res.data.msg) || url
          wx.showToast({ title: '服务器错误: ' + detail, icon: 'none', duration: 3000 })
          reject(new Error('Server Error: ' + detail))
        } else {
          wx.showToast({ title: '请求失败(' + statusCode + '): ' + url, icon: 'none', duration: 3000 })
          reject(new Error('Request failed: ' + statusCode + ' ' + url))
        }
      },
      fail(err) {
        if (showLoading) {
          wx.hideLoading()
        }
        wx.showToast({ title: '网络连接失败，请检查网络', icon: 'none', duration: 2000 })
        reject(err)
      }
    })
  })
}

function get(url, data, options = {}) {
  return request({ url, method: 'GET', data, ...options })
}

function post(url, data, options = {}) {
  return request({ url, method: 'POST', data, ...options })
}

function put(url, data, options = {}) {
  return request({ url, method: 'PUT', data, ...options })
}

function del(url, data, options = {}) {
  return request({ url, method: 'DELETE', data, ...options })
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
  BASE_URL
}
