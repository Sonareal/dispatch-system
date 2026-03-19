<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NTag, NSpace, NModal, NForm, NFormItem, NInput, NSelect } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import api from '@/api'

defineOptions({ name: '我负责的工单' })

const $table = ref(null)
const queryItems = ref({})

const statusLabelMap = {
  assigned: '已指派', processing: '处理中', transferred: '已转派',
  completed: '已完成', closed: '已关闭',
}
const statusColorMap = {
  assigned: 'info', processing: 'success', transferred: 'info',
  completed: 'success', closed: 'default',
}

const statusFilterOptions = [
  { label: '全部', value: '' },
  { label: '已指派', value: 'assigned' },
  { label: '处理中', value: 'processing' },
  { label: '已转派', value: 'transferred' },
  { label: '已完成', value: 'completed' },
]

// Transfer modal
const showTransferModal = ref(false)
const transferForm = ref({ ticket_id: null, transfer_to_id: null, reason: '' })
const transferLoading = ref(false)
const userOptions = ref([])

onMounted(() => {
  $table.value?.handleSearch()
  api.getUserList({ page: 1, page_size: 999 }).then((res) => {
    userOptions.value = (res.data || []).map((u) => ({ label: u.alias || u.username, value: u.id }))
  })
})

const columns = [
  { title: '工单号', key: 'ticket_no', width: 160, ellipsis: { tooltip: true } },
  { title: '客户姓名', key: 'customer_name', width: 80, align: 'center' },
  { title: '联系电话', key: 'customer_phone', width: 100, align: 'center' },
  {
    title: '状态', key: 'status', width: 80, align: 'center',
    render(row) {
      return h(NTag, { type: statusColorMap[row.status] || 'default', size: 'small' },
        { default: () => statusLabelMap[row.status] || row.status })
    },
  },
  { title: '创建时间', key: 'created_at', width: 140, align: 'center' },
  {
    title: '操作', key: 'actions', width: 180, align: 'center', fixed: 'right',
    render(row) {
      const btns = []
      if (row.status === 'assigned' || row.status === 'transferred') {
        btns.push(h(NButton, { size: 'small', type: 'success', onClick: () => startProcess(row) },
          { default: () => '开始处理' }))
      }
      if (row.status === 'processing') {
        btns.push(h(NButton, { size: 'small', type: 'primary', onClick: () => completeTicket(row) },
          { default: () => '完成' }))
      }
      if (['assigned', 'processing'].includes(row.status)) {
        btns.push(h(NButton, { size: 'small', onClick: () => openTransfer(row) },
          { default: () => '转派' }))
      }
      return h(NSpace, { justify: 'center', size: 'small' }, { default: () => btns })
    },
  },
]

async function startProcess(row) {
  await api.updateTicketStatus({ ticket_id: row.id, status: 'processing', remark: '开始处理' })
  window.$message?.success('已开始处理')
  $table.value?.handleSearch()
}

async function completeTicket(row) {
  await api.updateTicketStatus({ ticket_id: row.id, status: 'completed', remark: '处理完成' })
  window.$message?.success('工单已完成')
  $table.value?.handleSearch()
}

function openTransfer(row) {
  transferForm.value = { ticket_id: row.id, transfer_to_id: null, reason: '' }
  showTransferModal.value = true
}

async function handleTransfer() {
  if (!transferForm.value.transfer_to_id) {
    window.$message?.warning('请选择转派目标')
    return
  }
  transferLoading.value = true
  try {
    await api.transferTicket(transferForm.value)
    window.$message?.success('转派成功')
    showTransferModal.value = false
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || '转派失败')
  } finally {
    transferLoading.value = false
  }
}
</script>

<template>
  <CommonPage show-footer title="我负责的工单">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getMyAssignedTickets"
    >
      <template #queryBar>
        <QueryBarItem label="状态" :label-width="35">
          <NSelect v-model:value="queryItems.status" :options="statusFilterOptions" clearable
            style="width: 120px" @update:value="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="showTransferModal" title="转派工单" preset="card" style="width: 450px">
      <NForm :model="transferForm" label-placement="left" :label-width="80">
        <NFormItem label="转派给">
          <NSelect v-model:value="transferForm.transfer_to_id" :options="userOptions" placeholder="选择处理人" />
        </NFormItem>
        <NFormItem label="转派原因">
          <NInput v-model:value="transferForm.reason" type="textarea" placeholder="转派原因" />
        </NFormItem>
      </NForm>
      <template #action>
        <NSpace justify="end">
          <NButton @click="showTransferModal = false">取消</NButton>
          <NButton type="primary" :loading="transferLoading" @click="handleTransfer">确认转派</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
