<script setup>
import { h, onMounted, ref, watch } from 'vue'
import {
  NButton, NForm, NFormItem, NInput, NInputNumber, NSelect, NTag, NSpace,
  NModal, NDescriptions, NDescriptionsItem, NTimeline, NTimelineItem,
  NUpload, NCascader, NTabPane, NTabs, NDivider,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

const userStore = useUserStore()

defineOptions({ name: '工单列表' })

const $table = ref(null)
const queryItems = ref({})

const statusOptions = [
  { label: '全部', value: '' }, { label: '待审核', value: 'pending_review' },
  { label: '审核通过', value: 'approved' }, { label: '已驳回', value: 'rejected' },
  { label: '待指派', value: 'pending_assign' }, { label: '已指派', value: 'assigned' },
  { label: '处理中', value: 'processing' }, { label: '已转派', value: 'transferred' },
  { label: '已完成', value: 'completed' }, { label: '已关闭', value: 'closed' },
]

const statusColorMap = {
  pending_review: 'warning', approved: 'info', rejected: 'error',
  pending_assign: 'warning', assigned: 'info', processing: 'success',
  transferred: 'info', completed: 'success', closed: 'default',
}

const statusLabelMap = {
  pending_review: '待审核', approved: '审核通过', rejected: '已驳回',
  pending_assign: '待指派', assigned: '已指派', processing: '处理中',
  transferred: '已转派', completed: '已完成', closed: '已关闭',
}

const cityOptions = ref([])
const regionOptions = ref([])
const userOptions = ref([])

// Detail modal
const showDetailModal = ref(false)
const detailData = ref(null)
const detailTab = ref('info')

// Messaging
const msgContent = ref('')
const msgSending = ref(false)
const ticketMessages = ref([])

const {
  modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleAdd,
} = useCRUD({
  name: '工单', initForm: { city_id: null, region_id: null, salesman: userStore.userInfo?.alias || userStore.userInfo?.username || '' },
  doCreate: api.createTicket, doUpdate: api.updateTicket,
  doDelete: () => Promise.resolve(),
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
  api.getCityList({ is_active: true }).then((res) => {
    cityOptions.value = (res.data || []).map((c) => ({ label: c.name, value: c.id }))
  })
  api.getUserList({ page: 1, page_size: 999 }).then((res) => {
    userOptions.value = (res.data || []).map((u) => ({ label: u.alias || u.username, value: u.id }))
  })
})

// Load region tree when city changes in create form
watch(() => modalForm.value?.city_id, async (cityId) => {
  if (cityId) {
    const res = await api.getRegionTree({ city_id: cityId })
    regionOptions.value = buildCascaderOptions(res.data || [])
  } else {
    regionOptions.value = []
  }
})

function buildCascaderOptions(tree) {
  return tree.map(node => ({
    label: node.name, value: node.id,
    children: node.children?.length ? buildCascaderOptions(node.children) : undefined,
  }))
}

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
  { title: '提交人', key: 'submitter_name', width: 80, align: 'center' },
  { title: '处理人', key: 'assignee_name', width: 80, align: 'center' },
  { title: '创建时间', key: 'created_at', width: 140, align: 'center' },
  {
    title: '操作', key: 'actions', width: 120, align: 'center', fixed: 'right',
    render(row) {
      return h(NSpace, { justify: 'center', size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', type: 'primary', onClick: () => viewDetail(row.id) },
            { default: () => '详情' }),
        ]
      })
    },
  },
]

async function viewDetail(ticketId) {
  const res = await api.getTicket({ ticket_id: ticketId })
  detailData.value = res.data
  detailTab.value = 'info'
  showDetailModal.value = true
  loadMessages(ticketId)
}

async function loadMessages(ticketId) {
  try {
    const res = await api.getTicketMessages({ ticket_id: ticketId })
    ticketMessages.value = res.data || []
  } catch (e) { ticketMessages.value = [] }
}

async function sendMsg() {
  if (!msgContent.value.trim() || !detailData.value) return
  msgSending.value = true
  try {
    await api.sendMessage({
      ticket_id: detailData.value.id,
      receiver_id: detailData.value.assignee_id || detailData.value.submitter_id,
      msg_type: 'text',
      content: msgContent.value.trim(),
    })
    msgContent.value = ''
    loadMessages(detailData.value.id)
    window.$message?.success('发送成功')
  } catch (e) {
    window.$message?.error('发送失败')
  } finally { msgSending.value = false }
}

const actionLabelMap = {
  create: '创建', submit: '提交', review_approve: '审核通过', review_reject: '审核驳回',
  assign: '指派', transfer: '转派', start_process: '开始处理', complete: '完成',
  close: '关闭', resubmit: '重新提交',
}

const validateForm = {
  customer_name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
  customer_phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  city_id: [{ required: true, type: 'number', message: '请选择城市', trigger: 'change' }],
}
</script>

<template>
  <CommonPage show-footer title="工单列表">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <template #icon><TheIcon icon="mdi:plus" :size="16" /></template>
        新建工单
      </NButton>
    </template>

    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getTicketList">
      <template #queryBar>
        <QueryBarItem label="工单号" :label-width="50">
          <NInput v-model:value="queryItems.ticket_no" clearable placeholder="工单号"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="客户姓名" :label-width="65">
          <NInput v-model:value="queryItems.customer_name" clearable placeholder="客户姓名"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="35">
          <NSelect v-model:value="queryItems.status" :options="statusOptions" clearable
            style="width: 120px" @update:value="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem label="城市" :label-width="35">
          <NSelect v-model:value="queryItems.city_id" :options="cityOptions" clearable
            style="width: 120px" @update:value="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- Create ticket modal -->
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="80"
        :model="modalForm" :rules="validateForm">
        <NFormItem label="客户姓名" path="customer_name">
          <NInput v-model:value="modalForm.customer_name" placeholder="请输入客户姓名" />
        </NFormItem>
        <NFormItem label="联系电话" path="customer_phone">
          <NInput v-model:value="modalForm.customer_phone" placeholder="请输入联系电话" />
        </NFormItem>
        <NFormItem label="身份证号"><NInput v-model:value="modalForm.id_card" placeholder="请输入身份证号" /></NFormItem>
        <NFormItem label="申请金额"><NInputNumber v-model:value="modalForm.apply_amount" placeholder="申请金额" style="width: 100%" /></NFormItem>
        <NFormItem label="还款方式"><NInput v-model:value="modalForm.repayment_method" placeholder="还款方式" /></NFormItem>
        <NFormItem label="详细地址"><NInput v-model:value="modalForm.address" placeholder="详细地址" type="textarea" /></NFormItem>
        <NFormItem label="城市" path="city_id">
          <NSelect v-model:value="modalForm.city_id" :options="cityOptions" placeholder="请选择城市" />
        </NFormItem>
        <NFormItem label="所属区域">
          <NCascader v-model:value="modalForm.region_id" :options="regionOptions" placeholder="选择区域"
            clearable check-strategy="child" :show-path="true" />
        </NFormItem>
        <NFormItem label="业务员"><NInput v-model:value="modalForm.salesman" placeholder="业务员" /></NFormItem>
        <NFormItem label="考察费"><NInputNumber v-model:value="modalForm.inspection_fee" placeholder="考察费" style="width: 100%" /></NFormItem>
        <NFormItem label="备注"><NInput v-model:value="modalForm.remark" type="textarea" placeholder="备注" /></NFormItem>
      </NForm>
    </CrudModal>

    <!-- Detail modal -->
    <NModal v-model:show="showDetailModal" title="工单详情" preset="card" style="width: 800px; max-height: 85vh;" :body-style="{ overflow: 'auto' }">
      <template v-if="detailData">
        <NTabs v-model:value="detailTab">
          <NTabPane name="info" tab="基本信息">
            <NDescriptions bordered :column="2" label-placement="left" size="small">
              <NDescriptionsItem label="工单号">{{ detailData.ticket_no }}</NDescriptionsItem>
              <NDescriptionsItem label="状态">
                <NTag :type="statusColorMap[detailData.status]" size="small">{{ statusLabelMap[detailData.status] }}</NTag>
              </NDescriptionsItem>
              <NDescriptionsItem label="客户姓名">{{ detailData.customer_name }}</NDescriptionsItem>
              <NDescriptionsItem label="联系电话">{{ detailData.customer_phone }}</NDescriptionsItem>
              <NDescriptionsItem label="身份证号">{{ detailData.id_card || '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="申请金额">{{ detailData.apply_amount ? '¥' + detailData.apply_amount : '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="还款方式">{{ detailData.repayment_method || '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="考察费">{{ detailData.inspection_fee ? '¥' + detailData.inspection_fee : '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="业务员">{{ detailData.salesman || '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="详细地址" :span="2">{{ detailData.address || '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="提交人">{{ detailData.submitter_name }}</NDescriptionsItem>
              <NDescriptionsItem label="处理人">{{ detailData.assignee_name || '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="备注" :span="2">{{ detailData.remark || '-' }}</NDescriptionsItem>
              <NDescriptionsItem label="创建时间">{{ detailData.created_at }}</NDescriptionsItem>
              <NDescriptionsItem label="更新时间">{{ detailData.updated_at }}</NDescriptionsItem>
            </NDescriptions>
          </NTabPane>

          <NTabPane name="flow" tab="流转记录">
            <NTimeline>
              <NTimelineItem
                v-for="record in detailData.flow_records" :key="record.id"
                :type="record.action.includes('reject') ? 'error' : record.action.includes('approve') ? 'success' : 'info'"
                :title="(actionLabelMap[record.action] || record.action) + ' - ' + (record.operator_name || '')"
                :content="record.remark || ''"
                :time="record.created_at"
              />
            </NTimeline>
            <div v-if="!detailData.flow_records?.length" style="text-align:center;padding:20px;color:#999">暂无流转记录</div>
          </NTabPane>

          <NTabPane name="audit" tab="审核记录">
            <NTimeline>
              <NTimelineItem
                v-for="record in detailData.audit_records" :key="record.id"
                :type="record.result === 'approved' ? 'success' : 'error'"
                :title="(record.result === 'approved' ? '审核通过' : '审核驳回') + ' - ' + (record.reviewer_name || '')"
                :content="record.reject_reason || record.remark || ''"
                :time="record.created_at"
              />
            </NTimeline>
            <div v-if="!detailData.audit_records?.length" style="text-align:center;padding:20px;color:#999">暂无审核记录</div>
          </NTabPane>

          <NTabPane name="messages" tab="沟通记录">
            <div style="max-height: 300px; overflow-y: auto; padding: 10px 0;">
              <div v-for="msg in ticketMessages" :key="msg.id" style="margin-bottom: 12px; padding: 8px 12px; background: #f9f9f9; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #999;">
                  <span><b>{{ msg.sender_name }}</b> → {{ msg.receiver_name || '全部' }}</span>
                  <span>{{ msg.created_at }}</span>
                </div>
                <div style="margin-top: 4px;">
                  <NTag v-if="msg.msg_type !== 'text'" size="tiny" style="margin-right: 4px;">{{ msg.msg_type }}</NTag>
                  {{ msg.content || msg.file_url || '' }}
                </div>
              </div>
              <div v-if="!ticketMessages.length" style="text-align:center;padding:20px;color:#999">暂无沟通记录</div>
            </div>
            <NDivider style="margin: 8px 0" />
            <NSpace>
              <NInput v-model:value="msgContent" placeholder="输入消息..." style="width: 500px;"
                @keypress.enter="sendMsg" />
              <NButton type="primary" :loading="msgSending" @click="sendMsg">发送</NButton>
            </NSpace>
          </NTabPane>
        </NTabs>
      </template>
    </NModal>
  </CommonPage>
</template>
