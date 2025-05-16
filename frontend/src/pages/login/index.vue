<script lang="ts" setup>
import type { FormInstance, FormRules } from "element-plus"
import type { LoginRequestData } from "./apis/type"
import { useSettingsStore } from "@/pinia/stores/settings"
import { useUserStore } from "@/pinia/stores/user"
import ThemeSwitch from "@@/components/ThemeSwitch/index.vue"
import { Lock, User } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"
import { useRouter } from "vue-router"
import { loginApi } from "./apis"
import Owl from "./components/Owl.vue"
import { useFocus } from "./composables/useFocus"
import { usePermissionStore } from "@/pinia/stores/permission"
import { routerConfig } from "@/router/config"

const router = useRouter()
const userStore = useUserStore()
const settingsStore = useSettingsStore()
const { isFocus, handleBlur, handleFocus } = useFocus()

/** 登录表单元素的引用 */
const loginFormRef = ref<FormInstance>()

/** 登录按钮 Loading */
const loading = ref(false)

/** 登录表单数据 */
const loginFormData: LoginRequestData = reactive({
  email: "",
  password: ""
})

/** 登录表单校验规则 */
const loginFormRules: FormRules = {
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" }
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 8, max: 16, message: "长度在 8 到 16 个字符", trigger: "blur" }
  ]
}

/** 登录 */
async function handleLogin() {
  loginFormRef.value?.validate(async (valid) => {
    if (!valid) {
      return
    }
    try {
      loading.value = true
      const response = await loginApi(loginFormData)
      // 设置 token
      userStore.setAccessToken(response.data.access)
      userStore.setRefreshToken(response.data.refresh)
      // 设置用户信息
      userStore.setUserInfo({
        user_id: response.data.user_id,
        role: response.data.role,
        name: response.data.name
      })
      // 获取用户信息
      await userStore.getInfo()
      // 获取权限信息，主要用于生成可访问的路由
      const permissionStore = usePermissionStore()
      // 等待 permission store 初始化
      await new Promise(resolve => setTimeout(resolve, 200))
      // 设置路由
      routerConfig.dynamic ? permissionStore.setRoutes(userStore.roles) : permissionStore.setAllRoutes()
      // 只添加动态路由到路由实例中
      permissionStore.addRoutes.forEach(route => {
        if (!router.hasRoute(route.name as string)) {
          router.addRoute(route)
        }
      })
      // 跳转到首页
      router.push("/")
    } catch (error) {
      ElMessage.error((error as Error).message || "登录失败")
    } finally {
      loading.value = false
    }
  }).catch(() => {
    // 表单验证失败
  })
}
</script>

<template>
  <div class="login-container">
    <ThemeSwitch v-if="settingsStore.showThemeSwitch" class="theme-switch" />
    <Owl v-if="isFocus" :close-eyes="isFocus" />
    <div class="login-box">
      <div class="login-title">
        <h2>CodeCollab</h2>
      </div>
      <el-form
        ref="loginFormRef"
        :model="loginFormData"
        :rules="loginFormRules"
        class="login-form"
      >
        <el-form-item prop="email">
          <el-input
            v-model="loginFormData.email"
            placeholder="邮箱"
            :prefix-icon="User"
            @focus="handleFocus"
            @blur="handleBlur"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginFormData.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            @focus="handleFocus"
            @blur="handleBlur"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            :loading="loading"
            type="primary"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--el-color-primary-light-3) 0%, var(--el-color-primary) 100%);

  .theme-switch {
    position: fixed;
    top: 5%;
    right: 5%;
    cursor: pointer;
    z-index: 1;
  }

  .login-box {
    width: 400px;
    padding: 40px;
    border-radius: 16px;
    background: var(--el-bg-color);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);

    .login-title {
      text-align: center;
      margin-bottom: 40px;

      h2 {
        font-size: 28px;
        color: var(--el-text-color-primary);
        margin: 0;
        font-weight: 600;
      }
    }

    .login-form {
      .el-form-item {
        margin-bottom: 25px;
      }

      .el-input {
        --el-input-height: 44px;

        :deep(.el-input__wrapper) {
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

          &:hover {
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
          }
        }
      }

      .login-button {
        width: 100%;
        height: 44px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 500;
        margin-top: 10px;
        background: var(--el-color-primary);
        border: none;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(var(--el-color-primary-rgb), 0.3);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }
  }
}
</style>
