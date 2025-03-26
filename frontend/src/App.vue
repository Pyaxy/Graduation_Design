<script lang="ts" setup>
// import { usePany } from "@@/composables/usePany"
import { useTokenValidation } from "@/common/composables/useTokenValidation"
import { useGreyAndColorWeakness } from "@@/composables/useGreyAndColorWeakness"
import { useTheme } from "@@/composables/useTheme"
import zhCn from "element-plus/es/locale/lang/zh-cn" // Element Plus 中文包

const { initTheme } = useTheme()
const { initGreyAndColorWeakness } = useGreyAndColorWeakness()
const { validateToken } = useTokenValidation()
// 首页通知栏，一个通知栏显示一个通知，在App.vue中调用
// const { initStarNotification, initStoreNotification } = usePany()

onMounted(async () => {
  await validateToken()
  initTheme()
  initGreyAndColorWeakness()
  // initStarNotification()
  // initStoreNotification()
})
</script>

<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>
