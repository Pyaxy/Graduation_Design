<!-- frontend/src/views/HomeView.vue -->
<template>
    <a-row type="flex" justify="center">
      <a-col :span="18">
        <!-- 角色提示卡片 -->
        <a-card :bordered="false">
          <template #title>
            <span class="role-title">系统首页</span>
          </template>
          
          <!-- 根据角色显示不同提示 -->
          <a-alert 
            v-if="role"
            :message="alertMessage"
            :type="alertType"
            :show-icon="true"
            :description="roleDescription"
            class="role-alert"
          />
          
          <!-- 未获取到角色的异常处理 -->
          <a-alert
            v-else
            message="角色信息异常"
            type="error"
            description="未能获取有效的用户角色信息，请重新登录"
          />
        </a-card>
      </a-col>
    </a-row>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue';
  import userRole from '@/hooks/userRole';
  
  // 从sessionStorage获取角色信息
  const { role } = userRole();
  
  // 计算属性处理角色信息
  const alertMessage = computed(() => {
    return `当前角色：${role.value}`;
  });
  
  const alertType = computed(() => {
    const roleMap = {
      '管理员': 'success',
      '教师': 'info',
      '学生': 'warning'
    };
    return roleMap[role.value] || 'error';
  });
  
  const roleDescription = computed(() => {
    const descriptions = {
      '管理员': '您拥有系统全部管理权限，可访问所有功能模块',
      '教师': '您可以管理课程内容和学生作业，查看学生进度',
      '学生': '您可以参与编程练习、提交作业和查看课程资料'
    };
    return descriptions[role.value] || '未知角色类型，请联系管理员';
  });
  </script>
  
  <style scoped>
  .role-alert {
    margin-top: 20px;
  }
  
  .role-title {
    font-size: 1.5rem;
    color: #1890ff;
  }
  </style>
  