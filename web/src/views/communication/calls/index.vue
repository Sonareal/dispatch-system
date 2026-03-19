<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NTag } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'

defineOptions({ name: '通话记录' })

const { t } = useI18n({ useScope: 'global' })

const $table = ref(null)
const queryItems = ref({})

const statusColorMap = {
  initiating: 'warning', ringing: 'info', connected: 'success',
  ended: 'default', failed: 'error', missed: 'error',
}

const columns = computed(() => [
  { title: t('views.communication.col_id'), key: 'id', width: 60, align: 'center' },
  { title: t('views.communication.col_ticket_id'), key: 'ticket_id', width: 80, align: 'center' },
  { title: t('views.communication.col_caller_id'), key: 'caller_id', width: 80, align: 'center' },
  { title: t('views.communication.col_callee_id'), key: 'callee_id', width: 80, align: 'center' },
  {
    title: t('views.communication.col_status'), key: 'status', width: 80, align: 'center',
    render(row) {
      const statusMap = {
        initiating: t('views.communication.call_status_initiating'),
        ringing: t('views.communication.call_status_ringing'),
        connected: t('views.communication.call_status_connected'),
        ended: t('views.communication.call_status_ended'),
        failed: t('views.communication.call_status_failed'),
        missed: t('views.communication.call_status_missed'),
      }
      return h(NTag, { type: statusColorMap[row.status] || 'default', size: 'small' },
        { default: () => statusMap[row.status] || row.status })
    },
  },
  {
    title: t('views.communication.col_duration'), key: 'duration', width: 80, align: 'center',
    render(row) { return row.duration ? t('views.communication.duration_seconds', { n: row.duration }) : '-' },
  },
  { title: t('views.communication.col_start_time'), key: 'start_time', width: 140, align: 'center' },
  { title: t('views.communication.col_end_time'), key: 'end_time', width: 140, align: 'center' },
  { title: t('views.communication.col_created_at'), key: 'created_at', width: 140, align: 'center' },
])

onMounted(() => $table.value?.handleSearch())
</script>

<template>
  <CommonPage show-footer :title="t('views.communication.title_call_records')">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getCallRecords"
    >
      <template #queryBar>
        <QueryBarItem :label="t('views.communication.col_ticket_id')" :label-width="50">
          <n-input-number v-model:value="queryItems.ticket_id" clearable :placeholder="t('views.communication.placeholder_ticket_id')" style="width: 120px" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
