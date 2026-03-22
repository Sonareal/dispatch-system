import { request } from '@/utils'

export default {
  // === Auth & Base ===
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getSiteConfig: () => request.get('/site/config', { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  updatePassword: (data = {}) => request.post('/base/update_password', data),

  // === Users ===
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  getUserManagedRegions: (params = {}) => request.get('/user/managed_regions', { params }),
  setUserManagedRegions: (data = {}) => request.post('/user/set_managed_regions', data),

  // === Roles ===
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),

  // === Menus ===
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),

  // === APIs ===
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),

  // === Departments ===
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),

  // === Audit Log ===
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),

  // === Cities ===
  getCityList: (params = {}) => request.get('/city/list', { params }),
  getCity: (params = {}) => request.get('/city/get', { params }),
  createCity: (data = {}) => request.post('/city/create', data),
  updateCity: (data = {}) => request.post('/city/update', data),
  deleteCity: (params = {}) => request.delete('/city/delete', { params }),
  getUserCities: () => request.get('/city/user_cities'),
  setUserCities: (data = {}) => request.post('/city/set_user_cities', null, { params: data }),

  // === Regions ===
  getRegionList: (params = {}) => request.get('/region/list', { params }),
  getRegionTree: (params = {}) => request.get('/region/tree', { params }),
  getRegion: (params = {}) => request.get('/region/get', { params }),
  createRegion: (data = {}) => request.post('/region/create', data),
  updateRegion: (data = {}) => request.post('/region/update', data),
  deleteRegion: (params = {}) => request.delete('/region/delete', { params }),
  setRegionManager: (data = {}) => request.post('/region/set_manager', null, { params: data }),
  setRegionManagers: (data = {}) => request.post('/region/set_managers', data),
  getRegionManagers: (params = {}) => request.get('/region/managers', { params }),

  // === Tickets ===
  createTicket: (data = {}) => request.post('/ticket/create', data),
  getTicketList: (params = {}) => request.get('/ticket/list', { params }),
  getTicket: (params = {}) => request.get('/ticket/get', { params }),
  updateTicket: (data = {}) => request.post('/ticket/update', data),
  submitTicket: (data = {}) => request.post('/ticket/submit', data),
  withdrawTicket: (data = {}) => request.post('/ticket/withdraw', data),
  revertToReview: (data = {}) => request.post('/ticket/revert_to_review', data),
  auditTicket: (data = {}) => request.post('/ticket/audit', data),
  assignTicket: (data = {}) => request.post('/ticket/assign', data),
  transferTicket: (data = {}) => request.post('/ticket/transfer', data),
  updateTicketStatus: (data = {}) => request.post('/ticket/update_status', data),
  getFlowRecords: (params = {}) => request.get('/ticket/flow_records', { params }),
  getAuditRecords: (params = {}) => request.get('/ticket/audit_records', { params }),
  getPendingReviewTickets: (params = {}) => request.get('/ticket/pending_review', { params }),
  getMyAssignedTickets: (params = {}) => request.get('/ticket/my_assigned', { params }),
  getAssignableUsers: (params = {}) => request.get('/ticket/assignable_users', { params }),
  getTicketStatistics: (params = {}) => request.get('/ticket/statistics', { params }),

  // === Messages ===
  sendMessage: (data = {}) => request.post('/message/send', data),
  getMessageList: (params = {}) => request.get('/message/list', { params }),
  getTicketMessages: (params = {}) => request.get('/message/ticket_messages', { params }),
  markMessagesRead: (data = []) => request.post('/message/mark_read', data),
  getUnreadCount: () => request.get('/message/unread_count'),
  pushNotification: (data = {}) => request.post('/message/push', data),
  getMyNotifications: (params = {}) => request.get('/message/my_notifications', { params }),
  uploadVoiceMessage: (data) => request.post('/message/upload_voice', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteMessage: (message_id) => request.post('/message/delete', { message_id }),

  // === Calls ===
  initiateCall: (data = {}) => request.post('/message/call/initiate', data),
  answerCall: (data = {}) => request.post('/message/call/answer', data),
  hangupCall: (data = {}) => request.post('/message/call/hangup', data),
  getCallRecords: (params = {}) => request.get('/message/call/records', { params }),

  // === Operation Log ===
  getOpLogList: (params = {}) => request.get('/oplog/list', { params }),

  // === System Config ===
  getSysConfigList: (params = {}) => request.get('/sysconfig/list', { params }),
  getSysConfig: (params = {}) => request.get('/sysconfig/get', { params }),
  setSysConfig: (data = {}) => request.post('/sysconfig/set', data),
  deleteSysConfig: (params = {}) => request.delete('/sysconfig/delete', { params }),
}
