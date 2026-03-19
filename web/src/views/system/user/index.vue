<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives, watch, computed } from 'vue'
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
import { useI18n } from 'vue-i18n'

const { t } = useI18n({ useScope: 'global' })

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

const columns = computed(() => [
  { title: t('views.user.label_username'), key: 'username', width: 80, align: 'center', ellipsis: { tooltip: true } },
  { title: t('views.user.label_alias'), key: 'alias', width: 80, align: 'center', render(row) { return row.alias || '-' } },
  { title: t('views.user.label_phone'), key: 'phone', width: 100, align: 'center', render(row) { return row.phone || '-' } },
  {
    title: t('views.user.label_role'), key: 'role', width: 100, align: 'center',
    render(row) {
      const roles = row.roles ?? []
      return h('span', roles.map(r =>
        h(NTag, { type: 'info', size: 'small', style: { margin: '2px 3px' } }, { default: () => r.name })
      ))
    },
  },
  {
    title: t('views.user.label_managed_regions'), key: 'managed_regions', width: 120, align: 'center',
    render(row) {
      const regions = row.managed_regions ?? []
      if (!regions.length) return h('span', { style: { color: '#999' } }, '-')
      return h('span', regions.map(r =>
        h(NTag, { type: 'success', size: 'small', style: { margin: '2px 3px' } }, { default: () => r.name })
      ))
    },
  },
  { title: t('views.user.label_email'), key: 'email', width: 80, align: 'center', ellipsis: { tooltip: true } },
  {
    title: t('views.user.label_disabled'), key: 'is_active', width: 50, align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small', rubberBand: false, value: row.is_active,
        loading: !!row.publishing, checkedValue: false, uncheckedValue: true,
        onUpdateValue: () => handleUpdateDisable(row),
      })
    },
  },
  {
    title: t('common.buttons.actions'), key: 'actions', width: 160, align: 'center', fixed: 'right',
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
          }, { default: () => t('views.user.action_edit'), icon: renderIcon('material-symbols:edit', { size: 14 }) }),
          [[vPermission, 'post/api/v1/user/update']]
        ),
        h(NButton, {
          size: 'small', type: 'info', style: 'margin-right: 6px;',
          onClick: () => openRegionEdit(row),
        }, { default: () => t('views.user.action_region'), icon: renderIcon('mdi:map-marker', { size: 14 }) }),
        h(NPopconfirm, {
          onPositiveClick: () => handleDelete({ user_id: row.id }, false),
        }, {
          trigger: () => withDirectives(
            h(NButton, { size: 'small', type: 'error', style: 'margin-right: 6px;' },
              { default: () => t('views.user.action_delete'), icon: renderIcon('material-symbols:delete-outline', { size: 14 }) }),
            [[vPermission, 'delete/api/v1/user/delete']]
          ),
          default: () => h('div', {}, t('views.user.message_delete_confirm')),
        }),
        !row.is_superuser && h(NPopconfirm, {
          onPositiveClick: async () => {
            try {
              await api.resetPassword({ user_id: row.id })
              $message.success(t('views.user.message_reset_password_success'))
              $table.value?.handleSearch()
            } catch (error) { $message.error(t('views.user.message_reset_password_failed') + ': ' + error.message) }
          },
        }, {
          trigger: () => withDirectives(
            h(NButton, { size: 'small', type: 'warning' },
              { default: () => t('views.user.action_reset_password'), icon: renderIcon('material-symbols:lock-reset', { size: 14 }) }),
            [[vPermission, 'post/api/v1/user/reset_password']]
          ),
          default: () => h('div', {}, t('views.user.message_reset_password_confirm')),
        }),
      ]
    },
  },
])

async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) { $message.error(t('views.user.message_cannot_disable_self')); return }
  row.publishing = true
  row.is_active = !row.is_active
  row.publishing = false
  row.role_ids = row.roles.map(e => e.id)
  row.dept_id = row.dept?.id
  try {
    await api.updateUser(row)
    $message?.success(row.is_active ? t('views.user.message_enabled') : t('views.user.message_disabled'))
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
    window.$message?.success(t('views.user.message_region_success'))
    showRegionModal.value = false
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || t('views.user.message_region_failed'))
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

const validateAddUser = computed(() => ({
  username: [{ required: true, message: t('views.user.validate_username_required'), trigger: ['input', 'blur'] }],
  email: [
    { required: true, message: t('views.user.validate_email_required'), trigger: ['input', 'change'] },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (!/^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/.test(modalForm.value.email)) {
          callback(t('views.user.validate_email_format')); return
        }
        callback()
      },
    },
  ],
  password: [{ required: true, message: t('views.user.validate_password_required'), trigger: ['input', 'blur', 'change'] }],
  confirmPassword: [
    { required: true, message: t('views.user.validate_confirm_password_required'), trigger: ['input'] },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) { callback(t('views.user.validate_password_mismatch')); return }
        callback()
      },
    },
  ],
}))
</script>

<template>
  <NLayout has-sider wh-full>
    <NLayoutSider bordered content-style="padding: 24px;" :collapsed-width="0" :width="240" show-trigger="arrow-circle">
      <h1>{{ t('views.user.label_dept_list') }}</h1>
      <br />
      <NTree block-line :data="deptOption" key-field="id" label-field="name" default-expand-all :node-props="nodeProps" />
    </NLayoutSider>
    <NLayoutContent>
      <CommonPage show-footer :title="t('views.user.label_user_list')">
        <template #action>
          <NButton v-permission="'post/api/v1/user/create'" type="primary" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />{{ t('views.user.label_create_user') }}
          </NButton>
        </template>

        <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getUserList">
          <template #queryBar>
            <QueryBarItem :label="t('views.user.label_query_name')" :label-width="40">
              <NInput v-model:value="queryItems.username" clearable :placeholder="t('views.user.placeholder_username_input')" @keypress.enter="$table?.handleSearch()" />
            </QueryBarItem>
            <QueryBarItem :label="t('views.user.label_query_email')" :label-width="40">
              <NInput v-model:value="queryItems.email" clearable :placeholder="t('views.user.placeholder_email_input')" @keypress.enter="$table?.handleSearch()" />
            </QueryBarItem>
          </template>
        </CrudTable>

        <!-- Create/Edit user modal -->
        <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
          <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="80"
            :model="modalForm" :rules="validateAddUser">
            <NFormItem :label="t('views.user.label_username')" path="username">
              <NInput v-model:value="modalForm.username" clearable :placeholder="t('views.user.placeholder_username')" />
            </NFormItem>
            <NFormItem :label="t('views.user.label_alias')" path="alias">
              <NInput v-model:value="modalForm.alias" clearable :placeholder="t('views.user.placeholder_alias')" />
            </NFormItem>
            <NFormItem :label="t('views.user.label_phone')" path="phone">
              <NInput v-model:value="modalForm.phone" clearable :placeholder="t('views.user.placeholder_phone')" />
            </NFormItem>
            <NFormItem :label="t('views.user.label_email')" path="email">
              <NInput v-model:value="modalForm.email" clearable :placeholder="t('views.user.placeholder_email')" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" :label="t('views.user.label_password')" path="password">
              <NInput v-model:value="modalForm.password" show-password-on="mousedown" type="password" clearable :placeholder="t('views.user.placeholder_password')" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" :label="t('views.user.label_confirm_password')" path="confirmPassword">
              <NInput v-model:value="modalForm.confirmPassword" show-password-on="mousedown" type="password" clearable :placeholder="t('views.user.placeholder_confirm_password')" />
            </NFormItem>
            <NFormItem :label="t('views.user.label_role')" path="role_ids">
              <NCheckboxGroup v-model:value="modalForm.role_ids">
                <NSpace item-style="display: flex;">
                  <NCheckbox v-for="item in roleOption" :key="item.id" :value="item.id" :label="item.name" />
                </NSpace>
              </NCheckboxGroup>
            </NFormItem>
            <NFormItem :label="t('views.user.label_is_superuser')" path="is_superuser">
              <NSwitch v-model:value="modalForm.is_superuser" size="small" :checked-value="true" :unchecked-value="false" />
            </NFormItem>
            <NFormItem :label="t('views.user.label_disabled')" path="is_active">
              <NSwitch v-model:value="modalForm.is_active" :checked-value="false" :unchecked-value="true" :default-value="true" />
            </NFormItem>
            <NFormItem :label="t('views.user.label_dept')" path="dept_id">
              <NTreeSelect v-model:value="modalForm.dept_id" :options="deptOption" key-field="id" label-field="name"
                :placeholder="t('views.user.placeholder_select_dept')" clearable default-expand-all />
            </NFormItem>
          </NForm>
        </CrudModal>

        <!-- Region edit modal -->
        <NModal v-model:show="showRegionModal" :title="t('views.user.label_set_region')" preset="card" style="width: 550px">
          <div style="margin-bottom: 12px; color: #666;">
            {{ t('views.user.label_region_desc', { name: regionEditUser?.alias || regionEditUser?.username }) }}
          </div>
          <NForm label-placement="left" :label-width="80">
            <NFormItem :label="t('views.user.label_select_city')">
              <NSelect v-model:value="regionEditCityId" :options="cityOptions" :placeholder="t('views.user.placeholder_select_city')" clearable />
            </NFormItem>
            <NFormItem :label="t('views.user.label_select_region')">
              <NSelect v-model:value="regionEditValues" :options="regionFlatOptions" :placeholder="t('views.user.placeholder_select_region')"
                multiple filterable clearable :disabled="!regionEditCityId" />
            </NFormItem>
          </NForm>
          <template #action>
            <NSpace justify="end">
              <NButton @click="showRegionModal = false">{{ t('common.buttons.cancel') }}</NButton>
              <NButton type="primary" :loading="regionSaving" @click="saveRegions">{{ t('common.buttons.save') }}</NButton>
            </NSpace>
          </template>
        </NModal>
      </CommonPage>
    </NLayoutContent>
  </NLayout>
</template>
