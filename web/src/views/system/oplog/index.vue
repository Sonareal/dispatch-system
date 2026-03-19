<script setup>
import { onMounted, ref } from 'vue'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'

defineOptions({ name: '操作日志' })

const $table = ref(null)
const queryItems = ref({})

const columns = [
  { title: 'ID', key: 'id', width: 60, align: 'center' },
  { title: '模块', key: 'module', width: 80, align: 'center' },
  { title: '操作类型', key: 'action', width: 80, align: 'center' },
  { title: '操作人', key: 'operator_name', width: 80, align: 'center' },
  { title: '操作内容', key: 'content', width: 300, ellipsis: { tooltip: true } },
  { title: 'IP', key: 'ip', width: 100, align: 'center' },
  { title: '时间', key: 'created_at', width: 140, align: 'center' },
]

onMounted(() => $table.value?.handleSearch())
</script>

<template>
  <CommonPage show-footer title="操作日志">
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getOpLogList">
      <template #queryBar>
        <QueryBarItem label="模块" :label-width="35">
          <n-input v-model:value="queryItems.module" clearable placeholder="模块" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="操作人" :label-width="50">
          <n-input v-model:value="queryItems.operator_name" clearable placeholder="操作人" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
