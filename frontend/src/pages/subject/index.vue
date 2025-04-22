<script lang="ts" setup>
import { useUserStore } from "@/pinia/stores/user"
import { computed, ref } from "vue"
import MySubjects from "./components/MySubjects.vue"
import PublicSubjects from "./components/PublicSubjects.vue"

defineOptions({
  name: "Subject"
})

const userStore = useUserStore()
const { role } = storeToRefs(userStore)

const activeTab = ref(computed(() => role.value === "STUDENT" ? "public-subjects" : "my-subjects"))

// 计算属性：是否显示我的课题标签页
const showMySubjects = computed(() => role.value !== "STUDENT")
</script>

<template>
  <div class="app-container">
    <el-tabs v-model="activeTab">
      <el-tab-pane v-if="showMySubjects" label="我的课题" name="my-subjects">
        <MySubjects />
      </el-tab-pane>
      <el-tab-pane label="公开课题库" name="public-subjects">
        <PublicSubjects />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style lang="scss" scoped>
.app-container {
  padding: 20px;
}
</style>
