<script lang="ts" setup>
import type { CreateGroupRequestData, GroupData } from "../../apis/type"
import { usePagination } from "@/common/composables/usePagination"
import { useUserStore } from "@/pinia/stores/user"
import { CirclePlus, RefreshRight } from "@element-plus/icons-vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { storeToRefs } from "pinia"
import { ref, reactive, onMounted, watch } from "vue"
import { createGroup, getGroupsList, joinGroup, leaveGroup } from "../../apis"
import { useRouter } from "vue-router"

const props = defineProps<{
  courseId: string
}>()

const emit = defineEmits<{
  (e: "refresh"): void
}>()

// 用户角色
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

// 小组列表相关
const { paginationData: groupPaginationData, handleCurrentChange: handleGroupCurrentChange, handleSizeChange: handleGroupSizeChange } = usePagination()
const groupsLoading = ref(false)
const groupsData = ref<GroupData[]>([])

// 创建小组相关
const createGroupDialogVisible = ref(false)
const createGroupForm = reactive<CreateGroupRequestData>({
  course: props.courseId
})

const router = useRouter()

// 获取小组列表
function getGroupsData() {
  groupsLoading.value = true
  getGroupsList({
    page: groupPaginationData.currentPage,
    page_size: groupPaginationData.pageSize,
    course_id: props.courseId
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
        emit("refresh")
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
        emit("refresh")
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
      emit("refresh")
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

function handleViewDetail(groupId: string) {
  router.push({
    name: "Group-Detail",
    params: {
      courseId: props.courseId,
      groupId
    }
  })
}

// 监听分页参数的变化
watch([() => groupPaginationData.currentPage, () => groupPaginationData.pageSize], getGroupsData, { immediate: true })

defineExpose({
  getGroupsData
})
</script>

<template>
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
            <el-button
              v-if="group.students.some(student => student.user_id === userStore.user_id)"
              type="primary"
              text
              @click="handleViewDetail(group.id)"
            >
              查看详情
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

    <!-- 创建小组对话框 -->
    <el-dialog v-model="createGroupDialogVisible" title="创建小组" width="50%">
      <div class="create-group-content">
        <p>确定要创建新的小组吗？</p>
        <p class="tip">
          小组名称将由系统自动生成
        </p>
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

.pager-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
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
