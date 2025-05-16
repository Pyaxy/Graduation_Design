<script lang="ts" setup>
import type { CourseData } from "../apis/type"
import { useUserStore } from "@/pinia/stores/user"
import { storeToRefs } from "pinia"
import { onMounted, ref, watch } from "vue"
import { useRoute } from "vue-router"
import { getCourseDetail } from "../apis"
import CourseSubjectList from "./components/CourseSubjectList.vue"
import GroupList from "./components/GroupList.vue"
import PrivateSubjects from "./components/PrivateSubjects.vue"
import PublicSubjects from "./components/PublicSubjects.vue"
import StudentList from "./components/StudentList.vue"

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

// 在 script 部分添加
const subjectActiveTab = ref("private")

// 监听标签页变化
watch([activeTab, subjectActiveTab], ([newActiveTab, newSubjectActiveTab]) => {
  if (newActiveTab === "course-subjects") {
    // 当切换到课程课题列表时，触发刷新
    getCourseDetailData()
  } else if (newActiveTab === "subjects") {
    // 当切换到添加课题时，根据子标签页触发不同的刷新
    if (newSubjectActiveTab === "private" || newSubjectActiveTab === "public") {
      getCourseDetailData()
    }
  } else if (newActiveTab === "students") {
    // 当切换到学生列表时，触发刷新
    getCourseDetailData()
  } else if (newActiveTab === "groups") {
    // 当切换到小组列表时，触发刷新
    getCourseDetailData()
  }
})

onMounted(() => {
  getCourseDetailData()
})
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
          <StudentList
            v-if="activeTab === 'students' && courseId"
            :course-id="courseId"
            @refresh="getCourseDetailData"
          />
        </el-tab-pane>
        <el-tab-pane label="课题列表" name="course-subjects">
          <CourseSubjectList
            v-if="activeTab === 'course-subjects' && courseId"
            :course-id="courseId"
            @refresh="getCourseDetailData"
          />
        </el-tab-pane>
        <el-tab-pane
          v-if="userRole === 'TEACHER' || userRole === 'ADMIN'"
          label="添加课题"
          name="subjects"
        >
          <!-- 课题管理内容 -->
          <el-tabs v-model="subjectActiveTab">
            <el-tab-pane label="个人私有课题" name="private">
              <PrivateSubjects
                v-if="activeTab === 'subjects' && subjectActiveTab === 'private' && courseId"
                :course-id="courseId"
                :course-info="courseInfo"
                @refresh="getCourseDetailData"
              />
            </el-tab-pane>
            <el-tab-pane label="公共课题" name="public">
              <PublicSubjects
                v-if="activeTab === 'subjects' && subjectActiveTab === 'public' && courseId"
                :course-id="courseId"
                :course-info="courseInfo"
                @refresh="getCourseDetailData"
              />
            </el-tab-pane>
          </el-tabs>
        </el-tab-pane>
        <el-tab-pane label="小组列表" name="groups">
          <GroupList
            v-if="activeTab === 'groups' && courseId"
            :course-id="courseId"
            :course-status="courseInfo?.status || 'not_started'"
            @refresh="getCourseDetailData"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.app-container {
  padding: 20px;
}

/* 全局对话框样式 */
:global(.el-message-box) {
  display: inline-block;
  width: 420px;
  padding-bottom: 10px;
  vertical-align: middle;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  font-size: 18px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  text-align: left;
  overflow: hidden;
  backface-visibility: hidden;
}

:global(.el-message-box__wrapper) {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  overflow: auto;
  margin: 0;
}

:global(.el-message-box__wrapper::after) {
  content: "";
  display: inline-block;
  height: 100%;
  width: 0;
  vertical-align: middle;
}

:global(.el-message-box__header) {
  position: relative;
  padding: 15px 15px 10px;
}

:global(.el-message-box__title) {
  padding-left: 0;
  margin-bottom: 0;
  font-size: 18px;
  line-height: 1;
  color: #303133;
}

:global(.el-message-box__content) {
  padding: 10px 15px;
  color: #606266;
  font-size: 14px;
}

:global(.el-message-box__btns) {
  padding: 5px 15px 0;
  text-align: right;
}

:global(.el-message-box__btns button:nth-child(2)) {
  margin-left: 10px;
}

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

.tab-content {
  padding: 20px 0;
}

:deep(.el-tabs__nav-wrap) {
  margin-bottom: 20px;
}
</style>
