<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '系统配置' })

const $table = ref(null)
const queryItems = ref({})
const modalVisible = ref(false)
const modalTitle = ref('新增配置')
const modalLoading = ref(false)
const modalForm = ref({ key: '', value: '', desc: '', group: '' })
const modalFormRef = ref(null)

onMounted(() => $table.value?.handleSearch())

const columns = [
  { title: '配置键', key: 'key', width: 150 },
  { title: '配置值', key: 'value', width: 200, ellipsis: { tooltip: true } },
  { title: '说明', key: 'desc', width: 200, ellipsis: { tooltip: true } },
  { title: '分组', key: 'group', width: 100, align: 'center' },
  { title: '更新时间', key: 'updated_at', width: 140, align: 'center' },
  {
    title: '操作', key: 'actions', width: 120, align: 'center', fixed: 'right',
    render(row) {
      return [
        h(NButton, { size: 'small', type: 'primary', style: 'margin-right: 8px;', onClick: () => editConfig(row) },
          { default: () => '编辑' }),
        h(NPopconfirm, { onPositiveClick: () => deleteConfig(row.key) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除?',
        }),
      ]
    },
  },
]

function handleAdd() {
  modalTitle.value = '新增配置'
  modalForm.value = { key: '', value: '', desc: '', group: '' }
  modalVisible.value = true
}

function editConfig(row) {
  modalTitle.value = '编辑配置'
  modalForm.value = { ...row }
  modalVisible.value = true
}

async function handleSave() {
  modalLoading.value = true
  try {
    await api.setSysConfig(modalForm.value)
    window.$message?.success('保存成功')
    modalVisible.value = false
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || '保存失败')
  } finally {
    modalLoading.value = false
  }
}

async function deleteConfig(key) {
  await api.deleteSysConfig({ key })
  window.$message?.success('删除成功')
  $table.value?.handleSearch()
}
</script>

<template>
  <CommonPage show-footer title="系统配置">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="mdi:plus" :size="16" class="mr-5" />新增配置
      </NButton>
    </template>

    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getSysConfigList">
      <template #queryBar>
        <QueryBarItem label="配置键" :label-width="50">
          <NInput v-model:value="queryItems.key" clearable placeholder="配置键" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="分组" :label-width="35">
          <NInput v-model:value="queryItems.group" clearable placeholder="分组" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" :label-width="80" :model="modalForm">
        <NFormItem label="配置键" path="key"><NInput v-model:value="modalForm.key" placeholder="配置键" /></NFormItem>
        <NFormItem label="配置值" path="value"><NInput v-model:value="modalForm.value" type="textarea" placeholder="配置值" /></NFormItem>
        <NFormItem label="说明" path="desc"><NInput v-model:value="modalForm.desc" placeholder="说明" /></NFormItem>
        <NFormItem label="分组" path="group"><NInput v-model:value="modalForm.group" placeholder="分组" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
