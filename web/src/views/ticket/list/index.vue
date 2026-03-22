<script setup>
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton, NForm, NFormItem, NInput, NInputNumber, NSelect, NTag, NSpace,
  NModal, NDescriptions, NDescriptionsItem, NTimeline, NTimelineItem,
  NUpload, NCascader, NTabPane, NTabs, NDivider, NDataTable, NRadioGroup, NRadio,
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

const { t } = useI18n({ useScope: 'global' })
const userStore = useUserStore()

defineOptions({ name: '工单列表' })

const $table = ref(null)
const queryItems = ref({})

const statusOptions = computed(() => [
  { label: t('views.ticket.status_all'), value: '' },
  { label: t('views.ticket.status_draft'), value: 'draft' },
  { label: t('views.ticket.status_pending_review'), value: 'pending_review' },
  { label: t('views.ticket.status_approved'), value: 'approved' },
  { label: t('views.ticket.status_rejected'), value: 'rejected' },
  { label: t('views.ticket.status_pending_assign'), value: 'pending_assign' },
  { label: t('views.ticket.status_assigned'), value: 'assigned' },
  { label: t('views.ticket.status_processing'), value: 'processing' },
  { label: t('views.ticket.status_transferred'), value: 'transferred' },
  { label: t('views.ticket.status_completed'), value: 'completed' },
  { label: t('views.ticket.status_closed'), value: 'closed' },
])

const statusColorMap = {
  draft: 'default', pending_review: 'warning', approved: 'info', rejected: 'error',
  pending_assign: 'warning', assigned: 'info', processing: 'success',
  transferred: 'info', completed: 'success', closed: 'default',
}

const statusLabelMap = computed(() => ({
  draft: t('views.ticket.status_draft'),
  pending_review: t('views.ticket.status_pending_review'),
  approved: t('views.ticket.status_approved'),
  rejected: t('views.ticket.status_rejected'),
  pending_assign: t('views.ticket.status_pending_assign'),
  assigned: t('views.ticket.status_assigned'),
  processing: t('views.ticket.status_processing'),
  transferred: t('views.ticket.status_transferred'),
  completed: t('views.ticket.status_completed'),
  closed: t('views.ticket.status_closed'),
}))

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
const voiceUploading = ref(false)

// Assign modal
const showAssignModal = ref(false)
const assignAction = ref('') // 'audit_approve', 'audit_reject', 'assign', 'transfer'
const assignableUsers = ref([])
const selectedAssigneeId = ref(null)
const assignRemark = ref('')
const rejectReason = ref('')
const assignLoading = ref(false)

const {
  modalVisible, modalTitle, modalAction, modalLoading, handleSave, modalForm, modalFormRef, handleAdd,
} = useCRUD({
  name: '工单', initForm: {
    city_id: null, region_id: null,
    salesman: (() => {
      const u = userStore.userInfo
      if (!u) return ''
      if (u.alias && u.alias !== u.username) return `${u.alias}(${u.username})`
      return u.username || ''
    })(),
  },
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

const columns = computed(() => [
  { title: t('views.ticket.label_ticket_no'), key: 'ticket_no', width: 160, ellipsis: { tooltip: true } },
  { title: t('views.ticket.label_customer_name'), key: 'customer_name', width: 80, align: 'center' },
  { title: t('views.ticket.label_customer_phone'), key: 'customer_phone', width: 100, align: 'center' },
  {
    title: t('views.ticket.label_apply_amount'), key: 'apply_amount', width: 80, align: 'center',
    render(row) { return row.apply_amount ? `¥${row.apply_amount}` : '-' },
  },
  {
    title: t('views.ticket.label_status'), key: 'status', width: 80, align: 'center',
    render(row) {
      return h(NTag, { type: statusColorMap[row.status] || 'default', size: 'small' },
        { default: () => statusLabelMap.value[row.status] || row.status })
    },
  },
  { title: t('views.ticket.label_submitter'), key: 'submitter_name', width: 80, align: 'center' },
  { title: t('views.ticket.label_assignee'), key: 'assignee_name', width: 80, align: 'center' },
  { title: t('views.ticket.label_created_at'), key: 'created_at', width: 140, align: 'center' },
  {
    title: t('views.ticket.label_actions'), key: 'actions', width: 120, align: 'center', fixed: 'right',
    render(row) {
      return h(NSpace, { justify: 'center', size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', type: 'primary', onClick: () => viewDetail(row.id) },
            { default: () => t('views.ticket.label_detail') }),
        ]
      })
    },
  },
])

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
    window.$message?.success(t('views.ticket.message_send_success'))
  } catch (e) {
    window.$message?.error(t('views.ticket.message_send_failed'))
  } finally { msgSending.value = false }
}

function handleVoiceUpload({ file }) {
  if (!detailData.value) return false
  voiceUploading.value = true
  const formData = new FormData()
  formData.append('file', file.file)
  formData.append('ticket_id', detailData.value.id)
  formData.append('receiver_id', detailData.value.assignee_id || detailData.value.submitter_id || '')
  api.uploadVoiceMessage(formData).then(() => {
    loadMessages(detailData.value.id)
    window.$message?.success(t('views.ticket.voice_upload_success'))
  }).catch(() => {
    window.$message?.error(t('views.ticket.voice_upload_failed'))
  }).finally(() => {
    voiceUploading.value = false
  })
  return false // prevent default upload behavior
}

// ========== Assign / Audit actions ==========

async function openAssignModal(action) {
  assignAction.value = action
  assignRemark.value = ''
  rejectReason.value = ''
  selectedAssigneeId.value = null
  assignLoading.value = false

  if (action !== 'audit_reject') {
    // Load assignable users with workload
    try {
      const res = await api.getAssignableUsers({ ticket_id: detailData.value.id })
      assignableUsers.value = res.data || []
      // Auto-select the recommended user
      const recommended = assignableUsers.value.find(u => u.recommended)
      if (recommended) {
        selectedAssigneeId.value = recommended.id
      }
    } catch (e) {
      assignableUsers.value = []
    }
  }

  showAssignModal.value = true
}

const assignUserColumns = computed(() => [
  {
    title: t('views.ticket.assign_select_column'), key: 'select', width: 50, align: 'center',
    render(row) {
      return h(NRadio, {
        checked: selectedAssigneeId.value === row.id,
        onUpdateChecked: () => { selectedAssigneeId.value = row.id },
      })
    }
  },
  {
    title: t('views.ticket.assign_name_column'), key: 'alias', width: 100,
    render(row) {
      return h(NSpace, { size: 'small', align: 'center' }, {
        default: () => [
          row.alias,
          row.recommended ? h(NTag, { type: 'success', size: 'tiny' }, { default: () => t('views.audit.label_recommended') }) : null,
        ].filter(Boolean)
      })
    }
  },
  { title: t('views.ticket.assign_phone_column'), key: 'phone', width: 100 },
  {
    title: t('views.ticket.assign_role_column'), key: 'roles', width: 100,
    render(row) { return (row.roles || []).join(', ') }
  },
  {
    title: t('views.ticket.assign_region_column'), key: 'regions', width: 120,
    render(row) { return (row.regions || []).join(', ') || '-' }
  },
  {
    title: t('views.ticket.assign_workload_column'), key: 'workload', width: 90, align: 'center',
    render(row) {
      const type = row.workload === 0 ? 'success' : row.workload <= 3 ? 'warning' : 'error'
      return h(NTag, { type, size: 'small' }, { default: () => t('views.ticket.assign_workload_unit', { count: row.workload }) })
    }
  },
  {
    title: t('views.ticket.assign_match_column'), key: 'match_label', width: 80, align: 'center',
    render(row) {
      if (row.is_exact_match) return h(NTag, { type: 'success', size: 'small' }, { default: () => t('views.ticket.assign_exact_match') })
      if (row.is_region_match) return h(NTag, { type: 'info', size: 'small' }, { default: () => t('views.ticket.assign_city_match') })
      if (row.match_label) return h(NTag, { type: 'default', size: 'small' }, { default: () => row.match_label })
      return '-'
    }
  },
])

async function confirmAssign() {
  const action = assignAction.value
  const ticketId = detailData.value.id
  assignLoading.value = true

  try {
    if (action === 'audit_approve') {
      if (!selectedAssigneeId.value) {
        window.$message?.warning(t('views.ticket.message_select_assignee'))
        assignLoading.value = false
        return
      }
      await api.auditTicket({
        ticket_id: ticketId,
        result: 'approved',
        assign_to_id: selectedAssigneeId.value,
        remark: assignRemark.value,
      })
      window.$message?.success(t('views.ticket.message_approved_assigned'))
    } else if (action === 'audit_reject') {
      if (!rejectReason.value.trim()) {
        window.$message?.warning(t('views.ticket.message_input_reject_reason'))
        assignLoading.value = false
        return
      }
      await api.auditTicket({
        ticket_id: ticketId,
        result: 'rejected',
        reject_reason: rejectReason.value,
        remark: assignRemark.value,
      })
      window.$message?.success(t('views.ticket.message_rejected'))
    } else if (action === 'assign') {
      if (!selectedAssigneeId.value) {
        window.$message?.warning(t('views.ticket.message_select_assignee'))
        assignLoading.value = false
        return
      }
      await api.assignTicket({
        ticket_id: ticketId,
        assignee_id: selectedAssigneeId.value,
        remark: assignRemark.value,
      })
      window.$message?.success(t('views.ticket.message_assigned_success'))
    } else if (action === 'transfer') {
      if (!selectedAssigneeId.value) {
        window.$message?.warning(t('views.ticket.message_select_transfer'))
        assignLoading.value = false
        return
      }
      await api.transferTicket({
        ticket_id: ticketId,
        transfer_to_id: selectedAssigneeId.value,
        reason: assignRemark.value,
      })
      window.$message?.success(t('views.ticket.message_transferred_success'))
    }

    showAssignModal.value = false
    // Refresh detail
    await viewDetail(ticketId)
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || t('common.text.operation_failed'))
  } finally {
    assignLoading.value = false
  }
}

async function quickUpdateStatus(status) {
  const ticketId = detailData.value.id
  try {
    await api.updateTicketStatus({ ticket_id: ticketId, status, remark: '' })
    window.$message?.success(t('views.ticket.message_status_updated'))
    await viewDetail(ticketId)
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || t('common.text.operation_failed'))
  }
}

async function submitTicket() {
  const ticketId = detailData.value.id
  try {
    await api.submitTicket({ ticket_id: ticketId })
    window.$message?.success(t('views.ticket.message_submitted_review'))
    await viewDetail(ticketId)
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || t('views.ticket.message_submit_failed'))
  }
}

async function withdrawTicket() {
  const ticketId = detailData.value.id
  try {
    await api.withdrawTicket({ ticket_id: ticketId })
    window.$message?.success(t('views.ticket.message_withdrawn'))
    await viewDetail(ticketId)
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || t('views.ticket.message_withdraw_failed'))
  }
}

async function revertToReview() {
  const ticketId = detailData.value.id
  try {
    await api.revertToReview({ ticket_id: ticketId, remark: t('views.ticket.message_revert_remark') })
    window.$message?.success(t('views.ticket.message_reverted_review'))
    await viewDetail(ticketId)
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || t('common.text.operation_failed'))
  }
}

function editDraftTicket() {
  // Open the create modal with the ticket data prefilled for editing
  const d = detailData.value
  modalForm.value = {
    id: d.id, customer_name: d.customer_name, customer_phone: d.customer_phone,
    id_card: d.id_card, apply_amount: d.apply_amount ? Number(d.apply_amount) : null,
    repayment_method: d.repayment_method, address: d.address,
    city_id: d.city_id, region_id: d.region_id,
    salesman: d.salesman, inspection_fee: d.inspection_fee ? Number(d.inspection_fee) : null,
    remark: d.remark,
  }
  showDetailModal.value = false
  modalVisible.value = true
  // trigger region load
  if (d.city_id) {
    api.getRegionTree({ city_id: d.city_id }).then(res => {
      regionOptions.value = buildCascaderOptions(res.data || [])
    })
  }
}

const actionLabelMap = computed(() => ({
  create: t('views.ticket.action_label_create'),
  submit: t('views.ticket.action_label_submit'),
  withdraw: t('views.ticket.action_label_withdraw'),
  review_approve: t('views.ticket.action_label_review_approve'),
  review_reject: t('views.ticket.action_label_review_reject'),
  assign: t('views.ticket.action_label_assign'),
  transfer: t('views.ticket.action_label_transfer'),
  start_process: t('views.ticket.action_label_start_process'),
  complete: t('views.ticket.action_label_complete'),
  close: t('views.ticket.action_label_close'),
  resubmit: t('views.ticket.action_label_resubmit'),
}))

const assignModalTitle = computed(() => ({
  audit_approve: t('views.ticket.assign_modal_approve'),
  audit_reject: t('views.ticket.assign_modal_reject'),
  assign: t('views.ticket.assign_modal_assign'),
  transfer: t('views.ticket.assign_modal_transfer'),
}))

const validateForm = computed(() => ({
  customer_name: [{ required: true, message: t('views.ticket.validate_customer_name'), trigger: 'blur' }],
  customer_phone: [{ required: true, message: t('views.ticket.validate_customer_phone'), trigger: 'blur' }],
  city_id: [{ required: true, type: 'number', message: t('views.ticket.validate_city'), trigger: 'change' }],
}))
</script>

<template>
  <CommonPage show-footer :title="t('views.ticket.label_ticket_list')">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <template #icon><TheIcon icon="mdi:plus" :size="16" /></template>
        {{ t('views.ticket.label_create_ticket') }}
      </NButton>
    </template>

    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getTicketList">
      <template #queryBar>
        <QueryBarItem :label="t('views.ticket.label_ticket_no')" :label-width="50">
          <NInput v-model:value="queryItems.ticket_no" clearable :placeholder="t('views.ticket.label_ticket_no')"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem :label="t('views.ticket.label_customer_name')" :label-width="65">
          <NInput v-model:value="queryItems.customer_name" clearable :placeholder="t('views.ticket.label_customer_name')"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem :label="t('views.ticket.label_status')" :label-width="35">
          <NSelect v-model:value="queryItems.status" :options="statusOptions" clearable
            style="width: 120px" @update:value="$table?.handleSearch()" />
        </QueryBarItem>
        <QueryBarItem :label="t('views.ticket.label_city')" :label-width="35">
          <NSelect v-model:value="queryItems.city_id" :options="cityOptions" clearable
            style="width: 120px" @update:value="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- Create ticket modal -->
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" label-align="left" :label-width="80"
        :model="modalForm" :rules="validateForm">
        <NFormItem :label="t('views.ticket.label_customer_name')" path="customer_name">
          <NInput v-model:value="modalForm.customer_name" :placeholder="t('views.ticket.placeholder_customer_name')" />
        </NFormItem>
        <NFormItem :label="t('views.ticket.label_customer_phone')" path="customer_phone">
          <NInput v-model:value="modalForm.customer_phone" :placeholder="t('views.ticket.placeholder_customer_phone')" />
        </NFormItem>
        <NFormItem :label="t('views.ticket.label_id_card')"><NInput v-model:value="modalForm.id_card" :placeholder="t('views.ticket.placeholder_id_card')" /></NFormItem>
        <NFormItem :label="t('views.ticket.label_apply_amount')"><NInputNumber v-model:value="modalForm.apply_amount" :placeholder="t('views.ticket.placeholder_apply_amount')" style="width: 100%" /></NFormItem>
        <NFormItem :label="t('views.ticket.label_repayment_method')"><NInput v-model:value="modalForm.repayment_method" :placeholder="t('views.ticket.placeholder_repayment_method')" /></NFormItem>
        <NFormItem :label="t('views.ticket.label_address')"><NInput v-model:value="modalForm.address" :placeholder="t('views.ticket.placeholder_address')" type="textarea" /></NFormItem>
        <NFormItem :label="t('views.ticket.label_city')" path="city_id">
          <NSelect v-model:value="modalForm.city_id" :options="cityOptions" :placeholder="t('views.ticket.placeholder_city')" />
        </NFormItem>
        <NFormItem :label="t('views.ticket.label_region')">
          <NCascader v-model:value="modalForm.region_id" :options="regionOptions" :placeholder="t('views.ticket.placeholder_region')"
            clearable check-strategy="child" :show-path="true" />
        </NFormItem>
        <NFormItem :label="t('views.ticket.label_salesman')"><NInput v-model:value="modalForm.salesman" :placeholder="t('views.ticket.placeholder_salesman')" /></NFormItem>
        <NFormItem :label="t('views.ticket.label_inspection_fee')"><NInputNumber v-model:value="modalForm.inspection_fee" :placeholder="t('views.ticket.placeholder_inspection_fee')" style="width: 100%" /></NFormItem>
        <NFormItem :label="t('views.ticket.label_remark')"><NInput v-model:value="modalForm.remark" type="textarea" :placeholder="t('views.ticket.placeholder_remark')" /></NFormItem>
      </NForm>
    </CrudModal>

    <!-- Detail modal -->
    <NModal v-model:show="showDetailModal" :title="t('views.ticket.label_ticket_detail')" preset="card" style="width: 900px; max-height: 85vh;" :body-style="{ overflow: 'auto' }">
      <template v-if="detailData">
        <NTabs v-model:value="detailTab">
          <NTabPane name="info" :tab="t('views.ticket.tab_basic_info')">
            <NDescriptions bordered :column="2" label-placement="left" size="small">
              <NDescriptionsItem :label="t('views.ticket.label_ticket_no')">{{ detailData.ticket_no }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_status')">
                <NTag :type="statusColorMap[detailData.status]" size="small">{{ statusLabelMap[detailData.status] }}</NTag>
              </NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_customer_name')">{{ detailData.customer_name }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_customer_phone')">{{ detailData.customer_phone }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_id_card')">{{ detailData.id_card || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_apply_amount')">{{ detailData.apply_amount ? '¥' + detailData.apply_amount : '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_repayment_method')">{{ detailData.repayment_method || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_inspection_fee')">{{ detailData.inspection_fee ? '¥' + detailData.inspection_fee : '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_salesman')">{{ detailData.salesman || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_city_name')">{{ detailData.city_name || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_region_name')" :span="2">{{ detailData.region_path || detailData.region_name || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_address')" :span="2">{{ detailData.address || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_submitter')">{{ detailData.submitter_name }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_assignee')">{{ detailData.assignee_name || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_remark')" :span="2">{{ detailData.remark || '-' }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_created_at')">{{ detailData.created_at }}</NDescriptionsItem>
              <NDescriptionsItem :label="t('views.ticket.label_updated_at')">{{ detailData.updated_at }}</NDescriptionsItem>
            </NDescriptions>

            <!-- Action buttons based on status -->
            <NDivider style="margin: 12px 0" />
            <NSpace>
              <template v-if="detailData.status === 'draft'">
                <NButton type="warning" @click="editDraftTicket">{{ t('views.ticket.action_edit') }}</NButton>
                <NButton type="primary" @click="submitTicket">{{ t('views.ticket.action_submit_audit') }}</NButton>
              </template>
              <template v-if="detailData.status === 'pending_review'">
                <NButton @click="withdrawTicket">{{ t('views.ticket.action_withdraw') }}</NButton>
                <NButton type="success" @click="openAssignModal('audit_approve')">{{ t('views.ticket.action_approve_and_assign') }}</NButton>
                <NButton type="error" @click="openAssignModal('audit_reject')">{{ t('views.ticket.action_reject_ticket') }}</NButton>
              </template>
              <template v-if="detailData.status === 'rejected'">
                <NButton type="warning" @click="editDraftTicket">{{ t('views.ticket.action_modify_ticket') }}</NButton>
                <NButton type="primary" @click="submitTicket">{{ t('views.ticket.action_resubmit_audit') }}</NButton>
              </template>
              <template v-if="['approved', 'pending_assign'].includes(detailData.status)">
                <NButton type="primary" @click="openAssignModal('assign')">{{ t('views.ticket.action_assign') }}</NButton>
              </template>
              <template v-if="['assigned'].includes(detailData.status)">
                <NButton type="info" @click="quickUpdateStatus('processing')">{{ t('views.ticket.action_start_processing') }}</NButton>
                <NButton @click="openAssignModal('transfer')">{{ t('views.ticket.action_transfer') }}</NButton>
                <NButton type="warning" @click="openAssignModal('assign')">{{ t('views.ticket.action_reassign') }}</NButton>
              </template>
              <template v-if="['processing'].includes(detailData.status)">
                <NButton type="success" @click="quickUpdateStatus('completed')">{{ t('views.ticket.action_complete') }}</NButton>
                <NButton @click="openAssignModal('transfer')">{{ t('views.ticket.action_transfer') }}</NButton>
              </template>
              <template v-if="['transferred'].includes(detailData.status)">
                <NButton type="info" @click="quickUpdateStatus('processing')">{{ t('views.ticket.action_start_processing') }}</NButton>
                <NButton type="success" @click="quickUpdateStatus('completed')">{{ t('views.ticket.action_complete') }}</NButton>
                <NButton @click="openAssignModal('transfer')">{{ t('views.ticket.action_transfer_again') }}</NButton>
              </template>
              <template v-if="['completed'].includes(detailData.status)">
                <NButton type="warning" @click="revertToReview">{{ t('views.ticket.action_revert_review') }}</NButton>
              </template>
            </NSpace>
          </NTabPane>

          <NTabPane name="flow" :tab="t('views.ticket.tab_flow_records')">
            <NTimeline>
              <NTimelineItem
                v-for="record in detailData.flow_records" :key="record.id"
                :type="record.action.includes('reject') ? 'error' : record.action.includes('approve') ? 'success' : 'info'"
                :title="(actionLabelMap[record.action] || record.action) + ' - ' + (record.operator_name || '')"
                :content="record.remark || ''"
                :time="record.created_at"
              />
            </NTimeline>
            <div v-if="!detailData.flow_records?.length" style="text-align:center;padding:20px;color:#999">{{ t('views.ticket.no_flow_records') }}</div>
          </NTabPane>

          <NTabPane name="audit" :tab="t('views.ticket.tab_audit_records')">
            <NTimeline>
              <NTimelineItem
                v-for="record in detailData.audit_records" :key="record.id"
                :type="record.result === 'approved' ? 'success' : 'error'"
                :title="(record.result === 'approved' ? t('views.ticket.action_label_review_approve') : t('views.ticket.action_label_review_reject')) + ' - ' + (record.reviewer_name || '')"
                :content="record.reject_reason || record.remark || ''"
                :time="record.created_at"
              />
            </NTimeline>
            <div v-if="!detailData.audit_records?.length" style="text-align:center;padding:20px;color:#999">{{ t('views.ticket.no_audit_records') }}</div>
          </NTabPane>

          <NTabPane name="messages" :tab="t('views.ticket.tab_messages')">
            <div style="max-height: 300px; overflow-y: auto; padding: 10px 0;">
              <div v-for="msg in ticketMessages" :key="msg.id" style="margin-bottom: 12px; padding: 8px 12px; background: #f9f9f9; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #999;">
                  <span><b>{{ msg.sender_name }}</b> → {{ msg.receiver_name || t('views.ticket.receiver_all') }}</span>
                  <span>{{ msg.created_at }}</span>
                </div>
                <div style="margin-top: 4px;">
                  <!-- Voice message -->
                  <template v-if="msg.msg_type === 'voice'">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <NTag size="tiny" type="info">{{ t('views.ticket.label_voice_message') }}</NTag>
                      <audio controls preload="metadata" style="height: 32px; max-width: 260px;">
                        <source :src="msg.file_url" />
                      </audio>
                      <span v-if="msg.voice_duration" style="font-size: 12px; color: #999;">{{ msg.voice_duration }}s</span>
                    </div>
                  </template>
                  <!-- Image message -->
                  <template v-else-if="msg.msg_type === 'image'">
                    <NTag size="tiny" type="warning" style="margin-right: 4px;">{{ t('views.ticket.label_image_message') }}</NTag>
                    <a :href="msg.file_url" target="_blank"><img :src="msg.file_url" style="max-width: 240px; max-height: 180px; border-radius: 4px; margin-top: 4px; cursor: pointer; display: block;" /></a>
                  </template>
                  <!-- Text / system / other -->
                  <template v-else>
                    <NTag v-if="msg.msg_type !== 'text'" size="tiny" style="margin-right: 4px;">{{ msg.msg_type }}</NTag>
                    {{ msg.content || msg.file_url || '' }}
                  </template>
                </div>
              </div>
              <div v-if="!ticketMessages.length" style="text-align:center;padding:20px;color:#999">{{ t('views.ticket.no_messages') }}</div>
            </div>
            <NDivider style="margin: 8px 0" />
            <NSpace align="center">
              <NInput v-model:value="msgContent" :placeholder="t('views.ticket.placeholder_message')" style="width: 440px;"
                @keypress.enter="sendMsg" />
              <NButton type="primary" :loading="msgSending" @click="sendMsg">{{ t('views.ticket.action_send') }}</NButton>
              <NUpload
                :show-file-list="false"
                accept=".mp3,.wav,.amr,.m4a,audio/*"
                :custom-request="handleVoiceUpload"
              >
                <NButton :loading="voiceUploading" type="info" secondary>
                  <template #icon><TheIcon icon="mdi:microphone" :size="16" /></template>
                  {{ t('views.ticket.action_send_voice') }}
                </NButton>
              </NUpload>
            </NSpace>
          </NTabPane>
        </NTabs>
      </template>
    </NModal>

    <!-- Assign modal with user selection -->
    <NModal v-model:show="showAssignModal" :title="assignModalTitle[assignAction] || t('views.ticket.assign_modal_default')" preset="card"
      style="width: 900px; max-height: 80vh;" :body-style="{ overflow: 'auto' }">

      <!-- Reject only needs reason -->
      <template v-if="assignAction === 'audit_reject'">
        <NForm label-placement="left" :label-width="80">
          <NFormItem :label="t('views.ticket.label_reject_reason')" required>
            <NInput v-model:value="rejectReason" type="textarea" :rows="3" :placeholder="t('views.ticket.placeholder_reject_reason')" />
          </NFormItem>
          <NFormItem :label="t('views.ticket.label_remark')">
            <NInput v-model:value="assignRemark" type="textarea" :rows="2" :placeholder="t('views.ticket.placeholder_remark_optional')" />
          </NFormItem>
        </NForm>
      </template>

      <!-- Assign/Approve/Transfer needs user selection -->
      <template v-else>
        <div style="margin-bottom: 12px; color: #666; font-size: 13px;">
          {{ t('views.ticket.assign_hint') }} <NTag type="success" size="tiny">{{ t('views.audit.label_recommended') }}</NTag> {{ t('views.ticket.assign_hint_recommended') }}
        </div>

        <NDataTable
          :columns="assignUserColumns"
          :data="assignableUsers"
          :row-key="(row) => row.id"
          :row-class-name="(row) => row.id === selectedAssigneeId ? 'selected-row' : ''"
          :row-props="(row) => ({ style: { cursor: 'pointer' }, onClick: () => { selectedAssigneeId = row.id } })"
          size="small"
          :bordered="true"
          :max-height="300"
        />

        <div v-if="!assignableUsers.length" style="text-align: center; padding: 20px; color: #999;">
          {{ t('views.ticket.assign_no_users') }}
        </div>

        <NDivider style="margin: 12px 0" />
        <NForm label-placement="left" :label-width="80">
          <NFormItem :label="t('views.ticket.label_remark')">
            <NInput v-model:value="assignRemark" type="textarea" :rows="2" :placeholder="t('views.ticket.placeholder_remark_assign')" />
          </NFormItem>
        </NForm>
      </template>

      <template #action>
        <NSpace justify="end">
          <NButton @click="showAssignModal = false">{{ t('common.buttons.cancel') }}</NButton>
          <NButton type="primary" :loading="assignLoading" @click="confirmAssign">
            {{ assignAction === 'audit_reject' ? t('views.ticket.confirm_reject') : t('common.buttons.confirm') }}
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>

<style scoped>
:deep(.selected-row td) {
  background-color: #e6f7ff !important;
}
</style>
