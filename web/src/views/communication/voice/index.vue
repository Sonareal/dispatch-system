<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NTag } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'

defineOptions({ name: '语音记录' })

const { t } = useI18n({ useScope: 'global' })

const $table = ref(null)
const queryItems = ref({ msg_type: 'voice' })

const columns = computed(() => [
  { title: t('views.communication.col_id'), key: 'id', width: 60, align: 'center' },
  { title: t('views.communication.col_ticket_id'), key: 'ticket_id', width: 80, align: 'center' },
  { title: t('views.communication.col_sender'), key: 'sender_name', width: 80, align: 'center' },
  { title: t('views.communication.col_receiver'), key: 'receiver_name', width: 80, align: 'center' },
  { title: t('views.communication.col_file'), key: 'file_url', width: 200, ellipsis: { tooltip: true } },
  {
    title: t('views.communication.col_duration'), key: 'voice_duration', width: 80, align: 'center',
    render(row) { return row.voice_duration ? t('views.communication.duration_seconds', { n: row.voice_duration }) : '-' },
  },
  { title: t('views.communication.col_send_time'), key: 'created_at', width: 140, align: 'center' },
])

onMounted(() => $table.value?.handleSearch())
</script>

<template>
  <CommonPage show-footer :title="t('views.communication.title_voice_records')">
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getMessageList">
      <template #queryBar>
        <QueryBarItem :label="t('views.communication.col_ticket_id')" :label-width="50">
          <n-input-number v-model:value="queryItems.ticket_id" clearable :placeholder="t('views.communication.placeholder_ticket_id')" style="width: 120px"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
