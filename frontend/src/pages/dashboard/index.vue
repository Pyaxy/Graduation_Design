<script lang="ts" setup>
import { useUserStore } from "@/pinia/stores/user"

defineOptions({
  name: "Dashboard"
})

const userStore = useUserStore()
const isAdmin = userStore.roles.includes("ADMIN")

const features = [
  {
    title: '课题管理',
    description: '支持教师发布、管理课程设计课题，学生可在线选题和提交作品。',
    icon: '📚'
  },
  {
    title: '学生管理',
    description: '提供学生信息管理、成绩管理、学习进度跟踪等功能。',
    icon: '👨‍🎓'
  },
  {
    title: '课程管理',
    description: '支持课程信息维护、教学大纲管理、课程资源上传等功能。',
    icon: '📝'
  },
  {
    title: '代码管理',
    description: '提供代码在线编辑、版本控制、代码评审等功能。',
    icon: '💻'
  },
  {
    title: '教学过程管理',
    description: '支持教学进度跟踪、作业管理、在线答疑等功能。',
    icon: '📊'
  },
  {
    title: '文档管理',
    description: '提供教学文档、学习资料的上传、下载和管理功能。',
    icon: '📄'
  }
]
</script>

<template>
  <div class="dashboard-container">
    <div class="welcome-section">
      <h1>程序设计实践课程教学平台</h1>
      <p class="subtitle">基于Django框架的现代化教学解决方案</p>
    </div>

    <div class="features-grid">
      <div v-for="feature in features" :key="feature.title" class="feature-card">
        <div class="feature-icon">{{ feature.icon }}</div>
        <h3>{{ feature.title }}</h3>
        <p>{{ feature.description }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
}

.welcome-section h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 1.2em;
  color: #666;
}

.features-grid {
  display: flex;
  flex-direction: row;
  gap: 20px;
  margin-top: 30px;
  overflow-x: auto;
  min-width: 0;
}

.feature-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  font-size: 2em;
  margin-bottom: 15px;
}

.feature-card h3 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
}

.admin-notice {
  margin-top: 20px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  text-align: center;
}
</style>
