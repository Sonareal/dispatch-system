<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives, watch } from 'vue'
import {
  NButton, NCheckbox, NCheckboxGroup, NForm, NFormItem, NInput, NSpace,
  NSwitch, NTag, NPopconfirm, NLayout, NLayoutSider, NLayoutContent, NTreeSelect,
  NModal, NSelect, NTree,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'

defineOptions({ name: '用户管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef,
  handleEdit, handleDelete, handleAdd,
} = useCRUD({
  name: '用户',
  initForm: {},
  doCreate: api.createUser,
  doUpdate: api.updateUser,
  doDelete: api.deleteUser,
  refresh: () => $table.value?.handleSearch(),
})

const roleOption = ref([])
const deptOption = ref([])
const cityOptions = ref([])

// Region edit modal
const showRegionModal = ref(false)
const regionEditUser = ref(null)
const regionEditCityId = ref(null)
const regionFlatOptions = ref([])
const regionEditValues = ref([])
const regionSaving = ref(false)

onMounted(() => {
  $table.value?.handleSearch()
  api.getRoleList({ page: 1, page_size: 9999 }).then((res) => (roleOption.value = res.data))
  api.getDepts().then((res) => (deptOption.value = res.data))
  api.getCityList({ is_active: true }).then((res) => {
    cityOptions.value = (res.data || []).map((c) => ({ label: c.name, value: c.id }))
  })
})

const columns = [
  { title: '用户名', key: 'username', width: 80, align: 'center', ellipsis: { tooltip: true } },
  { title: '姓名', key: 'alias', width: 80, align: 'center', render(row) { return row.alias || '-' } },
  { title: '联系电话', key: 'phone', width: 100, align: 'center', render(row) { return row.phone || '-' } },
  {
    title: '角色', key: 'role', width: 100, align: 'center',
    render(row) {
      const roles = row.roles ?? []
      return h('span', roles.map(r =>
        h(NTag, { type: 'info', size: 'small', style: { margin: '2px 3px' } }, { default: () => r.name })
      ))
    },
  },
  {
    title: '负责区域', key: 'managed_regions', width: 120, align: 'center',
    render(row) {
      const regions = row.managed_regions ?? []
      if (!regions.length) return h('span', { style: { color: '#999' } }, '-')
      return h('span', regions.map(r =>
        h(NTag, { type: 'success', size: 'small', style: { margin: '2px 3px' } }, { default: () => r.name })
      ))
    },
  },
  { title: '邮箱', key: 'email', width: 80, align: 'center', ellipsis: { tooltip: true } },
  {
    title: '禁用', key: 'is_active', width: 50, align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small', rubberBand: false, value: row.is_active,
        loading: !!row.publishing, checkedValue: false, uncheckedValue: true,
        onUpdateValue: () => handleUpdateDisable(row),
      })
    },
  },
  {
    title: '操作', key: 'actions', width: 160, align: 'center', fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(NButton, {
            size: 'small', type: 'primary', style: 'margin-right: 6px;',
            onClick: () => {
              handleEdit(row)
              modalForm.value.dept_id = row.dept?.id
              modalForm.value.role_ids = row.roles.map((e) => (e = e.id))
              delete modalForm.value.dept
            },
          }, { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 14 }) }),
          [[vPermission, 'post/api/v1/user/update']]
        ),
        h(NButton, {
          size: 'small', type: 'info', style: 'margin-right: 6px;',
          onClick: () => openRegionEdit(row),
        }, { default: () => '区域', icon: renderIcon('mdi:map-marker', { size: 14 }) }),
        h(NPopconfirm, {
          onPositiveClick: () => handleDelete({ user_id: row.id }, false),
        }, {
          trigger: () => withDirectives(
            h(NButton, { size: 'small', type: 'error', style: 'margin-right: 6px;' },
              { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 14 }) }),
            [[vPermission, 'delete/api/v1/user/delete']]
          ),
          default: () => h('div', {}, '确定删除该用户吗?'),
        }),
        !row.is_superuser && h(NPopconfirm, {
          onPositiveClick: async () => {
            try {
              await api.resetPassword({ user_id: row.id })
              $message.success('密码已成功重置为123456')
              $table.value?.handleSearch()
            } catch (error) { $message.error('重置密码失败: ' + error.message) }
          },
        }, {
          trigger: () => withDirectives(
            h(NButton, { size: 'small', type: 'warning' },
              { default: () => '重置密码', icon: renderIcon('material-symbols:lock-reset', { size: 14 }) }),
            [[vPermission, 'post/api/v1/user/reset_password']]
          ),
          default: () => h('div', {}, '确定重置密码为123456吗?'),
        }),
      ]
    },
  },
]

async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) { $message.error('当前登录用户不可禁用！'); return }
  row.publishing = true
  row.is_active = !row.is_active
  row.publishing = false
  row.role_ids = row.roles.map(e => e.id)
  row.dept_id = row.dept?.id
  try {
    await api.updateUser(row)
    $message?.success(row.is_active ? '已取消禁用该用户' : '已禁用该用户')
    $table.value?.handleSearch()
  } catch (err) {
    row.is_active = !row.is_active
  } finally { row.publishing = false }
}

// Region editing
async function openRegionEdit(user) {
  regionEditUser.value = user
  regionEditCityId.value = null
  regionFlatOptions.value = []
  regionEditValues.value = []

  try {
    const res = await api.getUserManagedRegions({ user_id: user.id })
    const currentRegions = res.data || []
    regionEditValues.value = currentRegions.map(r => r.id)
    if (currentRegions.length && currentRegions[0].city_id) {
      regionEditCityId.value = currentRegions[0].city_id
    }
  } catch (e) { /* ignore */ }

  showRegionModal.value = true
}

watch(regionEditCityId, async (cityId) => {
  if (cityId) {
    const res = await api.getRegionTree({ city_id: cityId })
    regionFlatOptions.value = flattenTree(res.data || [])
  } else {
    regionFlatOptions.value = []
  }
})

function flattenTree(tree, prefix = '') {
  let result = []
  for (const node of tree) {
    result.push({ label: prefix + node.name, value: node.id })
    if (node.children?.length) {
      result = result.concat(flattenTree(node.children, prefix + node.name + ' / '))
    }
  }
  return result
}

async function saveRegions() {
  if (!regionEditUser.value) return
  regionSaving.value = true
  try {
    await api.setUserManagedRegions({ user_id: regionEditUser.value.id, region_ids: regionEditValues.value })
    window.$message?.success('区域设置成功')
    showRegionModal.value = false
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || '设置失败')
  } finally { regionSaving.value = false }
}

let lastClickedNodeId = null
const nodeProps = ({ option }) => ({
  onClick() {
    if (lastClickedNodeId === option.id) {
      $table.value?.handleSearch(); lastClickedNodeId = null
    } else {
      api.getUserList({ dept_id: option.id }).then((res) => {
        $table.value.tableData = res.data; lastClickedNodeId = option.id
      })
    }
  },
})

const validateAddUser = {
  username: [{ required: true, message: '请输入名称', trigger: ['input', 'blur'] }],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: ['input', 'change'] },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (!/^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/.test(modalForm.value.email)) {
          callback('邮箱格式错误'); return
        }
        callback()
      },
    },
  ],
  password: [{ required: true, message: '请输入密码', trigger: ['input', 'blur', 'change'] }],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: ['input'] },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) { callback('两次密码输入不一致'); return }
        callback()
      },
    },
  ],
}
</script>

<template>
  <NLayout has-sider wh-full>
    <NLayoutSider bordered content-style="padding: 24px;" :collapsed-width="0" :width="240" show-trigger="arrow-circle">
      <h1>部门列表</h1>
      <br />
      <NTree block-line :data="deptOption" key-field="id" label-field="name" default-expand-all :node-props="nodeProps" />
    </NLayoutSider>
    <NLayoutContent>
      <CommonPage show-footer title="用户列表">
        <template #action>
          <NButton v-permission="'post/api/v1/user/create'" type="primary" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建用户
          </NButton>
        </template>

        <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getUserList">
          <template #queryBar>
            <QueryBarItem label="名称" :label-width="40">
              <NInput v-model:value="queryItems.username" clearable placeholder="用户名" @keypress.enter="$table?.handleSearch()" />
            </QueryBarItem>
            <QueryBarItem label="邮箱" :label-width="40">
              <NInput v-model:value="queryItems.email" clearable placeholder="邮箱" @keypress.enter="$table?.handleSearch()" />
            </QueryBarItem>
          </template>
        </CrudTable>

        <!-- Create/Edit user modal -->
        <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
          <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="80"
            :model="modalForm" :rules="validateAddUser">
            <NFormItem label="用户名称" path="username">
              <NInput v-model:value="modalForm.username" clearable placeholder="请输入用户名称" />
            </NFormItem>
            <NFormItem label="姓名" path="alias">
              <NInput v-model:value="modalForm.alias" clearable placeholder="请输入姓名" />
            </NFormItem>
            <NFormItem label="联系电话" path="phone">
              <NInput v-model:value="modalForm.phone" clearable placeholder="请输入联系电话" />
            </NFormItem>
            <NFormItem label="邮箱" path="email">
              <NInput v-model:value="modalForm.email" clearable placeholder="请输入邮箱" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="密码" path="password">
              <NInput v-model:value="modalForm.password" show-password-on="mousedown" type="password" clearable placeholder="请输入密码" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="确认密码" path="confirmPassword">
              <NInput v-model:value="modalForm.confirmPassword" show-password-on="mousedown" type="password" clearable placeholder="请确认密码" />
            </NFormItem>
            <NFormItem label="角色" path="role_ids">
              <NCheckboxGroup v-model:value="modalForm.role_ids">
                <NSpace item-style="display: flex;">
                  <NCheckbox v-for="item in roleOption" :key="item.id" :value="item.id" :label="item.name" />
                </NSpace>
              </NCheckboxGroup>
            </NFormItem>
            <NFormItem label="超级用户" path="is_superuser">
              <NSwitch v-model:value="modalForm.is_superuser" size="small" :checked-value="true" :unchecked-value="false" />
            </NFormItem>
            <NFormItem label="禁用" path="is_active">
              <NSwitch v-model:value="modalForm.is_active" :checked-value="false" :unchecked-value="true" :default-value="true" />
            </NFormItem>
            <NFormItem label="部门" path="dept_id">
              <NTreeSelect v-model:value="modalForm.dept_id" :options="deptOption" key-field="id" label-field="name"
                placeholder="请选择部门" clearable default-expand-all />
            </NFormItem>
          </NForm>
        </CrudModal>

        <!-- Region edit modal -->
        <NModal v-model:show="showRegionModal" title="设置负责区域" preset="card" style="width: 550px">
          <div style="margin-bottom: 12px; color: #666;">
            为用户 <NTag type="info" size="small">{{ regionEditUser?.alias || regionEditUser?.username }}</NTag> 设置负责的行政区域（可多选）
          </div>
          <NForm label-placement="left" :label-width="80">
            <NFormItem label="选择城市">
              <NSelect v-model:value="regionEditCityId" :options="cityOptions" placeholder="先选择城市" clearable />
            </NFormItem>
            <NFormItem label="选择区域">
              <NSelect v-model:value="regionEditValues" :options="regionFlatOptions" placeholder="选择负责区域"
                multiple filterable clearable :disabled="!regionEditCityId" />
            </NFormItem>
          </NForm>
          <template #action>
            <NSpace justify="end">
              <NButton @click="showRegionModal = false">取消</NButton>
              <NButton type="primary" :loading="regionSaving" @click="saveRegions">保存</NButton>
            </NSpace>
          </template>
        </NModal>
      </CommonPage>
    </NLayoutContent>
  </NLayout>
</template>
