<script lang="ts" setup>
import { usePagination } from "@/common/composables/usePagination"
import { useUserStore } from "@/pinia/stores/user"
import { RefreshRight, Search } from "@element-plus/icons-vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { ref, reactive, watch } from "vue"
import { getStudents, leaveCourse } from "../../apis"

const props = defineProps<{
  courseId: string
}>()

const emit = defineEmits<{
  (e: "refresh"): void
}>()

// 用户角色
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

// 学生列表相关
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const studentsLoading = ref(false)
const studentsData = ref<any[]>([])
const searchFormRef = ref()
const searchData = reactive({
  student_search: ""
})

// 获取学生列表
function getStudentsData() {
  studentsLoading.value = true
  getStudents(props.courseId, {
    page: paginationData.currentPage,
    page_size: paginationData.pageSize,
    ...searchData
  })
    .then(({ data }) => {
      paginationData.total = data.count
      studentsData.value = data.results
    })
    .finally(() => {
      studentsLoading.value = false
    })
}

// 搜索
function handleSearch() {
  paginationData.currentPage === 1 ? getStudentsData() : (paginationData.currentPage = 1)
}

// 重置搜索
function resetSearch() {
  searchFormRef.value?.resetFields()
  searchData.student_search = ""
  handleSearch()
}

// 退出学生
function handleRemoveStudent(row: any) {
  ElMessageBox.confirm(`确定要将学生 ${row.name} 从课程中移除吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(async () => {
    await leaveCourse(props.courseId, {
      student_user_id: row.user_id
    })
      .then(() => {
        ElMessage.success("移除成功")
        getStudentsData()
        emit("refresh")
      })
      .catch(() => {
        ElMessage.error("移除失败")
      })
  })
}

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getStudentsData, { immediate: true })

defineExpose({
  getStudentsData
})
</script>

<template>
  <div>
    <!-- 学生列表搜索区域 -->
    <el-card v-loading="studentsLoading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="student_search" label="学生姓名或学号">
          <el-input v-model="searchData.student_search" placeholder="请输入" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            查询
          </el-button>
          <el-button :icon="RefreshRight" @click="resetSearch">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 学生列表表格 -->
    <el-card shadow="never" class="table-wrapper">
      <el-table :data="studentsData" border>
        <el-table-column prop="name" label="姓名" align="center" />
        <el-table-column prop="user_id" label="学号" align="center" />
        <el-table-column
          v-if="userRole === 'TEACHER' || userRole === 'ADMIN'"
          fixed="right"
          label="操作"
          width="120"
          align="center"
        >
          <template #default="scope">
            <el-button type="danger" text bg size="small" @click="handleRemoveStudent(scope.row)">
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="pager-wrapper">
      <el-pagination
        background
        :layout="paginationData.layout"
        :page-sizes="paginationData.pageSizes"
        :total="paginationData.total"
        :page-size="paginationData.pageSize"
        :current-page="paginationData.currentPage"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.search-wrapper {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding-bottom: 2px;
  }
}

.table-wrapper {
  margin-bottom: 20px;
}

.pager-wrapper {
  display: flex;
  justify-content: flex-end;
}
</style>
