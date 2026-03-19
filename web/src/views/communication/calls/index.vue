<script setup>
import { h, onMounted, ref } from 'vue'
import { NTag } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'

defineOptions({ name: '通话记录' })

const $table = ref(null)
const queryItems = ref({})

const statusMap = {
  initiating: '发起中', ringing: '响铃中', connected: '通话中',
  ended: '已结束', failed: '失败', missed: '未接',
}
const statusColorMap = {
  initiating: 'warning', ringing: 'info', connected: 'success',
  ended: 'default', failed: 'error', missed: 'error',
}

const columns = [
  { title: 'ID', key: 'id', width: 60, align: 'center' },
  { title: '工单ID', key: 'ticket_id', width: 80, align: 'center' },
  { title: '发起人ID', key: 'caller_id', width: 80, align: 'center' },
  { title: '接听人ID', key: 'callee_id', width: 80, align: 'center' },
  {
    title: '状态', key: 'status', width: 80, align: 'center',
    render(row) {
      return h(NTag, { type: statusColorMap[row.status] || 'default', size: 'small' },
        { default: () => statusMap[row.status] || row.status })
    },
  },
  {
    title: '时长', key: 'duration', width: 80, align: 'center',
    render(row) { return row.duration ? `${row.duration}秒` : '-' },
  },
  { title: '开始时间', key: 'start_time', width: 140, align: 'center' },
  { title: '结束时间', key: 'end_time', width: 140, align: 'center' },
  { title: '创建时间', key: 'created_at', width: 140, align: 'center' },
]

onMounted(() => $table.value?.handleSearch())
</script>

<template>
  <CommonPage show-footer title="通话记录">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getCallRecords"
    >
      <template #queryBar>
        <QueryBarItem label="工单ID" :label-width="50">
          <n-input-number v-model:value="queryItems.ticket_id" clearable placeholder="工单ID" style="width: 120px" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
