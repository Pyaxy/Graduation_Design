<script lang="ts" setup>
import type { FormInstance, FormRules } from "element-plus"
import { ElMessage } from "element-plus"
import { ref } from "vue"
import { useRouter } from "vue-router"
import { registerApi } from "./apis"

const router = useRouter()
const registerFormRef = ref<FormInstance>()

const registerForm = ref({
  email: "",
  password: "",
  confirmPassword: "",
  user_id: "",
  name: "",
  school: ""
})

const rules = ref<FormRules>({
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱地址", trigger: "blur" }
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 20, message: "密码长度在 6 到 20 个字符", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.value.password) {
          callback(new Error("两次输入的密码不一致"))
        } else {
          callback()
        }
      },
      trigger: "blur"
    }
  ],
  user_id: [
    { required: true, message: "请输入学号/工号", trigger: "blur" },
    { min: 2, max: 20, message: "请输入正确的学号/工号", trigger: "blur" }
  ],
  name: [
    { required: true, message: "请输入姓名", trigger: "blur" },
    { min: 2, max: 20, message: "姓名长度在 2 到 20 个字符", trigger: "blur" }
  ],
  school: [
    { required: true, message: "请输入学校", trigger: "blur" },
    { min: 2, max: 50, message: "学校长度在 2 到 50 个字符", trigger: "blur" }
  ]
})

/** 提交注册 */
async function handleRegister() {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await registerApi({
          email: registerForm.value.email,
          password: registerForm.value.password,
          confirm_password: registerForm.value.confirmPassword,
          user_id: registerForm.value.user_id,
          name: registerForm.value.name,
          school: registerForm.value.school,
          role: "STUDENT"
        })
        ElMessage.success("注册成功")
        router.push("/login")
      } catch (error: any) {
        // 错误消息已在axios拦截器中处理，不需要再次显示
        console.error("注册失败:", error)
      }
    }
  })
}

/** 返回登录页 */
function goToLogin() {
  router.push("/login")
}
</script>

<template>
  <div class="register-container">
    <div class="register-box">
      <h2>用户注册</h2>
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="rules"
        label-width="100px"
        class="register-form"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请确认密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="学号/工号" prop="user_id">
          <el-input v-model="registerForm.user_id" placeholder="请输入学号/工号" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="registerForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="学校" prop="school">
          <el-input v-model="registerForm.school" placeholder="请输入学校" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRegister">注册</el-button>
          <el-button @click="goToLogin">返回登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--el-bg-color-page);

  .register-box {
    width: 400px;
    padding: 40px;
    background-color: var(--el-bg-color);
    border-radius: 8px;
    box-shadow: var(--el-box-shadow-light);

    h2 {
      text-align: center;
      margin-bottom: 30px;
      color: var(--el-text-color-primary);
    }

    .register-form {
      .el-form-item {
        margin-bottom: 25px;
      }

      .el-button {
        width: 100%;
        margin-bottom: 10px;
      }
    }
  }
}
</style>
