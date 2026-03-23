const { get, post } = require('../../utils/request')

Page({
  data: {
    users: [],
    roles: [],
    regions: [],
    citiesData: [],
    selectedCityId: null,
    loading: false,
    // Edit modal
    showEditModal: false,
    editUser: null,
    selectedRoleIds: [],
    selectedRegionIds: [],
    rolesWithSelected: [],
    regionsWithSelected: [],
  },

  onLoad() {
    this.fetchData()
  },

  async fetchData() {
    this.setData({ loading: true })
    try {
      const [usersRes, rolesRes, citiesRes] = await Promise.all([
        get('/user/list', { page_size: 999 }, { showLoading: false }),
        get('/role/list', {}, { showLoading: false }),
        get('/city/list', { is_active: true }, { showLoading: false }),
      ])
      this.setData({
        users: (usersRes.data || []).map(u => ({
          ...u,
          avatarChar: (u.alias || u.username || '?').charAt(0),
          role_text: (u.roles || []).map(r => r.name).join('、') || '无',
          region_text: (u.managed_regions || []).join('、') || '无',
        })),
        roles: rolesRes.data || [],
        citiesData: citiesRes.data || [],
        loading: false,
      })
    } catch (e) {
      console.error('Failed to fetch data:', e)
      this.setData({ loading: false })
    }
  },

  onEditUser(e) {
    const userId = e.currentTarget.dataset.id
    const user = this.data.users.find(u => u.id === userId)
    if (!user) return

    const selectedRoleIds = (user.roles || []).map(r => r.id)

    const cityId = user.default_city_id || (this.data.citiesData.length > 0 ? this.data.citiesData[0].id : null)

    this.setData({
      showEditModal: true,
      editUser: user,
      selectedRoleIds,
      selectedCityId: cityId,
    })
    this._refreshChips()

    if (cityId) {
      this.loadRegions(cityId)
    }
  },

  async loadRegions(cityId) {
    try {
      const res = await get('/region/tree', { city_id: cityId }, { showLoading: false })
      // Flatten tree to get district-level regions
      const regions = []
      const flatten = (nodes) => {
        for (const n of nodes) {
          if (n.level === 'district' || (!n.children || n.children.length === 0)) {
            regions.push(n)
          }
          if (n.children) flatten(n.children)
        }
      }
      flatten(res.data || [])
      this.setData({ regions })
      this._refreshChips()
    } catch (e) {
      console.error('Failed to load regions:', e)
    }
  },

  _refreshChips() {
    const roleIds = this.data.selectedRoleIds
    const regionIds = this.data.selectedRegionIds
    this.setData({
      rolesWithSelected: this.data.roles.map(r => ({ ...r, selected: roleIds.indexOf(r.id) >= 0 })),
      regionsWithSelected: this.data.regions.map(r => ({ ...r, selected: regionIds.indexOf(r.id) >= 0 })),
    })
  },

  onCitySelect(e) {
    const cityId = e.currentTarget.dataset.id
    this.setData({ selectedCityId: cityId, selectedRegionIds: [], regions: [] })
    this.loadRegions(cityId)
  },

  closeEditModal() {
    this.setData({ showEditModal: false, editUser: null, selectedRoleIds: [], selectedRegionIds: [], rolesWithSelected: [], regionsWithSelected: [] })
  },

  onRoleToggle(e) {
    const roleId = e.currentTarget.dataset.id
    let ids = [...this.data.selectedRoleIds]
    const idx = ids.indexOf(roleId)
    if (idx >= 0) {
      ids.splice(idx, 1)
    } else {
      ids.push(roleId)
    }
    this.setData({ selectedRoleIds: ids })
    this._refreshChips()
  },

  onRegionToggle(e) {
    const regionId = e.currentTarget.dataset.id
    let ids = [...this.data.selectedRegionIds]
    const idx = ids.indexOf(regionId)
    if (idx >= 0) {
      ids.splice(idx, 1)
    } else {
      ids.push(regionId)
    }
    this.setData({ selectedRegionIds: ids })
    this._refreshChips()
  },

  async saveUser() {
    const user = this.data.editUser
    if (!user) return

    try {
      // Update roles
      await post('/user/update_roles', {
        user_id: user.id,
        role_ids: this.data.selectedRoleIds,
      })

      // Update managed regions
      await post('/user/set_managed_regions', {
        user_id: user.id,
        region_ids: this.data.selectedRegionIds,
      })

      wx.showToast({ title: '保存成功', icon: 'success' })
      this.closeEditModal()
      this.fetchData()
    } catch (e) {
      console.error('Failed to save:', e)
    }
  },

  async onToggleActive(e) {
    const userId = e.currentTarget.dataset.id
    const active = e.currentTarget.dataset.active
    try {
      await post('/user/toggle_active', { user_id: userId, is_active: !active })
      wx.showToast({ title: active ? '已禁用' : '已启用', icon: 'success' })
      this.fetchData()
    } catch (e) {
      console.error('Toggle failed:', e)
    }
  },
})
