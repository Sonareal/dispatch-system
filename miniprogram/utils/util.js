/**
 * Format date to YYYY-MM-DD HH:mm:ss
 */
function formatTime(date) {
  if (!date) return ''
  if (typeof date === 'string') {
    date = new Date(date)
  }
  if (typeof date === 'number') {
    date = new Date(date)
  }

  const year = date.getFullYear()
  const month = padZero(date.getMonth() + 1)
  const day = padZero(date.getDate())
  const hour = padZero(date.getHours())
  const minute = padZero(date.getMinutes())
  const second = padZero(date.getSeconds())

  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

/**
 * Format date to YYYY-MM-DD
 */
function formatDate(date) {
  if (!date) return ''
  if (typeof date === 'string') {
    date = new Date(date)
  }

  const year = date.getFullYear()
  const month = padZero(date.getMonth() + 1)
  const day = padZero(date.getDate())

  return `${year}-${month}-${day}`
}

/**
 * Pad number with leading zero
 */
function padZero(n) {
  return n < 10 ? '0' + n : '' + n
}

/**
 * Format relative time (e.g., "3分钟前", "2小时前")
 */
function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return Math.floor(diff / minute) + '分钟前'
  } else if (diff < day) {
    return Math.floor(diff / hour) + '小时前'
  } else if (diff < 7 * day) {
    return Math.floor(diff / day) + '天前'
  } else {
    return formatTime(date)
  }
}

/**
 * Ticket status map
 */
const STATUS_MAP = {
  pending_review: { text: '待审核', color: '#ff9900', tagClass: 'tag-orange' },
  approved: { text: '已审核', color: '#2d8cf0', tagClass: 'tag-blue' },
  rejected: { text: '已驳回', color: '#ed4014', tagClass: 'tag-red' },
  processing: { text: '处理中', color: '#2d8cf0', tagClass: 'tag-blue' },
  inspecting: { text: '验车中', color: '#ff9900', tagClass: 'tag-orange' },
  completed: { text: '已完成', color: '#19be6b', tagClass: 'tag-green' },
  cancelled: { text: '已取消', color: '#999999', tagClass: 'tag-grey' }
}

/**
 * Get status display info
 */
function getStatusInfo(status) {
  return STATUS_MAP[status] || { text: status || '未知', color: '#999999', tagClass: 'tag-grey' }
}

/**
 * Format phone number with mask (e.g., 138****5678)
 */
function maskPhone(phone) {
  if (!phone || phone.length < 7) return phone || ''
  return phone.substring(0, 3) + '****' + phone.substring(phone.length - 4)
}

/**
 * Format ID card with mask
 */
function maskIdCard(idCard) {
  if (!idCard || idCard.length < 10) return idCard || ''
  return idCard.substring(0, 4) + '**********' + idCard.substring(idCard.length - 4)
}

/**
 * Format amount to 2 decimal places with comma separator
 */
function formatAmount(amount) {
  if (amount === null || amount === undefined || amount === '') return '0.00'
  const num = parseFloat(amount)
  if (isNaN(num)) return '0.00'
  return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * Validate phone number
 */
function isValidPhone(phone) {
  return /^1[3-9]\d{9}$/.test(phone)
}

/**
 * Validate ID card number (simplified)
 */
function isValidIdCard(idCard) {
  return /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/.test(idCard)
}

/**
 * Debounce function
 */
function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * Deep clone object
 */
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  return JSON.parse(JSON.stringify(obj))
}

module.exports = {
  formatTime,
  formatDate,
  formatRelativeTime,
  padZero,
  getStatusInfo,
  maskPhone,
  maskIdCard,
  formatAmount,
  isValidPhone,
  isValidIdCard,
  debounce,
  deepClone,
  STATUS_MAP
}
