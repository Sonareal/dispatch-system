<script setup>
import { h, onMounted, ref } from 'vue'
import {
  NButton, NTag, NSpace, NModal, NForm, NFormItem, NInput,
  NRadioGroup, NRadio, NDataTable, NDivider, NDescriptions, NDescriptionsItem,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import { renderIcon } from '@/utils'
import api from '@/api'

defineOptions({ name: '待审核工单' })

const $table = ref(null)
const queryItems = ref({})

// Audit modal state
const showAuditModal = ref(false)
const auditTicket = ref(null)
const auditResult = ref('approved')
const rejectReason = ref('')
const auditRemark = ref('')
const auditLoading = ref(false)
const assignableUsers = ref([])
const selectedAssigneeId = ref(null)

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  { title: '工单号', key: 'ticket_no', width: 160, ellipsis: { tooltip: true } },
  { title: '客户姓名', key: 'customer_name', width: 80, align: 'center' },
  { title: '联系电话', key: 'customer_phone', width: 100, align: 'center' },
  {
    title: '申请金额', key: 'apply_amount', width: 80, align: 'center',
    render(row) { return row.apply_amount ? `¥${row.apply_amount}` : '-' },
  },
  { title: '提交人', key: 'submitter_name', width: 80, align: 'center' },
  { title: '创建时间', key: 'created_at', width: 140, align: 'center' },
  {
    title: '操作', key: 'actions', width: 100, align: 'center', fixed: 'right',
    render(row) {
      return h(NButton, {
        size: 'small', type: 'warning',
        onClick: () => openAudit(row),
      }, { default: () => '审核', icon: () => renderIcon('mdi:clipboard-check-outline', { size: 14 })() })
    },
  },
]

async function openAudit(row) {
  auditTicket.value = row
  auditResult.value = 'approved'
  rejectReason.value = ''
  auditRemark.value = ''
  selectedAssigneeId.value = null

  try {
    const res = await api.getAssignableUsers({ ticket_id: row.id })
    assignableUsers.value = res.data || []
    const recommended = assignableUsers.value.find(u => u.recommended)
    if (recommended) selectedAssigneeId.value = recommended.id
  } catch (e) {
    assignableUsers.value = []
  }

  showAuditModal.value = true
}

const assignUserColumns = [
  {
    title: '选择', key: 'select', width: 50, align: 'center',
    render(row) {
      return h(NRadio, {
        checked: selectedAssigneeId.value === row.id,
        onUpdateChecked: () => { selectedAssigneeId.value = row.id },
      })
    }
  },
  {
    title: '姓名', key: 'alias', width: 100,
    render(row) {
      return h(NSpace, { size: 'small', align: 'center' }, {
        default: () => [
          row.alias,
          row.recommended ? h(NTag, { type: 'success', size: 'tiny' }, { default: () => '推荐' }) : null,
        ].filter(Boolean)
      })
    }
  },
  { title: '联系电话', key: 'phone', width: 100 },
  { title: '角色', key: 'roles', width: 100, render(row) { return (row.roles || []).join(', ') } },
  { title: '负责区域', key: 'regions', width: 120, render(row) { return (row.regions || []).join(', ') || '-' } },
  {
    title: '当前工单数', key: 'workload', width: 90, align: 'center',
    render(row) {
      const type = row.workload === 0 ? 'success' : row.workload <= 3 ? 'warning' : 'error'
      return h(NTag, { type, size: 'small' }, { default: () => `${row.workload} 单` })
    }
  },
  {
    title: '区域匹配', key: 'is_region_match', width: 80, align: 'center',
    render(row) {
      return row.is_exact_match
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => '精确' })
        : row.is_region_match
          ? h(NTag, { type: 'info', size: 'small' }, { default: () => '同城' })
          : h(NTag, { type: 'default', size: 'small' }, { default: () => '-' })
    }
  },
]

async function handleAudit() {
  if (auditResult.value === 'approved' && !selectedAssigneeId.value) {
    window.$message?.warning('审核通过时请选择指派人员')
    return
  }
  if (auditResult.value === 'rejected' && !rejectReason.value.trim()) {
    window.$message?.warning('驳回时必须填写驳回原因')
    return
  }

  auditLoading.value = true
  try {
    await api.auditTicket({
      ticket_id: auditTicket.value.id,
      result: auditResult.value,
      reject_reason: auditResult.value === 'rejected' ? rejectReason.value : '',
      assign_to_id: auditResult.value === 'approved' ? selectedAssigneeId.value : null,
      remark: auditRemark.value,
    })
    window.$message?.success(auditResult.value === 'approved' ? '审核通过并已指派' : '已驳回')
    showAuditModal.value = false
    $table.value?.handleSearch()
  } catch (e) {
    window.$message?.error(e.message || '审核失败')
  } finally {
    auditLoading.value = false
  }
}
</script>

<template>
  <CommonPage show-footer title="待审核工单">
    <CrudTable ref="$table" v-model:query-items="queryItems" :columns="columns" :get-data="api.getPendingReviewTickets">
      <template #queryBar>
        <QueryBarItem label="工单号" :label-width="50">
          <n-input v-model:value="queryItems.ticket_no" clearable placeholder="工单号"
            @keypress.enter="$table?.handleSearch()" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="showAuditModal" title="工单审核" preset="card"
      style="width: 900px; max-height: 85vh;" :body-style="{ overflow: 'auto' }">

      <template v-if="auditTicket">
        <NDescriptions bordered :column="3" label-placement="left" size="small" style="margin-bottom: 16px;">
          <NDescriptionsItem label="工单号">{{ auditTicket.ticket_no }}</NDescriptionsItem>
          <NDescriptionsItem label="客户姓名">{{ auditTicket.customer_name }}</NDescriptionsItem>
          <NDescriptionsItem label="联系电话">{{ auditTicket.customer_phone }}</NDescriptionsItem>
          <NDescriptionsItem label="申请金额">{{ auditTicket.apply_amount ? '¥' + auditTicket.apply_amount : '-' }}</NDescriptionsItem>
          <NDescriptionsItem label="提交人">{{ auditTicket.submitter_name }}</NDescriptionsItem>
          <NDescriptionsItem label="提交时间">{{ auditTicket.created_at }}</NDescriptionsItem>
        </NDescriptions>
      </template>

      <NDivider style="margin: 12px 0" />

      <NForm label-placement="left" :label-width="80">
        <NFormItem label="审核结果">
          <NRadioGroup v-model:value="auditResult">
            <NRadio value="approved">通过并指派</NRadio>
            <NRadio value="rejected">驳回</NRadio>
          </NRadioGroup>
        </NFormItem>
      </NForm>

      <template v-if="auditResult === 'rejected'">
        <NForm label-placement="left" :label-width="80">
          <NFormItem label="驳回原因" required>
            <NInput v-model:value="rejectReason" type="textarea" :rows="3" placeholder="请输入驳回原因（必填）" />
          </NFormItem>
          <NFormItem label="备注">
            <NInput v-model:value="auditRemark" type="textarea" :rows="2" placeholder="补充说明（选填）" />
          </NFormItem>
        </NForm>
      </template>

      <template v-else>
        <div style="margin-bottom: 12px; color: #666; font-size: 13px;">
          系统已根据工单所属区域自动匹配可用人员，并按工作负载排序。标记
          <NTag type="success" size="tiny">推荐</NTag> 的为区域匹配且负载最低的人员。
        </div>

        <NDataTable
          :columns="assignUserColumns" :data="assignableUsers" :row-key="(row) => row.id"
          :row-props="(row) => ({ style: { cursor: 'pointer', background: row.id === selectedAssigneeId ? '#e6f7ff' : '' }, onClick: () => { selectedAssigneeId = row.id } })"
          size="small" :bordered="true" :max-height="280"
        />

        <div v-if="!assignableUsers.length" style="text-align: center; padding: 20px; color: #999;">
          暂无可指派人员，请先在用户管理中设置区域负责人
        </div>

        <NDivider style="margin: 12px 0" />
        <NForm label-placement="left" :label-width="80">
          <NFormItem label="备注">
            <NInput v-model:value="auditRemark" type="textarea" :rows="2" placeholder="备注说明（选填）" />
          </NFormItem>
        </NForm>
      </template>

      <template #action>
        <NSpace justify="end">
          <NButton @click="showAuditModal = false">取消</NButton>
          <NButton :type="auditResult === 'rejected' ? 'error' : 'primary'" :loading="auditLoading" @click="handleAudit">
            {{ auditResult === 'rejected' ? '确认驳回' : '确认通过并指派' }}
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>

<style scoped>
:deep(.n-data-table-tr:hover td) {
  background-color: #f5f5f5 !important;
}
</style>
