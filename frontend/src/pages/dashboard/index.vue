<script lang="ts" setup>
import { useUserStore } from "@/pinia/stores/user"

defineOptions({
  name: "Dashboard"
})

const userStore = useUserStore()
const isAdmin = userStore.roles.includes("ADMIN")
</script>

<template>
  <div class="dashboard-container">
    <h1>这是通用页面</h1>
    <p>当前用户角色: {{ isAdmin ? '管理员' : '编辑者' }}</p>

    <!-- 123 -->
  </div>
</template>

<style scoped>
.dashboard-container {
  padding: 20px;
}
</style>
