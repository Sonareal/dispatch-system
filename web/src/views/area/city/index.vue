<script setup>
import { h, onMounted, ref, computed } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NSwitch, NTag, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n({ useScope: 'global' })

defineOptions({ name: '城市管理' })

const $table = ref(null)
const queryItems = ref({})

const {
  modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef,
  handleEdit, handleDelete, handleAdd,
} = useCRUD({
  name: '城市', initForm: { is_active: true, order: 0 },
  doCreate: api.createCity, doUpdate: api.updateCity,
  doDelete: api.deleteCity,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => $table.value?.handleSearch())

const columns = computed(() => [
  { title: t('views.city.label_id'), key: 'id', width: 60, align: 'center' },
  { title: t('views.city.label_city_name'), key: 'name', width: 120, align: 'center' },
  { title: t('views.city.label_city_code'), key: 'code', width: 100, align: 'center' },
  { title: t('views.city.label_order'), key: 'order', width: 60, align: 'center' },
  {
    title: t('views.city.label_status'), key: 'is_active', width: 60, align: 'center',
    render(row) { return h(NTag, { type: row.is_active ? 'success' : 'error', size: 'small' }, { default: () => row.is_active ? t('views.city.label_status_active') : t('views.city.label_status_inactive') }) },
  },
  { title: t('views.city.label_created_at'), key: 'created_at', width: 140, align: 'center' },
  {
    title: t('common.buttons.actions'), key: 'actions', width: 120, align: 'center', fixed: 'right',
    render(row) {
      return [
        h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
          { default: () => t('views.city.action_edit'), icon: () => renderIcon('material-symbols:edit', { size: 14 })() }),
        h(NPopconfirm, { onPositiveClick: () => handleDelete({ city_id: row.id }, false) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' },
            { default: () => t('views.city.action_delete'), icon: () => renderIcon('material-symbols:delete-outline', { size: 14 })() }),
          default: () => t('views.city.message_delete_confirm'),
        }),
      ]
    },
  },
])
</script>

<template>
  <CommonPage show-footer :title="t('views.city.label_city_management')">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="mdi:plus" :size="16" class="mr-5" />{{ t('views.city.label_create_city') }}
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getCityList">
      <template #queryBar>
        <QueryBarItem :label="t('views.city.label_city_name')" :label-width="65">
          <NInput v-model:value="queryItems.name" clearable :placeholder="t('views.city.placeholder_city_name')" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" :label-width="80" :model="modalForm">
        <NFormItem :label="t('views.city.label_city_name')" path="name"><NInput v-model:value="modalForm.name" :placeholder="t('views.city.placeholder_city_name')" /></NFormItem>
        <NFormItem :label="t('views.city.label_city_code')" path="code"><NInput v-model:value="modalForm.code" :placeholder="t('views.city.placeholder_city_code')" /></NFormItem>
        <NFormItem :label="t('views.city.label_order')" path="order"><NInputNumber v-model:value="modalForm.order" style="width: 100%" /></NFormItem>
        <NFormItem :label="t('views.city.label_is_active')" path="is_active"><NSwitch v-model:value="modalForm.is_active" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
