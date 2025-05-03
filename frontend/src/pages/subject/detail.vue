<script lang="ts" setup>
import { useUserStore } from "@/pinia/stores/user"
import { ArrowLeft } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"
import { computed, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getPublicSubjectDetail, getSubjectDetail } from "./apis"

defineOptions({
  name: "SubjectDetail"
})

const route = useRoute()
const router = useRouter()
const loading = ref<boolean>(false)
const subjectDetail = ref<any>(null)
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

const isPublic = computed(() => route.query.isPublic === "true")

const languageOptions = [
  { label: "Python", value: "PYTHON" },
  { label: "Java", value: "JAVA" },
  { label: "C++", value: "CPP" },
  { label: "C", value: "C" }
]

// 获取课题详情
function getDetail() {
  const id = route.params.id

  if (!id) {
    ElMessage.error("课题ID不存在")
    router.push("/code_week/subject-list")
    return
  }

  loading.value = true
  if (isPublic.value) {
    getPublicSubjectDetail(Number(id))
      .then(({ data }) => {
        subjectDetail.value = data
      })
      .catch(() => {
        ElMessage.error("获取课题详情失败")
        router.push("/code_week/subject-list")
      })
      .finally(() => {
        loading.value = false
      })
  } else {
    getSubjectDetail(Number(id))
      .then(({ data }) => {
        subjectDetail.value = data
      })
      .catch(() => {
        ElMessage.error("获取课题详情失败")
        router.push("/code_week/subject-list")
      })
      .finally(() => {
        loading.value = false
      })
  }
}

// 返回列表页
function handleBack() {
  router.push("/code_week/subject-list")
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
        <el-descriptions :column="2" border>
          <el-descriptions-item label="课题标题" :span="2">
            <span class="title">{{ subjectDetail?.title }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="课题描述" :span="2">
            <div class="description">{{ subjectDetail?.description }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="适用语言" :span="2">
            <el-tag
              v-for="lang in subjectDetail?.languages"
              :key="lang"
              class="mx-1"
              type="success"
              effect="plain"
            >
              {{ languageOptions.find(opt => opt.value === lang)?.label }}
            </el-tag>
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
            <div class="user-info">
              <span>{{ subjectDetail?.creator?.name }}</span>
              <el-tag size="small" class="ml-2">
                {{ subjectDetail?.creator?.role_display }}
              </el-tag>
            </div>
          </el-descriptions-item>
          <template v-if="!isPublic">
            <el-descriptions-item label="审核状态">
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
            <el-descriptions-item label="公开状态">
              <el-tag
                v-if="subjectDetail?.public_status === 'APPROVED'"
                type="success"
                effect="plain"
              >
                {{ subjectDetail?.public_status_display }}
              </el-tag>
              <el-tag
                v-else-if="subjectDetail?.public_status === 'REJECTED'"
                type="danger"
                effect="plain"
              >
                {{ subjectDetail?.public_status_display }}
              </el-tag>
              <el-tag
                v-else-if="subjectDetail?.public_status === 'PENDING'"
                type="warning"
                effect="plain"
              >
                {{ subjectDetail?.public_status_display }}
              </el-tag>
              <el-tag v-else type="info" effect="plain">
                {{ subjectDetail?.public_status_display }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="审核人">
              <div class="user-info">
                <span>{{ subjectDetail?.reviewer?.name || "无" }}</span>
                <el-tag v-if="subjectDetail?.reviewer" size="small" class="ml-2">
                  {{ subjectDetail?.reviewer?.role_display }}
                </el-tag>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="审核意见">
              {{ subjectDetail?.review_comments || "无" }}
            </el-descriptions-item>
            <el-descriptions-item label="公开审核人">
              <div class="user-info">
                <span>{{ subjectDetail?.public_reviewer?.name || "无" }}</span>
                <el-tag v-if="subjectDetail?.public_reviewer" size="small" class="ml-2">
                  {{ subjectDetail?.public_reviewer?.role_display }}
                </el-tag>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="公开审核意见">
              {{ subjectDetail?.public_review_comments || "无" }}
            </el-descriptions-item>
          </template>
          <el-descriptions-item label="创建时间">
            {{ subjectDetail?.created_at }}
          </el-descriptions-item>
          <template v-if="!isPublic">
            <el-descriptions-item label="更新时间">
              {{ subjectDetail?.updated_at }}
            </el-descriptions-item>
          </template>
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
    font-size: 20px;
    font-weight: bold;
    color: var(--el-text-color-primary);
  }

  .description {
    white-space: pre-wrap;
    line-height: 1.6;
    color: var(--el-text-color-regular);
  }

  .user-info {
    display: flex;
    align-items: center;
  }

  .ml-2 {
    margin-left: 8px;
  }

  .mx-1 {
    margin: 0 4px;
  }

  :deep(.el-descriptions__label) {
    width: 120px;
    font-weight: bold;
  }

  :deep(.el-descriptions__content) {
    color: var(--el-text-color-regular);
  }
}
</style>
