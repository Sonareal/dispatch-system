<template>
  <n-dropdown :options="options" @select="handleChangeLocale">
    <n-icon mr-20 size="18" style="cursor: pointer">
      <icon-mdi:globe />
    </n-icon>
  </n-dropdown>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/store'
import { router } from '~/src/router'

const store = useAppStore()
const { availableLocales, t } = useI18n()

const options = computed(() => {
  let select = []
  availableLocales.forEach((locale) => {
    select.push({
      label: t('lang', 1, { locale: locale }),
      key: locale,
    })
  })
  return select
})

const handleChangeLocale = (value) => {
  store.setLocale(value)
  // Full page reload to apply all translations including dynamic menus
  window.location.reload()
}
</script>
