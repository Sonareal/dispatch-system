<script setup>
import { h, onMounted, ref, watch } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSelect, NTree, NSpace, NCard, NTag, NPopover, NModal } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '行政区管理' })

const treeData = ref([])
const cityOptions = ref([])
const selectedCityId = ref(null)
const userOptions = ref([])
const userMap = ref({})

// Manager edit modal
const showManagerModal = ref(false)
const managerEditNode = ref(null)
const managerEditValues = ref([])
const managerSaving = ref(false)

const levelOptions = [
  { label: '省', value: 'province' },
  { label: '市', value: 'city' },
  { label: '区/县', value: 'district' },
  { label: '街道', value: 'street' },
]

const {
  modalVisible, modalTitle, modalLoading, handleSave, modalForm, modalFormRef,
  handleEdit, handleAdd,
} = useCRUD({
  name: '行政区', initForm: { parent_id: 0, level: 'province', city_id: null },
  doCreate: api.createRegion, doUpdate: api.updateRegion, doDelete: api.deleteRegion,
  refresh: () => loadTree(),
})

onMounted(() => {
  api.getCityList({ is_active: true }).then((res) => {
    cityOptions.value = (res.data || []).map((c) => ({ label: c.name, value: c.id }))
    if (cityOptions.value.length) selectedCityId.value = cityOptions.value[0].value
  })
  loadUsers()
})

function loadUsers() {
  api.getUserList({ page: 1, page_size: 999 }).then((res) => {
    const users = res.data || []
    userOptions.value = users.map((u) => ({
      label: `${u.alias || u.username}${u.phone ? ' (' + u.phone + ')' : ''}`,
      value: u.id,
    }))
    const map = {}
    users.forEach(u => { map[u.id] = u.alias || u.username })
    userMap.value = map
  })
}

watch(selectedCityId, () => loadTree())

async function loadTree() {
  if (!selectedCityId.value) { treeData.value = []; return }
  const res = await api.getRegionTree({ city_id: selectedCityId.value })
  treeData.value = res.data || []
}

function addChild(node) {
  handleAdd()
  modalForm.value.parent_id = node.id
  modalForm.value.city_id = selectedCityId.value
}

async function deleteRegion(node) {
  await api.deleteRegion({ region_id: node.id })
  window.$message?.success('删除成功')
  loadTree()
}

function editNode(node) {
  handleEdit(node)
}

function addRoot() {
  handleAdd()
  modalForm.value.parent_id = 0
  modalForm.value.city_id = selectedCityId.value
}

// Manager multi-select modal
function openManagerEdit(node) {
  managerEditNode.value = node
  managerEditValues.value = (node.managers || []).map(m => m.id)
  showManagerModal.value = true
}

async function saveManagers() {
  if (!managerEditNode.value) return
  managerSaving.value = true
  try {
    await api.setRegionManagers({ region_id: managerEditNode.value.id, user_ids: managerEditValues.value })
    window.$message?.success('负责人设置成功')
    showManagerModal.value = false
    loadTree()
  } catch (e) {
    window.$message?.error(e.message || '设置失败')
  } finally { managerSaving.value = false }
}

const renderSuffix = ({ option }) => {
  const managers = option.managers || []
  const MAX_SHOW = 2

  const managerTags = []
  if (managers.length > 0) {
    // Show first MAX_SHOW managers as tags
    const shown = managers.slice(0, MAX_SHOW)
    for (const m of shown) {
      managerTags.push(h(NTag, { type: 'success', size: 'tiny', style: 'margin-right:2px' }, { default: () => m.alias }))
    }
    // If more, show +N with popover
    if (managers.length > MAX_SHOW) {
      const remaining = managers.slice(MAX_SHOW)
      managerTags.push(
        h(NPopover, { trigger: 'hover' }, {
          trigger: () => h(NTag, { type: 'info', size: 'tiny', style: 'cursor:pointer' }, { default: () => `+${remaining.length}` }),
          default: () => h('div', { style: 'max-width:300px' },
            remaining.map(m => h(NTag, { type: 'success', size: 'small', style: 'margin:2px' }, { default: () => `${m.alias} ${m.phone || ''}` }))
          ),
        })
      )
    }
  }

  return h(NSpace, { size: 4, style: 'margin-left: 8px', align: 'center' }, {
    default: () => [
      ...managerTags,
      h(NButton, { size: 'tiny', quaternary: true, onClick: (e) => { e.stopPropagation(); openManagerEdit(option) } },
        { default: () => managers.length ? '改' : '设负责人', icon: () => renderIcon('mdi:account-multiple', { size: 14 })() }),
      h(NButton, { size: 'tiny', type: 'primary', quaternary: true, onClick: (e) => { e.stopPropagation(); editNode(option) } },
        { icon: () => renderIcon('mdi:pencil', { size: 14 })() }),
      h(NButton, { size: 'tiny', type: 'info', quaternary: true, onClick: (e) => { e.stopPropagation(); addChild(option) } },
        { icon: () => renderIcon('mdi:plus', { size: 14 })() }),
      h(NButton, { size: 'tiny', type: 'error', quaternary: true, onClick: (e) => { e.stopPropagation(); deleteRegion(option) } },
        { icon: () => renderIcon('mdi:delete', { size: 14 })() }),
    ]
  })
}
</script>

<template>
  <CommonPage show-footer title="行政区管理">
    <template #action>
      <NSpace>
        <NSelect v-model:value="selectedCityId" :options="cityOptions" placeholder="选择城市" style="width: 200px" />
        <NButton type="primary" @click="addRoot">
          <TheIcon icon="mdi:plus" :size="16" class="mr-5" />添加根节点
        </NButton>
      </NSpace>
    </template>

    <NCard>
      <NTree
        block-line :data="treeData" key-field="id" label-field="name"
        children-field="children" default-expand-all :render-suffix="renderSuffix"
      />
      <div v-if="!treeData.length" style="text-align: center; padding: 40px; color: #999;">
        暂无行政区数据，请先选择城市并添加
      </div>
    </NCard>

    <!-- Edit region form -->
    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
      <NForm ref="modalFormRef" label-placement="left" :label-width="80" :model="modalForm">
        <NFormItem label="名称" path="name"><NInput v-model:value="modalForm.name" placeholder="区域名称" /></NFormItem>
        <NFormItem label="编码" path="code"><NInput v-model:value="modalForm.code" placeholder="区域编码" /></NFormItem>
        <NFormItem label="层级" path="level"><NSelect v-model:value="modalForm.level" :options="levelOptions" /></NFormItem>
      </NForm>
    </CrudModal>

    <!-- Manager multi-select modal -->
    <NModal v-model:show="showManagerModal" title="设置区域负责人" preset="card" style="width: 500px">
      <div style="margin-bottom: 12px; color: #666;">
        为 <NTag type="info" size="small">{{ managerEditNode?.name }}</NTag> 设置负责人（可多选）
      </div>
      <NSelect
        v-model:value="managerEditValues"
        :options="userOptions"
        placeholder="选择负责人"
        multiple filterable clearable
      />
      <template #action>
        <NSpace justify="end">
          <NButton @click="showManagerModal = false">取消</NButton>
          <NButton type="primary" :loading="managerSaving" @click="saveManagers">保存</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
