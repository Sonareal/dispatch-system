<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NTag, NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NSpace } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '消息记录' })

const $table = ref(null)
const queryItems = ref({})
const showPushModal = ref(false)
const pushForm = ref({ user_id: null, ticket_id: null, content: '', title: '系统通知' })
const pushLoading = ref(false)
const userOptions = ref([])

const msgTypeMap = { text: '文字', voice: '语音', image: '图片', system: '系统' }
const msgTypeColorMap = { text: 'info', voice: 'warning', image: 'success', system: 'default' }

onMounted(() => {
  $table.value?.handleSearch()
  api.getUserList({ page: 1, page_size: 999 }).then((res) => {
    userOptions.value = (res.data || []).map((u) => ({ label: u.alias || u.username, value: u.id }))
  })
})

const columns = [
  { title: 'ID', key: 'id', width: 60, align: 'center' },
  { title: '工单ID', key: 'ticket_id', width: 80, align: 'center' },
  { title: '发送人', key: 'sender_name', width: 80, align: 'center' },
  { title: '接收人', key: 'receiver_name', width: 80, align: 'center' },
  {
    title: '类型', key: 'msg_type', width: 60, align: 'center',
    render(row) { return h(NTag, { type: msgTypeColorMap[row.msg_type] || 'default', size: 'small' }, { default: () => msgTypeMap[row.msg_type] || row.msg_type }) },
  },
  { title: '内容', key: 'content', width: 250, ellipsis: { tooltip: true } },
  {
    title: '已读', key: 'is_read', width: 60, align: 'center',
    render(row) { return h(NTag, { type: row.is_read ? 'success' : 'warning', size: 'small' }, { default: () => row.is_read ? '已读' : '未读' }) },
  },
  { title: '发送时间', key: 'created_at', width: 140, align: 'center' },
]

function openPush() {
  pushForm.value = { user_id: null, ticket_id: null, content: '', title: '系统通知' }
  showPushModal.value = true
}

async function handlePush() {
  if (!pushForm.value.user_id) { window.$message?.warning('请选择目标用户'); return }
  if (!pushForm.value.content) { window.$message?.warning('请输入通知内容'); return }
  pushLoading.value = true
  try {
    await api.pushNotification(pushForm.value)
    window.$message?.success('推送成功')
    showPushModal.value = false
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || '推送失败')
  } finally {
    pushLoading.value = false
  }
}
</script>

<template>
  <CommonPage show-footer title="消息记录">
    <template #action>
      <NButton type="primary" @click="openPush">
        <TheIcon icon="mdi:send" :size="16" class="mr-5" />推送通知
      </NButton>
    </template>

    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getMessageList">
      <template #queryBar>
        <QueryBarItem label="工单ID" :label-width="50">
          <NInputNumber v-model:value="queryItems.ticket_id" clearable placeholder="工单ID"
            style="width: 120px" @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="35">
          <NSelect v-model:value="queryItems.msg_type" clearable style="width: 100px"
            :options="[{label:'文字',value:'text'},{label:'语音',value:'voice'},{label:'图片',value:'image'},{label:'系统',value:'system'}]"
            @update:value="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="showPushModal" title="推送通知" preset="card" style="width: 500px">
      <NForm :model="pushForm" label-placement="left" :label-width="80">
        <NFormItem label="目标用户">
          <NSelect v-model:value="pushForm.user_id" :options="userOptions" placeholder="选择用户" filterable />
        </NFormItem>
        <NFormItem label="关联工单">
          <NInputNumber v-model:value="pushForm.ticket_id" placeholder="工单ID(可选)" style="width: 100%" />
        </NFormItem>
        <NFormItem label="标题"><NInput v-model:value="pushForm.title" placeholder="通知标题" /></NFormItem>
        <NFormItem label="内容"><NInput v-model:value="pushForm.content" type="textarea" placeholder="通知内容" :rows="3" /></NFormItem>
      </NForm>
      <template #action>
        <NSpace justify="end">
          <NButton @click="showPushModal = false">取消</NButton>
          <NButton type="primary" :loading="pushLoading" @click="handlePush">发送</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
