<script lang="ts" setup>
import { ArrowLeft } from "@element-plus/icons-vue"
import { onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getSubjectDetail } from "./apis"

defineOptions({
  name: "SubjectDetail"
})

const route = useRoute()
const router = useRouter()
const loading = ref<boolean>(false)
const subjectDetail = ref<any>(null)

// 获取课题详情
function getDetail() {
  const id = route.params.id
  if (!id) {
    ElMessage.error("课题ID不存在")
    router.push("/code_week/subject")
    return
  }

  loading.value = true
  getSubjectDetail(Number(id))
    .then(({ data }) => {
      subjectDetail.value = data
    })
    .catch(() => {
      ElMessage.error("获取课题详情失败")
      router.push("/code_week/subject")
    })
    .finally(() => {
      loading.value = false
    })
}

// 返回列表页
function handleBack() {
  router.push("/code_week/subject")
}

onMounted(() => {
  getDetail()
})
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never">
      <div class="header-wrapper">
        <el-button :icon="ArrowLeft" @click="handleBack">
          返回列表
        </el-button>
      </div>

      <div class="content-wrapper">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="课题标题">
            <span class="title">{{ subjectDetail?.title }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="课题描述">
            <div class="description">{{ subjectDetail?.description }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="课题文件">
            <el-link
              v-if="subjectDetail?.description_file_url"
              type="primary"
              :href="subjectDetail.description_file_url"
              target="_blank"
            >
              点击下载
            </el-link>
            <span v-else>无</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            {{ subjectDetail?.creator?.name }}
            <el-tag size="small" class="ml-2">
              {{ subjectDetail?.creator?.role_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最大学生数">
            {{ subjectDetail?.max_students }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag
              v-if="subjectDetail?.status === 'APPROVED'"
              type="success"
              effect="plain"
            >
              {{ subjectDetail?.status_display }}
            </el-tag>
            <el-tag
              v-else-if="subjectDetail?.status === 'REJECTED'"
              type="danger"
              effect="plain"
            >
              {{ subjectDetail?.status_display }}
            </el-tag>
            <el-tag v-else type="warning" effect="plain">
              {{ subjectDetail?.status_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="审核人">
            {{ subjectDetail?.reviewer?.name || "无" }}
            <el-tag v-if="subjectDetail?.reviewer" size="small" class="ml-2">
              {{ subjectDetail?.reviewer?.role_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="审核意见">
            {{ subjectDetail?.review_comments || "无" }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ subjectDetail?.created_at }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ subjectDetail?.updated_at }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.header-wrapper {
  margin-bottom: 20px;
}

.content-wrapper {
  .title {
    font-size: 18px;
    font-weight: bold;
  }

  .description {
    white-space: pre-wrap;
    line-height: 1.6;
  }

  .ml-2 {
    margin-left: 8px;
  }
}
</style>
