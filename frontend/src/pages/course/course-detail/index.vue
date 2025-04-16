<script lang="ts" setup>
import type { CourseData } from "../apis/type"
import { usePagination } from "@/common/composables/usePagination"
import { useUserStore } from "@/pinia/stores/user"
import { RefreshRight, Search } from "@element-plus/icons-vue"
import { storeToRefs } from "pinia"
import { onMounted, ref, reactive, watch } from "vue"
import { useRoute } from "vue-router"
import { getCourseDetail, getStudents, leaveCourse} from "../apis"

const route = useRoute()
const courseId = route.params.id as string
const loading = ref(false)
const courseInfo = ref<CourseData | null>(null)

// 用户角色
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

// 获取课程详情
function getCourseDetailData() {
  loading.value = true
  return getCourseDetail(courseId)
    .then(({ data }) => {
      courseInfo.value = data
    })
    .finally(() => {
      loading.value = false
    })
}

// 当前激活的标签页
const activeTab = ref("students")

// 学生列表相关
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const studentsLoading = ref(false)
const studentsData = ref<any[]>([])
const searchFormRef = ref()
const searchData = reactive({
  search: ""
})

// 获取学生列表
function getStudentsData() {
  studentsLoading.value = true
  getStudents(courseId, {
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
  searchData.search = ""
  handleSearch()
}

// 退出学生
function handleRemoveStudent(row: any) {
  ElMessageBox.confirm(`确定要将学生 ${row.name} 从课程中移除吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(async () => {
    await leaveCourse(courseId, {
      student_user_id: row.user_id
    })
      .then(() => {
        ElMessage.success("移除成功")
        getStudentsData()
      })
      .catch(() => {
        ElMessage.error("移除失败")
      })
  })
}

onMounted(() => {
  getCourseDetailData()
})

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getStudentsData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <!-- 课程基本信息卡片 -->
    <el-card v-loading="loading" shadow="never" class="course-info-card">
      <template v-if="courseInfo">
        <div class="course-header">
          <h2>{{ courseInfo.name }}</h2>
          <el-tag :type="courseInfo.status === 'in_progress' ? 'success' : courseInfo.status === 'completed' ? 'info' : 'warning'" effect="plain">
            {{ courseInfo.status === 'in_progress' ? '进行中' : courseInfo.status === 'completed' ? '已结束' : '未开始' }}
          </el-tag>
        </div>
        <div class="course-meta">
          <div class="meta-item">
            <span class="label">课程码：</span>
            <span class="value">{{ courseInfo.course_code }}</span>
          </div>
          <div class="meta-item">
            <span class="label">教师：</span>
            <span class="value">{{ courseInfo.teacher?.name }}</span>
          </div>
          <div class="meta-item">
            <span class="label">时间：</span>
            <span class="value">{{ courseInfo.start_date }} 至 {{ courseInfo.end_date }}</span>
          </div>
        </div>
        <div class="course-description">
          <span class="label">课程描述：</span>
          <span class="value">{{ courseInfo.description || '暂无描述' }}</span>
        </div>
      </template>
    </el-card>

    <!-- 导航标签页 -->
    <el-card shadow="never" class="nav-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="学生列表" name="students">
          <!-- 学生列表搜索区域 -->
          <el-card v-loading="studentsLoading" shadow="never" class="search-wrapper">
            <el-form ref="searchFormRef" :inline="true" :model="searchData">
              <el-form-item prop="search" label="学生姓名或学号">
                <el-input v-model="searchData.search" placeholder="请输入" />
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
              <el-table-column v-if="['ADMIN', 'TEACHER'].includes(userRole)" fixed="right" label="操作" width="120" align="center">
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
        </el-tab-pane>
        <el-tab-pane label="课程作业" name="assignments">
          <!-- 课程作业内容 -->
          <div class="tab-content">
            课程作业内容
          </div>
        </el-tab-pane>
        <el-tab-pane label="课程资源" name="resources">
          <!-- 课程资源内容 -->
          <div class="tab-content">
            课程资源内容
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.course-info-card {
  margin-bottom: 20px;

  .course-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      margin-right: 16px;
    }
  }

  .course-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    margin-bottom: 16px;

    .meta-item {
      .label {
        color: #606266;
        margin-right: 8px;
      }
    }
  }

  .course-description {
    .label {
      color: #606266;
      margin-right: 8px;
    }
  }
}

.nav-card {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
}

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

.tab-content {
  padding: 20px 0;
}
</style>
