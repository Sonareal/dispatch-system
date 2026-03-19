<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NSwitch, NTag, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

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

const columns = [
  { title: 'ID', key: 'id', width: 60, align: 'center' },
  { title: '城市名称', key: 'name', width: 120, align: 'center' },
  { title: '城市编码', key: 'code', width: 100, align: 'center' },
  { title: '排序', key: 'order', width: 60, align: 'center' },
  {
    title: '状态', key: 'is_active', width: 60, align: 'center',
    render(row) { return h(NTag, { type: row.is_active ? 'success' : 'error', size: 'small' }, { default: () => row.is_active ? '启用' : '禁用' }) },
  },
  { title: '创建时间', key: 'created_at', width: 140, align: 'center' },
  {
    title: '操作', key: 'actions', width: 120, align: 'center', fixed: 'right',
    render(row) {
      return [
        h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => handleEdit(row) },
          { default: () => '编辑', icon: () => renderIcon('material-symbols:edit', { size: 14 })() }),
        h(NPopconfirm, { onPositiveClick: () => handleDelete({ city_id: row.id }, false) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' },
            { default: () => '删除', icon: () => renderIcon('material-symbols:delete-outline', { size: 14 })() }),
          default: () => '确定删除该城市吗?',
        }),
      ]
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="城市管理">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="mdi:plus" :size="16" class="mr-5" />新建城市
      </NButton>
    </template>
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getCityList">
      <template #queryBar>
        <QueryBarItem label="城市名称" :label-width="65">
          <NInput v-model:value="queryItems.name" clearable placeholder="城市名称" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" :label-width="80" :model="modalForm">
        <NFormItem label="城市名称" path="name"><NInput v-model:value="modalForm.name" placeholder="城市名称" /></NFormItem>
        <NFormItem label="城市编码" path="code"><NInput v-model:value="modalForm.code" placeholder="城市编码" /></NFormItem>
        <NFormItem label="排序" path="order"><NInputNumber v-model:value="modalForm.order" style="width: 100%" /></NFormItem>
        <NFormItem label="启用" path="is_active"><NSwitch v-model:value="modalForm.is_active" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
