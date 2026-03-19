<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NTag, NSpace } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import api from '@/api'

defineOptions({ name: '我的工单' })

const $table = ref(null)
const queryItems = ref({ my_tickets: true })

const statusLabelMap = {
  pending_review: '待审核', approved: '审核通过', rejected: '已驳回',
  pending_assign: '待指派', assigned: '已指派', processing: '处理中',
  transferred: '已转派', completed: '已完成', closed: '已关闭',
}
const statusColorMap = {
  pending_review: 'warning', approved: 'info', rejected: 'error',
  pending_assign: 'warning', assigned: 'info', processing: 'success',
  transferred: 'info', completed: 'success', closed: 'default',
}

onMounted(() => $table.value?.handleSearch())

const columns = [
  { title: '工单号', key: 'ticket_no', width: 160, ellipsis: { tooltip: true } },
  { title: '客户姓名', key: 'customer_name', width: 80, align: 'center' },
  { title: '联系电话', key: 'customer_phone', width: 100, align: 'center' },
  {
    title: '申请金额', key: 'apply_amount', width: 80, align: 'center',
    render(row) { return row.apply_amount ? `¥${row.apply_amount}` : '-' },
  },
  {
    title: '状态', key: 'status', width: 80, align: 'center',
    render(row) {
      return h(NTag, { type: statusColorMap[row.status] || 'default', size: 'small' },
        { default: () => statusLabelMap[row.status] || row.status })
    },
  },
  { title: '处理人', key: 'assignee_name', width: 80, align: 'center' },
  { title: '创建时间', key: 'created_at', width: 140, align: 'center' },
]
</script>

<template>
  <CommonPage show-footer title="我的工单">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getTicketList"
    >
      <template #queryBar>
        <QueryBarItem label="工单号" :label-width="50">
          <n-input v-model:value="queryItems.ticket_no" clearable placeholder="工单号"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
