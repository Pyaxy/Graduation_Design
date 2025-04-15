<script lang="ts" setup>
import type { FormInstance, FormRules } from "element-plus"
import type { CourseData } from "./apis/type"
import { usePagination } from "@@/composables/usePagination"
import { CirclePlus, Refresh, RefreshRight, Search } from "@element-plus/icons-vue"
import { useRouter } from "vue-router"
import { getCourseList, joinCourse, leaveCourse } from "./apis"

defineOptions({
  name: "CourseStudent"
})

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// #region 查看详情
const router = useRouter()

function handleViewDetail(row: CourseData) {
  router.push(`course-detail/${row.id}`)
}
// #endregion

// #region 加入/退出课程
const joinDialogVisible = ref<boolean>(false)
const joinFormRef = ref<FormInstance | null>(null)
const joinData = reactive({
  course_code: ""
})

function handleJoin() {
  joinDialogVisible.value = true
}

function submitJoin() {
  joinFormRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    loading.value = true
    joinCourse(joinData)
      .then(() => {
        ElMessage.success("加入成功")
        joinDialogVisible.value = false
        getCourseData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}

function handleLeave(row: CourseData) {
  // 如果课程已结束，提示用户无需退出
  if (row.status === "completed") {
    ElMessage.warning("课程已结束，无需退出")
    return
  }

  ElMessageBox.confirm(
    `正在退出课程：${row.name}，退出后将无法继续访问课程内容，确认退出？`,
    "提示",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    }
  ).then(() => {
    loading.value = true
    leaveCourse(row.id)
      .then(() => {
        ElMessage.success("退出成功")
        getCourseData()
      })
      .catch((error) => {
        if (error.message) {
          ElMessage.error(error.message)
        } else {
          ElMessage.error("退出课程失败")
        }
      })
      .finally(() => {
        loading.value = false
      })
  })
}
// #endregion

// #region 查
const tableData = ref<CourseData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  search: "",
  status: "" as "not_started" | "in_progress" | "completed" | ""
})

function getCourseData() {
  loading.value = true
  getCourseList({
    page: paginationData.currentPage,
    page_size: paginationData.pageSize,
    ...searchData
  })
    .then(({ data }) => {
      paginationData.total = data.count
      tableData.value = data.results
    })
    .catch(() => {
      tableData.value = []
      paginationData.total = 0
    })
    .finally(() => {
      loading.value = false
    })
}

function handleSearch() {
  paginationData.currentPage === 1 ? getCourseData() : (paginationData.currentPage = 1)
}

function resetSearch() {
  searchFormRef.value?.resetFields()
  searchData.search = ""
  searchData.status = ""
  handleSearch()
}
// #endregion

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getCourseData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="search" label="课程名称或课程码">
          <el-input v-model="searchData.search" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="status" label="状态">
          <el-select v-model="searchData.status" placeholder="请选择" clearable style="width: 200px">
            <el-option label="未开始" value="not_started" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已结束" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            查询
          </el-button>
          <el-button :icon="Refresh" @click="resetSearch">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card v-loading="loading" shadow="never">
      <div class="toolbar-wrapper">
        <div>
          <el-button type="primary" :icon="CirclePlus" @click="handleJoin">
            加入课程
          </el-button>
        </div>
        <div>
          <el-tooltip content="刷新当前页">
            <el-button type="primary" :icon="RefreshRight" circle @click="getCourseData" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table :data="tableData">
          <el-table-column prop="name" label="课程名称" align="center" />
          <el-table-column prop="description" label="课程描述" align="center" />
          <el-table-column prop="teacher.name" label="教师" align="center" />
          <el-table-column prop="course_code" label="课程码" align="center" />
          <el-table-column prop="status" label="状态" align="center">
            <template #default="scope">
              <el-tag v-if="scope.row.status === 'in_progress'" type="success" effect="plain">
                进行中
              </el-tag>
              <el-tag v-else-if="scope.row.status === 'completed'" type="info" effect="plain">
                已结束
              </el-tag>
              <el-tag v-else type="warning" effect="plain">
                未开始
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_date" label="开始日期" align="center" />
          <el-table-column prop="end_date" label="结束日期" align="center" />
          <el-table-column fixed="right" label="操作" width="200" align="center">
            <template #default="scope">
              <el-button type="primary" text bg size="small" @click="handleViewDetail(scope.row)">
                查看
              </el-button>
              <el-button type="danger" text bg size="small" @click="handleLeave(scope.row)">
                退出
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
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
    </el-card>

    <!-- 加入课程对话框 -->
    <el-dialog v-model="joinDialogVisible" title="加入课程" width="50%">
      <el-form ref="joinFormRef" :model="joinData" label-width="100px" label-position="left">
        <el-form-item prop="course_code" label="课程码">
          <el-input v-model="joinData.course_code" placeholder="请输入课程码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="joinDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="loading" @click="submitJoin">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.search-wrapper {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding-bottom: 2px;
  }
}

.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.table-wrapper {
  margin-bottom: 20px;
}

.pager-wrapper {
  display: flex;
  justify-content: flex-end;
}
</style>
