const TOKEN_KEY = 'dispatch_token'
const USER_KEY = 'dispatch_user'

function getToken() {
  try {
    return wx.getStorageSync(TOKEN_KEY) || ''
  } catch (e) {
    console.error('Failed to get token:', e)
    return ''
  }
}

function setToken(token) {
  try {
    wx.setStorageSync(TOKEN_KEY, token)
  } catch (e) {
    console.error('Failed to set token:', e)
  }
}

function removeToken() {
  try {
    wx.removeStorageSync(TOKEN_KEY)
  } catch (e) {
    console.error('Failed to remove token:', e)
  }
}

function getUserInfo() {
  try {
    const data = wx.getStorageSync(USER_KEY)
    return data ? JSON.parse(data) : null
  } catch (e) {
    console.error('Failed to get user info:', e)
    return null
  }
}

function setUserInfo(info) {
  try {
    wx.setStorageSync(USER_KEY, JSON.stringify(info))
  } catch (e) {
    console.error('Failed to set user info:', e)
  }
}

function removeUserInfo() {
  try {
    wx.removeStorageSync(USER_KEY)
  } catch (e) {
    console.error('Failed to remove user info:', e)
  }
}

function clearAuth() {
  removeToken()
  removeUserInfo()
}

function isLoggedIn() {
  return !!getToken()
}

module.exports = {
  getToken,
  setToken,
  removeToken,
  getUserInfo,
  setUserInfo,
  removeUserInfo,
  clearAuth,
  isLoggedIn
}
