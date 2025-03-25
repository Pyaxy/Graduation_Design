<template>
    <a-card title="认证测试面板" :bordered="false" class="test-panel">
      <a-space direction="vertical">
        <a-button 
          type="primary" 
          @click="testAccessToken"
          :loading="testingAccess"
        >
          <template #icon><LockOutlined /></template>
          验证Access Token有效性
        </a-button>
  
        <a-button 
          type="primary" 
          @click="testRefreshToken"
          :loading="testingRefresh"
        >
          <template #icon><SyncOutlined /></template>
          验证Refresh Token有效性
        </a-button>
  
        <a-button 
          danger 
          @click="clearAllTokens"
        >
          <template #icon><DeleteOutlined /></template>
          一键清除所有Token
        </a-button>
      </a-space>
  
      <a-divider />
  
      <a-descriptions title="当前Token状态" bordered>
        <a-descriptions-item label="Access Token存在">
          {{ hasAccessToken ? '是' : '否' }}
        </a-descriptions-item>
        <a-descriptions-item label="Refresh Token存在">
          {{ hasRefreshToken ? '是' : '否' }}
        </a-descriptions-item>
        <a-descriptions-item label="Access Token过期时间">
          {{ accessTokenExpire || '未知' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-card>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue';
  import { message } from 'ant-design-vue';
  import { 
    LockOutlined, 
    SyncOutlined, 
    DeleteOutlined 
  } from '@ant-design/icons-vue';
  import { apiClient } from '@/utils/auth';
  
  const testingAccess = ref(false);
  const testingRefresh = ref(false);
  
  // 计算属性实时反映存储状态
  const hasAccessToken = computed(() => {
    return !!sessionStorage.getItem('access_token');
  });
  
  const hasRefreshToken = computed(() => {
    return !!localStorage.getItem('refresh_token') || 
      document.cookie.includes('refresh_token=');
  });
  
  const accessTokenExpire = computed(() => {
    const token = sessionStorage.getItem('access_token');
    if (!token) return null;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return new Date(payload.exp * 1000).toLocaleString();
    } catch {
      return '无效Token';
    }
  });
  
  // 测试Access Token有效性
  const testAccessToken = async () => {
    testingAccess.value = true;
    try {
      const response = await apiClient.get('/accounts/user/');
      message.success(`Token有效，欢迎 ${response.data.name}`);
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Access Token已失效，请重新登录');
      } else {
        message.error(`验证失败：${error.message}`);
      }
    } finally {
      testingAccess.value = false;
    }
  };
  
  // 测试Refresh Token有效性
  const testRefreshToken = async () => {
    testingRefresh.value = true;
    try {
      const refreshToken = localStorage.getItem('refresh_token') || 
        sessionStorage.getItem('refresh_token');
        // document.cookie.replace(/(?:(?:^|.*;\s*)refresh_token\s*=\s*([^;]*).*$)|^.*$/, '$1');

  
      if (!refreshToken) throw new Error('无有效Refresh Token');
  
      const response = await apiClient.post('/accounts/refresh/', {
        refresh: refreshToken
      });
  
      sessionStorage.setItem('access_token', response.data.access);
      message.success('Refresh Token有效，已更新Access Token');
    } catch (error) {
      message.error(`Refresh Token无效：${error.response?.data?.error || error.message}`);
    } finally {
      testingRefresh.value = false;
    }
  };
  
  // 清除所有Token
  const clearAllTokens = () => {
    sessionStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('role');
    sessionStorage.removeItem('name');
    sessionStorage.removeItem('user_id');
    
    
    // 清除Cookie中的refresh_token
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    message.success('已清除所有Token');
  };
  </script>
  
  <style scoped>
  .test-panel {
    max-width: 600px;
    margin: 2rem auto;
  }
  
  .ant-descriptions {
    margin-top: 1.5rem;
  }
  
  .ant-btn {
    width: 240px;
    justify-content: start;
  }
  </style>
  