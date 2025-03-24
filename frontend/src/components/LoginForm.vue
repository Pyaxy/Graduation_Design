<script setup>
import { reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue';

// 表单引用和响应式状态
const formRef = ref();
const formState = reactive({
  email: '',
  password: ''
});

// 验证规则配置
const rules = {
  email: [
    { 
      required: true,
      message: '请输入注册邮箱',
      trigger: 'blur'
    },
    {
      type: 'email',
      message: '邮箱格式不正确',
      trigger: ['blur', 'change']
    }
  ],
  password: [
    { 
      required: true,
      message: '请输入密码',
      trigger: 'blur'
    },
    {
      min: 8,
      message: '密码长度至少8位',
      trigger: 'blur'
    }
  ]
};

// 登录提交处理
const loading = ref(false);
const handleLogin = async () => {
  try {
    // 先进行表单验证
    await formRef.value.validate();
    
    loading.value = true;
    const response = await axios.post('http://localhost:8000/accounts/login/', {
      email: formState.email,
      password: formState.password
    }, {
      headers: { 'Content-Type': 'application/json' }
    });

    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    message.success('登录成功，正在跳转...');
    // 后续添加路由跳转逻辑
    
  } catch (error) {
    if (error.errorFields) {
      // 表单验证错误
      message.error('请正确填写登录信息');
    } else {
      // API请求错误
      handleApiError(error);
    }
  } finally {
    loading.value = false;
  }
};

// 错误处理函数
const handleApiError = (error) => {
  let errorMessage = '登录失败';
  if (error.response?.status === 401) {
    errorMessage = '邮箱或密码错误';
  } else if (error.response) {
    errorMessage = `服务器错误：${error.response.status}`;
  }
  message.error(errorMessage);
};

// 重置表单
// const resetForm = () => {
//   formRef.value.resetFields();
// };
</script>

<template>
  <div class="login-container">
    <a-card title="CodeCollab 登录" class="login-card">
      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        layout="vertical"
        @keypress.enter="handleLogin"
      >
        <a-form-item name="email">
          <template #label>
            <span class="form-label">邮箱</span>
          </template>
          <a-input
            v-model:value="formState.email"
            placeholder="user@example.com"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <template #label>
            <span class="form-label">密码</span>
          </template>
          <a-input-password
            v-model:value="formState.password"
            placeholder="至少8位密码"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            block
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '立即登录' }}
          </a-button>
          <!-- <a-button block style="margin-top: 10px" @click="resetForm">
            重置表单
          </a-button> -->
        </a-form-item>
      </a-form>

      <div class="additional-actions">
        <router-link to="/register">新用户注册</router-link>
        <router-link to="/forgot-password" class="forgot-password">
          忘记密码？
        </router-link>
      </div>
    </a-card>
  </div>
</template>

<style scoped>
/* 保持原有样式不变 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.login-card {
  width: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.additional-actions {
  margin-top: 24px;
  display: flex;
  justify-content: space-between;
}

.forgot-password {
  color: #1890ff;
}

.form-label {
  font-weight: 500;
}
</style>
