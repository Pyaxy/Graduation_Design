<script lang="ts" setup>
import type { CourseData, CreateGroupRequestData, GroupData } from "../apis/type"
import { usePagination } from "@/common/composables/usePagination"
import { useUserStore } from "@/pinia/stores/user"
import { CirclePlus, RefreshRight, Search } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"
import { storeToRefs } from "pinia"
import { onMounted, ref, reactive, watch } from "vue"
import { useRoute } from "vue-router"
import { createGroup, getCourseDetail, getGroupsList, getStudents, joinGroup, leaveCourse, leaveGroup } from "../apis"

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
  student_search: ""
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

// 小组列表相关
const { paginationData: groupPaginationData, handleCurrentChange: handleGroupCurrentChange, handleSizeChange: handleGroupSizeChange } = usePagination()
const groupsLoading = ref(false)
const groupsData = ref<GroupData[]>([])

// 创建小组相关
const createGroupDialogVisible = ref(false)
const createGroupForm = reactive<CreateGroupRequestData>({
  course: courseId
})

// 获取小组列表
function getGroupsData() {
  groupsLoading.value = true
  getGroupsList({
    page: groupPaginationData.currentPage,
    page_size: groupPaginationData.pageSize,
    course_id: courseId
  })
    .then(({ data }) => {
      groupPaginationData.total = data.count
      groupsData.value = data.results
    })
    .finally(() => {
      groupsLoading.value = false
    })
}

// 加入小组
function handleJoinGroup(group: GroupData) {
  ElMessageBox.confirm(`确定要加入小组：${group.name}？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    groupsLoading.value = true
    joinGroup(group.id)
      .then(() => {
        ElMessage.success("加入成功")
        getGroupsData()
      })
      .catch((error) => {
        if (error.message) {
          ElMessage.error(error.message)
        } else {
          ElMessage.error("加入小组失败")
        }
      })
      .finally(() => {
        groupsLoading.value = false
      })
  })
}

// 判断是否是组长
function isGroupCreator(group: GroupData) {
  return group.creator.user_id === userStore.user_id
}

// 判断是否是教师
function isTeacher() {
  return userRole.value === "TEACHER" || userRole.value === "ADMIN"
}

// 判断是否有权限踢出成员
function canRemoveMember(group: GroupData, student: GroupData["students"][0]) {
  // 如果是教师，可以踢出所有成员
  if (isTeacher()) return true
  // 如果是组长，可以踢出自己小组的成员
  if (isGroupCreator(group)) return true
  // 如果是自己，可以退出小组
  if (student.user_id === userStore.user_id) return true
  return false
}

// 踢出成员
function handleRemoveMember(group: GroupData, student: GroupData["students"][0]) {
  ElMessageBox.confirm(`确定要将学生 ${student.name} 从小组 ${group.name} 中移除吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    groupsLoading.value = true
    leaveGroup(group.id, {
      student_user_id: student.user_id
    })
      .then(() => {
        ElMessage.success("移除成功")
        getGroupsData()
      })
      .catch((error) => {
        if (error.message) {
          ElMessage.error(error.message)
        } else {
          ElMessage.error("移除失败")
        }
      })
      .finally(() => {
        groupsLoading.value = false
      })
  })
}

// 创建小组
function handleCreateGroup() {
  groupsLoading.value = true
  createGroup(createGroupForm)
    .then(() => {
      ElMessage.success("创建成功")
      createGroupDialogVisible.value = false
      getGroupsData()
    })
    .catch((error) => {
      if (error.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error("创建失败")
      }
    })
    .finally(() => {
      groupsLoading.value = false
    })
}

onMounted(() => {
  getCourseDetailData()
})

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getStudentsData, { immediate: true })
watch([() => groupPaginationData.currentPage, () => groupPaginationData.pageSize], getGroupsData, { immediate: true })
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
        <el-tab-pane label="小组列表" name="groups">
          <!-- 小组列表内容 -->
          <div v-loading="groupsLoading" class="groups-wrapper">
            <!-- 工具栏 -->
            <div class="toolbar-wrapper">
              <div>
                <el-button v-if="userRole === 'STUDENT'" type="primary" :icon="CirclePlus" @click="createGroupDialogVisible = true">
                  创建小组
                </el-button>
              </div>
              <div>
                <el-tooltip content="刷新当前页">
                  <el-button type="primary" :icon="RefreshRight" circle @click="getGroupsData" />
                </el-tooltip>
              </div>
            </div>
            <el-row :gutter="20">
              <el-col v-for="group in groupsData" :key="group.id" :xs="24" :sm="12" :md="8" :lg="6">
                <el-card class="group-card" shadow="hover">
                  <template #header>
                    <div class="group-header">
                      <span class="group-name">{{ group.name }}</span>
                      <el-tag v-if="group.creator.user_id === userStore.user_id" type="success" size="small">
                        组长
                      </el-tag>
                    </div>
                  </template>
                  <div class="group-members">
                    <div v-for="student in group.students" :key="student.user_id" class="member-item">
                      <div class="member-info">
                        <span class="member-name">{{ student.name }}</span>
                        <el-tag v-if="student.user_id === group.creator.user_id" type="success" size="small">
                          组长
                        </el-tag>
                      </div>
                      <div class="member-actions">
                        <el-button
                          v-if="canRemoveMember(group, student)"
                          type="danger"
                          size="small"
                          @click="handleRemoveMember(group, student)"
                        >
                          {{ student.user_id === userStore.user_id ? '退出' : '踢出' }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                  <div class="group-actions">
                    <el-button
                      v-if="!group.students.some(s => s.user_id === userStore.user_id) && userRole === 'STUDENT'"
                      type="primary"
                      size="small"
                      @click="handleJoinGroup(group)"
                    >
                      加入小组
                    </el-button>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <div class="pager-wrapper">
              <el-pagination
                background
                :layout="groupPaginationData.layout"
                :page-sizes="groupPaginationData.pageSizes"
                :total="groupPaginationData.total"
                :page-size="groupPaginationData.pageSize"
                :current-page="groupPaginationData.currentPage"
                @size-change="handleGroupSizeChange"
                @current-change="handleGroupCurrentChange"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建小组对话框 -->
    <el-dialog v-model="createGroupDialogVisible" title="创建小组" width="50%">
      <div class="create-group-content">
        <p>确定要创建新的小组吗？</p>
        <p class="tip">小组名称将由系统自动生成</p>
      </div>
      <template #footer>
        <el-button @click="createGroupDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="groupsLoading" @click="handleCreateGroup">
          确认
        </el-button>
      </template>
    </el-dialog>
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

.groups-wrapper {
  padding: 20px 0;
}

.group-card {
  margin-bottom: 20px;
  height: 100%;

  .group-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .group-name {
      font-weight: bold;
      font-size: 16px;
    }
  }

  .group-members {
    margin-bottom: 16px;

    .member-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .member-info {
        display: flex;
        align-items: center;
        gap: 8px;

        .member-name {
          font-size: 14px;
        }
      }

      .member-actions {
        display: flex;
        gap: 8px;
      }
    }
  }

  .group-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}

.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.create-group-content {
  text-align: center;
  padding: 20px 0;

  .tip {
    color: #909399;
    font-size: 14px;
    margin-top: 10px;
  }
}
</style>
