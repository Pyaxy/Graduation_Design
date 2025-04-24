<script lang="ts" setup>
import type { GroupData } from "./apis/type"
import CourseSubjectList from "@/pages/course/course-detail/components/CourseSubjectList.vue"
import { useUserStore } from "@/pinia/stores/user"
import { ElMessage } from "element-plus"
import { storeToRefs } from "pinia"
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getGroupDetail, selectSubject, unselectSubject } from "./apis"

const route = useRoute()
const router = useRouter()
const courseId = route.params.courseId as string
const groupId = route.params.groupId as string
const loading = ref(false)
const groupInfo = ref<GroupData | null>(null)

// 用户角色
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

// 获取小组详情
function getGroupDetailData() {
  loading.value = true
  return getGroupDetail(groupId)
    .then(({ data }) => {
      groupInfo.value = data
    })
    .finally(() => {
      loading.value = false
    })
}

// 处理选题
function handleSelectSubject(subjectId: string) {
  loading.value = true
  selectSubject(groupId, subjectId)
    .then(() => {
      ElMessage.success("选题成功")
      getGroupDetailData()
    })
    .catch((error: any) => {
      if (error.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error("选题失败")
      }
    })
    .finally(() => {
      loading.value = false
    })
}

// 处理退选
function handleUnselectSubject() {
  loading.value = true
  unselectSubject(groupId)
    .then(() => {
      ElMessage.success("退选成功")
      getGroupDetailData()
    })
    .catch((error: any) => {
      if (error.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error("退选失败")
      }
    })
    .finally(() => {
      loading.value = false
    })
}

onMounted(() => {
  getGroupDetailData()
})
</script>

<template>
  <div class="app-container">
    <!-- 小组基本信息卡片 -->
    <el-card v-loading="loading" shadow="never" class="group-info-card">
      <template v-if="groupInfo">
        <div class="group-header">
          <h2>{{ groupInfo.name }}</h2>
          <div class="group-stats">
            <el-tag type="info">成员数：{{ groupInfo.students.length }}/{{ groupInfo.max_students }}</el-tag>
          </div>
        </div>
        <div class="group-meta">
          <div class="meta-item">
            <span class="label">课程ID：</span>
            <span class="value">{{ groupInfo.course }}</span>
          </div>
          <div class="meta-item">
            <span class="label">组长：</span>
            <span class="value">{{ groupInfo.creator.name }}</span>
            <el-tag size="small" type="success">{{ groupInfo.creator.role_display }}</el-tag>
          </div>
          <div class="meta-item">
            <span class="label">创建时间：</span>
            <span class="value">{{ groupInfo.created_at }}</span>
          </div>
          <div class="meta-item">
            <span class="label">更新时间：</span>
            <span class="value">{{ groupInfo.updated_at }}</span>
          </div>
        </div>
      </template>
    </el-card>

    <!-- 导航标签页 -->
    <el-card shadow="never" class="nav-card">
      <el-tabs>
        <el-tab-pane label="成员列表">
          <div class="tab-content">
            <el-table v-if="groupInfo" :data="groupInfo.students">
              <el-table-column prop="user_id" label="学号" align="center" />
              <el-table-column prop="name" label="姓名" align="center" />
              <el-table-column prop="role_display" label="角色" align="center">
                <template #default="scope">
                  <el-tag v-if="scope.row.user_id === groupInfo.creator.user_id" type="success">
                    组长
                  </el-tag>
                  <el-tag v-else type="info">
                    {{ scope.row.role_display }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        <el-tab-pane label="选题信息">
          <div class="tab-content">
            <template v-if="groupInfo?.group_subjects?.length > 0">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="课题名称">
                  {{ groupInfo.group_subjects[0].course_subject.subject.title }}
                </el-descriptions-item>
                <el-descriptions-item label="课题描述">
                  {{ groupInfo.group_subjects[0].course_subject.subject.description }}
                </el-descriptions-item>
                <el-descriptions-item label="课题类型">
                  <el-tag :type="groupInfo.group_subjects[0].course_subject.subject_type === 'PUBLIC' ? 'success' : 'warning'">
                    {{ groupInfo.group_subjects[0].course_subject.subject_type === 'PUBLIC' ? '公开课题' : '私有课题' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="编程语言">
                  <el-tag v-for="lang in groupInfo.group_subjects[0].course_subject.subject.languages" :key="lang" class="mr-2">
                    {{ lang }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建者">
                  {{ groupInfo.group_subjects[0].course_subject.subject.creator.name }}
                  <el-tag size="small" type="info" class="ml-2">
                    {{ groupInfo.group_subjects[0].course_subject.subject.creator.role_display }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="选题时间">
                  {{ groupInfo.group_subjects[0].created_at }}
                </el-descriptions-item>
                <el-descriptions-item>
                  <el-button type="danger" @click="handleUnselectSubject">退选课题</el-button>
                </el-descriptions-item>
              </el-descriptions>
            </template>
            <template v-else>
              <el-empty description="暂未选题" />
              <div class="select-subject-wrapper">
                <h3>可选课题列表</h3>
                <CourseSubjectList
                  :course-id="courseId"
                  :show-select-button="true"
                  @select="handleSelectSubject"
                />
              </div>
            </template>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.app-container {
  padding: 20px;
}

.group-info-card {
  margin-bottom: 20px;

  .group-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      margin-right: 16px;
    }
  }

  .group-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    margin-bottom: 16px;

    .meta-item {
      display: flex;
      align-items: center;
      gap: 8px;

      .label {
        color: #606266;
      }
    }
  }
}

.nav-card {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
}

.tab-content {
  padding: 20px 0;
}

:deep(.el-tabs__nav-wrap) {
  margin-bottom: 20px;
}

.mr-2 {
  margin-right: 8px;
}

.ml-2 {
  margin-left: 8px;
}

.select-subject-wrapper {
  margin-top: 20px;

  h3 {
    margin-bottom: 20px;
    font-size: 16px;
    font-weight: 500;
  }
}
</style>
