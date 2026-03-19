<template>
  <router-link h-60 f-c-c to="/">
    <icon-custom-logo text-36 color-primary></icon-custom-logo>
    <h2
      v-show="!appStore.collapsed"
      ml-2
      mr-8
      max-w-150
      flex-shrink-0
      text-16
      font-bold
      color-primary
    >
      {{ $t('app_name') }}
    </h2>
  </router-link>
</template>

<script setup>
import { useAppStore } from '@/store'
const appStore = useAppStore()
</script>
