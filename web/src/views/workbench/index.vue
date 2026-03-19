<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <n-avatar :size="60" round>
              <TheIcon icon="mdi:account-circle" :size="40" />
            </n-avatar>
            <div ml-10>
              <p text-20 font-semibold>你好，{{ userStore.name }}</p>
              <p mt-5 text-14 op-60>欢迎使用派单管理系统</p>
            </div>
          </div>
          <n-space :size="20" :wrap="false">
            <n-statistic label="待审核" :value="stats.pending_review" />
            <n-statistic label="处理中" :value="stats.processing" />
            <n-statistic label="已完成" :value="stats.completed" />
            <n-statistic label="工单总数" :value="stats.total" />
          </n-space>
        </div>
      </n-card>

      <n-grid :cols="4" :x-gap="15" :y-gap="15" mt-15>
        <n-gi>
          <n-card hoverable class="cursor-pointer" @click="$router.push('/ticket/pending-review')">
            <div flex items-center>
              <n-avatar :size="48" round color="#f0a020">
                <TheIcon icon="mdi:file-document-edit-outline" :size="28" color="#fff" />
              </n-avatar>
              <div ml-15>
                <p text-14 op-60>待审核工单</p>
                <p text-24 font-bold>{{ stats.pending_review }}</p>
              </div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card hoverable class="cursor-pointer" @click="$router.push('/ticket/my-assigned')">
            <div flex items-center>
              <n-avatar :size="48" round color="#2080f0">
                <TheIcon icon="mdi:account-hard-hat" :size="28" color="#fff" />
              </n-avatar>
              <div ml-15>
                <p text-14 op-60>我负责的</p>
                <p text-24 font-bold>{{ stats.assigned }}</p>
              </div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card hoverable class="cursor-pointer" @click="$router.push('/ticket/list')">
            <div flex items-center>
              <n-avatar :size="48" round color="#18a058">
                <TheIcon icon="mdi:check-circle-outline" :size="28" color="#fff" />
              </n-avatar>
              <div ml-15>
                <p text-14 op-60>已完成</p>
                <p text-24 font-bold>{{ stats.completed }}</p>
              </div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card hoverable class="cursor-pointer" @click="$router.push('/ticket/list')">
            <div flex items-center>
              <n-avatar :size="48" round color="#d03050">
                <TheIcon icon="mdi:close-circle-outline" :size="28" color="#fff" />
              </n-avatar>
              <div ml-15>
                <p text-14 op-60>已驳回</p>
                <p text-24 font-bold>{{ stats.rejected }}</p>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>

      <n-card title="快捷操作" mt-15 rounded-10>
        <n-space>
          <n-button type="primary" @click="$router.push('/ticket/list')">
            <TheIcon icon="mdi:plus" :size="16" class="mr-5" />新建工单
          </n-button>
          <n-button @click="$router.push('/ticket/pending-review')">
            <TheIcon icon="mdi:file-document-edit-outline" :size="16" class="mr-5" />审核工单
          </n-button>
          <n-button @click="$router.push('/communication/messages')">
            <TheIcon icon="mdi:message-outline" :size="16" class="mr-5" />消息中心
          </n-button>
        </n-space>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useUserStore } from '@/store'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

const userStore = useUserStore()
const stats = ref({ total: 0, pending_review: 0, processing: 0, completed: 0, rejected: 0, assigned: 0 })

onMounted(async () => {
  try {
    const res = await api.getTicketStatistics()
    stats.value = res.data || stats.value
  } catch (e) {
    console.error(e)
  }
})
</script>
