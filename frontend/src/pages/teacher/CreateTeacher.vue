<script setup lang="ts">
import type { FormInstance, FormRules } from "element-plus"
import { registerApi } from "@/pages/register/apis"
import { ElMessage } from "element-plus"
import { reactive, ref } from "vue"

const formRef = ref<FormInstance>()

const form = reactive({
  email: "",
  teacherId: "",
  name: "",
  school: ""
})

const rules = reactive<FormRules>({
  email: [
    { required: true, message: "请输入邮箱地址", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱地址", trigger: "blur" }
  ],
  teacherId: [
    { required: true, message: "请输入工号", trigger: "blur" }
  ],
  name: [
    { required: true, message: "请输入姓名", trigger: "blur" }
  ],
  school: [
    { required: true, message: "请输入学校名称", trigger: "blur" }
  ]
})

function submitForm() {
  if (!formRef.value) return

  formRef.value.validate(async (valid) => {
    if (valid) {
      await registerApi({
        email: form.email,
        password: form.teacherId,
        confirm_password: form.teacherId,
        user_id: form.teacherId,
        name: form.name,
        school: form.school,
        role: "TEACHER"
      })
      ElMessage.success("教师账号创建成功！")
      resetForm()
    }
  })
}

function resetForm() {
  if (!formRef.value) return
  formRef.value.resetFields()
}
</script>

<template>
  <div class="create-teacher-container">
    <!-- TODO: 美化样式 -->
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>创建教师账号</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="teacher-form"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入教师邮箱" />
        </el-form-item>

        <el-form-item label="工号" prop="teacherId">
          <el-input v-model="form.teacherId" placeholder="请输入教师工号" />
        </el-form-item>

        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入教师姓名" />
        </el-form-item>

        <el-form-item label="学校" prop="school">
          <el-input v-model="form.school" placeholder="请输入学校名称" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="submitForm">创建账号</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.create-teacher-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.teacher-form {
  margin-top: 20px;
}
</style>
