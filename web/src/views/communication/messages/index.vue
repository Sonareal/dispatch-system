<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NTag, NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NSpace } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '消息记录' })

const { t } = useI18n({ useScope: 'global' })

const $table = ref(null)
const queryItems = ref({})
const showPushModal = ref(false)
const pushForm = ref({ user_id: null, ticket_id: null, content: '', title: '' })
const pushLoading = ref(false)
const userOptions = ref([])

const msgTypeColorMap = { text: 'info', voice: 'warning', image: 'success', system: 'default' }

onMounted(() => {
  $table.value?.handleSearch()
  api.getUserList({ page: 1, page_size: 999 }).then((res) => {
    userOptions.value = (res.data || []).map((u) => ({ label: u.alias || u.username, value: u.id }))
  })
})

const msgTypeOptions = computed(() => [
  { label: t('views.communication.msg_type_text'), value: 'text' },
  { label: t('views.communication.msg_type_voice'), value: 'voice' },
  { label: t('views.communication.msg_type_image'), value: 'image' },
  { label: t('views.communication.msg_type_system'), value: 'system' },
])

const columns = computed(() => [
  { title: t('views.communication.col_id'), key: 'id', width: 60, align: 'center' },
  { title: t('views.communication.col_ticket_id'), key: 'ticket_id', width: 80, align: 'center' },
  { title: t('views.communication.col_sender'), key: 'sender_name', width: 80, align: 'center' },
  { title: t('views.communication.col_receiver'), key: 'receiver_name', width: 80, align: 'center' },
  {
    title: t('views.communication.col_msg_type'), key: 'msg_type', width: 60, align: 'center',
    render(row) {
      const msgTypeMap = { text: t('views.communication.msg_type_text'), voice: t('views.communication.msg_type_voice'), image: t('views.communication.msg_type_image'), system: t('views.communication.msg_type_system') }
      return h(NTag, { type: msgTypeColorMap[row.msg_type] || 'default', size: 'small' }, { default: () => msgTypeMap[row.msg_type] || row.msg_type })
    },
  },
  { title: t('views.communication.col_content'), key: 'content', width: 250, ellipsis: { tooltip: true } },
  {
    title: t('views.communication.col_is_read'), key: 'is_read', width: 60, align: 'center',
    render(row) { return h(NTag, { type: row.is_read ? 'success' : 'warning', size: 'small' }, { default: () => row.is_read ? t('views.communication.label_read') : t('views.communication.label_unread') }) },
  },
  { title: t('views.communication.col_send_time'), key: 'created_at', width: 140, align: 'center' },
])

function openPush() {
  pushForm.value = { user_id: null, ticket_id: null, content: '', title: t('views.communication.label_system_notification') }
  showPushModal.value = true
}

async function handlePush() {
  if (!pushForm.value.user_id) { window.$message?.warning(t('views.communication.message_select_user')); return }
  if (!pushForm.value.content) { window.$message?.warning(t('views.communication.message_input_content')); return }
  pushLoading.value = true
  try {
    await api.pushNotification(pushForm.value)
    window.$message?.success(t('views.communication.message_push_success'))
    showPushModal.value = false
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || t('views.communication.message_push_failed'))
  } finally {
    pushLoading.value = false
  }
}
</script>

<template>
  <CommonPage show-footer :title="t('views.communication.title_message_records')">
    <template #action>
      <NButton type="primary" @click="openPush">
        <TheIcon icon="mdi:send" :size="16" class="mr-5" />{{ t('views.communication.label_push_notification') }}
      </NButton>
    </template>

    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getMessageList">
      <template #queryBar>
        <QueryBarItem :label="t('views.communication.col_ticket_id')" :label-width="50">
          <NInputNumber v-model:value="queryItems.ticket_id" clearable :placeholder="t('views.communication.placeholder_ticket_id')"
            style="width: 120px" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem :label="t('views.communication.col_msg_type')" :label-width="35">
          <NSelect v-model:value="queryItems.msg_type" clearable style="width: 100px"
            :options="msgTypeOptions"
            @update:value="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="showPushModal" :title="t('views.communication.label_push_notification')" preset="card" style="width: 500px">
      <NForm :model="pushForm" label-placement="left" :label-width="80">
        <NFormItem :label="t('views.communication.label_target_user')">
          <NSelect v-model:value="pushForm.user_id" :options="userOptions" :placeholder="t('views.communication.placeholder_select_user')" filterable />
        </NFormItem>
        <NFormItem :label="t('views.communication.label_related_ticket')">
          <NInputNumber v-model:value="pushForm.ticket_id" :placeholder="t('views.communication.placeholder_ticket_id_optional')" style="width: 100%" />
        </NFormItem>
        <NFormItem :label="t('views.communication.label_title')"><NInput v-model:value="pushForm.title" :placeholder="t('views.communication.placeholder_notification_title')" /></NFormItem>
        <NFormItem :label="t('views.communication.label_content')"><NInput v-model:value="pushForm.content" type="textarea" :placeholder="t('views.communication.placeholder_notification_content')" :rows="3" /></NFormItem>
      </NForm>
      <template #action>
        <NSpace justify="end">
          <NButton @click="showPushModal = false">{{ t('views.communication.action_cancel') }}</NButton>
          <NButton type="primary" :loading="pushLoading" @click="handlePush">{{ t('views.communication.action_send') }}</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
