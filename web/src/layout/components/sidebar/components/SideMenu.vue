<template>
  <n-menu
    ref="menu"
    class="side-menu"
    accordion
    :indent="18"
    :collapsed-icon-size="22"
    :collapsed-width="64"
    :options="menuOptions"
    :value="activeKey"
    @update:value="handleMenuSelect"
  />
</template>

<script setup>
import { usePermissionStore, useAppStore } from '@/store'
import { renderCustomIcon, renderIcon, isExternal } from '@/utils'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n({ useScope: 'global' })

// Menu name i18n mapping (Chinese -> i18n key)
const menuNameMap = {
  '工单管理': 'menu.ticket',
  '工单列表': 'menu.ticket_list',
  '待审核': 'menu.pending_review',
  '我的工单': 'menu.my_tickets',
  '我负责的': 'menu.my_assigned',
  '沟通管理': 'menu.communication',
  '消息记录': 'menu.messages',
  '语音记录': 'menu.voice_records',
  '通话记录': 'menu.call_records',
  '区域管理': 'menu.area',
  '城市管理': 'menu.city',
  '行政区管理': 'menu.region',
  '系统管理': 'menu.system',
  '用户管理': 'menu.user',
  '角色管理': 'menu.role',
  '菜单管理': 'menu.menu',
  'API管理': 'menu.api',
  '部门管理': 'menu.dept',
  '审计日志': 'menu.audit_log',
  '操作日志': 'menu.op_log',
  '系统配置': 'menu.sys_config',
}

function translateMenuName(name) {
  if (locale.value === 'cn') return name
  const key = menuNameMap[name]
  if (key) {
    const translated = t(key)
    if (translated !== key) return translated
  }
  return name
}

const router = useRouter()
const curRoute = useRoute()
const permissionStore = usePermissionStore()
const appStore = useAppStore()

const activeKey = computed(() => curRoute.meta?.activeMenu || curRoute.name)

const menuOptions = computed(() => {
  return permissionStore.menus.map((item) => getMenuItem(item)).sort((a, b) => a.order - b.order)
})

const menu = ref(null)
watch(curRoute, async () => {
  await nextTick()
  menu.value?.showOption()
})

function resolvePath(basePath, path) {
  if (isExternal(path)) return path
  return (
    '/' +
    [basePath, path]
      .filter((path) => !!path && path !== '/')
      .map((path) => path.replace(/(^\/)|(\/$)/g, ''))
      .join('/')
  )
}

function getMenuItem(route, basePath = '') {
  let menuItem = {
    label: translateMenuName((route.meta && route.meta.title) || route.name),
    key: route.name,
    path: resolvePath(basePath, route.path),
    icon: getIcon(route.meta),
    order: route.meta?.order || 0,
  }

  const visibleChildren = route.children
    ? route.children.filter((item) => item.name && !item.isHidden)
    : []

  if (!visibleChildren.length) return menuItem

  if (visibleChildren.length === 1) {
    // 单个子路由处理
    const singleRoute = visibleChildren[0]
    menuItem = {
      ...menuItem,
      label: translateMenuName(singleRoute.meta?.title || singleRoute.name),
      key: singleRoute.name,
      path: resolvePath(menuItem.path, singleRoute.path),
      icon: getIcon(singleRoute.meta),
    }
    const visibleItems = singleRoute.children
      ? singleRoute.children.filter((item) => item.name && !item.isHidden)
      : []

    if (visibleItems.length === 1) {
      menuItem = getMenuItem(visibleItems[0], menuItem.path)
    } else if (visibleItems.length > 1) {
      menuItem.children = visibleItems
        .map((item) => getMenuItem(item, menuItem.path))
        .sort((a, b) => a.order - b.order)
    }
  } else {
    menuItem.children = visibleChildren
      .map((item) => getMenuItem(item, menuItem.path))
      .sort((a, b) => a.order - b.order)
  }
  return menuItem
}

function getIcon(meta) {
  if (meta?.customIcon) return renderCustomIcon(meta.customIcon, { size: 18 })
  if (meta?.icon) return renderIcon(meta.icon, { size: 18 })
  return null
}

function handleMenuSelect(key, item) {
  if (isExternal(item.path)) {
    window.open(item.path)
  } else {
    if (item.path === curRoute.path) {
      appStore.reloadPage()
    } else {
      router.push(item.path)
    }
  }
}
</script>

<style lang="scss">
.side-menu:not(.n-menu--collapsed) {
  .n-menu-item-content {
    &::before {
      left: 5px;
      right: 5px;
    }
    &.n-menu-item-content--selected,
    &:hover {
      &::before {
        border-left: 4px solid var(--primary-color);
      }
    }
  }
}
</style>
