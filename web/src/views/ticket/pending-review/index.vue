<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NTag, NSpace, NModal, NForm, NFormItem, NInput, NRadioGroup, NRadio, NSelect } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import api from '@/api'

defineOptions({ name: '待审核工单' })

const $table = ref(null)
const queryItems = ref({})
const showAuditModal = ref(false)
const auditForm = ref({ ticket_id: null, result: 'approved', reject_reason: '', remark: '', assign_to_id: null })
const auditLoading = ref(false)
const userOptions = ref([])

onMounted(() => {
  $table.value?.handleSearch()
  api.getUserList({ page: 1, page_size: 999 }).then((res) => {
    userOptions.value = (res.data || []).map((u) => ({ label: u.alias || u.username, value: u.id }))
  })
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

function openAudit(row) {
  auditForm.value = { ticket_id: row.id, result: 'approved', reject_reason: '', remark: '', assign_to_id: null }
  showAuditModal.value = true
}

async function handleAudit() {
  auditLoading.value = true
  try {
    await api.auditTicket(auditForm.value)
    window.$message?.success('审核完成')
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
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getPendingReviewTickets"
    />

    <NModal v-model:show="showAuditModal" title="工单审核" preset="card" style="width: 500px">
      <NForm :model="auditForm" label-placement="left" :label-width="80">
        <NFormItem label="审核结果">
          <NRadioGroup v-model:value="auditForm.result">
            <NRadio value="approved">通过</NRadio>
            <NRadio value="rejected">驳回</NRadio>
          </NRadioGroup>
        </NFormItem>
        <NFormItem v-if="auditForm.result === 'rejected'" label="驳回原因">
          <NInput v-model:value="auditForm.reject_reason" type="textarea" placeholder="请输入驳回原因" />
        </NFormItem>
        <NFormItem v-if="auditForm.result === 'approved'" label="指派给">
          <NSelect v-model:value="auditForm.assign_to_id" :options="userOptions" placeholder="选择处理人(可选)" clearable />
        </NFormItem>
        <NFormItem label="备注">
          <NInput v-model:value="auditForm.remark" type="textarea" placeholder="备注" />
        </NFormItem>
      </NForm>
      <template #action>
        <NSpace justify="end">
          <NButton @click="showAuditModal = false">取消</NButton>
          <NButton type="primary" :loading="auditLoading" @click="handleAudit">确认</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
