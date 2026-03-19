<script setup>
import { h, onMounted, ref } from 'vue'
import { NTag } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'

defineOptions({ name: '语音记录' })

const $table = ref(null)
const queryItems = ref({ msg_type: 'voice' })

const columns = [
  { title: 'ID', key: 'id', width: 60, align: 'center' },
  { title: '工单ID', key: 'ticket_id', width: 80, align: 'center' },
  { title: '发送人', key: 'sender_name', width: 80, align: 'center' },
  { title: '接收人', key: 'receiver_name', width: 80, align: 'center' },
  { title: '文件', key: 'file_url', width: 200, ellipsis: { tooltip: true } },
  {
    title: '时长', key: 'voice_duration', width: 80, align: 'center',
    render(row) { return row.voice_duration ? `${row.voice_duration}秒` : '-' },
  },
  { title: '发送时间', key: 'created_at', width: 140, align: 'center' },
]

onMounted(() => $table.value?.handleSearch())
</script>

<template>
  <CommonPage show-footer title="语音记录">
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getMessageList">
      <template #queryBar>
        <QueryBarItem label="工单ID" :label-width="50">
          <n-input-number v-model:value="queryItems.ticket_id" clearable placeholder="工单ID" style="width: 120px"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
