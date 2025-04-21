<script lang="ts" setup>
import type { FormInstance, FormRules, UploadFile } from "element-plus"
import type { CreateOrUpdateSubjectRequestData, SubjectData } from "./apis/type"
import { useUserStore } from "@/pinia/stores/user"
import { usePagination } from "@@/composables/usePagination"
import { CirclePlus, Delete, Download, Refresh, RefreshRight, Search } from "@element-plus/icons-vue"
import { cloneDeep } from "lodash-es"
import { storeToRefs } from "pinia"
import { useRouter } from "vue-router"
import { applyPublicSubject, createSubjectApi, deleteSubject, getSubjectList, reviewPublicSubject, reviewSubject, updateSubject } from "./apis/index"

defineOptions({
  name: "Subject"
})
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// #region 查看详情
const router = useRouter()

function handleViewDetail(row: SubjectData) {
  router.push(`subject-detail/${row.id}`)
}
// #endregion

// #region 增
const DEFAULT_FORM_DATA: CreateOrUpdateSubjectRequestData = {
  id: undefined,
  title: "",
  description: "",
  max_students: 1
}
const dialogVisible = ref<boolean>(false)
const formRef = ref<FormInstance | null>(null)
const formData = ref<CreateOrUpdateSubjectRequestData>(cloneDeep(DEFAULT_FORM_DATA))
const descriptionFile = ref<File | null>(null)
const formRules: FormRules<CreateOrUpdateSubjectRequestData> = {
  title: [{ required: true, trigger: "blur", message: "请输入课题标题" }],
  description: [{ required: true, trigger: "blur", message: "请输入课题描述" }],
  max_students: [{ required: true, trigger: "blur", message: "请输入最大学生数" }]
}

function handleCreateOrUpdate() {
  formRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    loading.value = true
    const formDataObj = new FormData()
    Object.entries(formData.value).forEach(([key, value]) => {
      if (value !== undefined) {
        formDataObj.append(key, value.toString())
      }
    })
    if (descriptionFile.value) {
      formDataObj.append("description_file", descriptionFile.value)
    }

    const promise = formData.value.id === undefined
      ? createSubjectApi(formDataObj)
      : updateSubject(formData.value.id, formDataObj)

    promise
      .then(() => {
        ElMessage.success("操作成功")
        dialogVisible.value = false
        getSubjectData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}

function resetForm() {
  formRef.value?.clearValidate()
  formData.value = cloneDeep(DEFAULT_FORM_DATA)
  descriptionFile.value = null
}

function handleFileChange(uploadFile: UploadFile) {
  if (uploadFile.raw) {
    descriptionFile.value = uploadFile.raw
  }
}
// #endregion

// #region 删
function handleDelete(row: SubjectData) {
  ElMessageBox.confirm(`正在删除课题：${row.title}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteSubject(row.id).then(() => {
      ElMessage.success("删除成功")
      getSubjectData()
    })
  })
}
// #endregion

// #region 改
function handleUpdate(row: SubjectData) {
  dialogVisible.value = true
  formData.value = cloneDeep({
    id: row.id,
    title: row.title,
    description: row.description,
    max_students: row.max_students
  })
}
// #endregion

// #region 查
const tableData = ref<SubjectData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  search: "",
  status: "" as "PENDING" | "APPROVED" | "REJECTED" | "",
  public_status: "" as "NOT_APPLIED" | "PENDING" | "APPROVED" | "REJECTED" | ""
})

function getSubjectData() {
  loading.value = true
  getSubjectList({
    page: paginationData.currentPage,
    page_size: paginationData.pageSize,
    ...searchData
  })
    .then(({ data }) => {
      paginationData.total = data.count
      tableData.value = data.results
    })
    .catch(() => {
      tableData.value = []
      paginationData.total = 0
    })
    .finally(() => {
      loading.value = false
    })
}

function handleSearch() {
  paginationData.currentPage === 1 ? getSubjectData() : (paginationData.currentPage = 1)
}

function resetSearch() {
  searchFormRef.value?.resetFields()
  searchData.search = ""
  searchData.status = ""
  searchData.public_status = ""
  handleSearch()
}
// #endregion

// #region 审核
const reviewDialogVisible = ref<boolean>(false)
const reviewFormRef = ref<FormInstance | null>(null)
const reviewData = reactive({
  id: 0 as number,
  status: "APPROVED" as "APPROVED" | "REJECTED",
  review_comments: "" as string
})

function handleReview(row: SubjectData) {
  reviewDialogVisible.value = true
  reviewData.id = row.id
}

function submitReview() {
  reviewFormRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    loading.value = true
    reviewSubject(reviewData.id, {
      status: reviewData.status,
      review_comments: reviewData.review_comments
    })
      .then(() => {
        ElMessage.success("审核成功")
        reviewDialogVisible.value = false
        getSubjectData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}
// #endregion

// #region 公开审核
const publicReviewDialogVisible = ref<boolean>(false)
const publicReviewFormRef = ref<FormInstance | null>(null)
const publicReviewData = reactive({
  id: 0 as number,
  public_status: "APPROVED" as "APPROVED" | "REJECTED",
  public_review_comments: "" as string
})

function handleApplyPublic(row: SubjectData) {
  ElMessageBox.confirm(`确定要申请公开课题：${row.title}？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    loading.value = true
    applyPublicSubject(row.id)
      .then(() => {
        ElMessage.success("申请成功")
        getSubjectData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}

function handlePublicReview(row: SubjectData) {
  publicReviewDialogVisible.value = true
  publicReviewData.id = row.id
}

function submitPublicReview() {
  publicReviewFormRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    loading.value = true
    reviewPublicSubject(publicReviewData.id, {
      public_status: publicReviewData.public_status,
      public_review_comments: publicReviewData.public_review_comments
    })
      .then(() => {
        ElMessage.success("审核成功")
        publicReviewDialogVisible.value = false
        getSubjectData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}
// #endregion

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getSubjectData, { immediate: true })
onMounted(() => {
  console.log(userRole.value)
})
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="search" label="课题标题或简介">
          <el-input v-model="searchData.search" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="status" label="审核状态">
          <el-select v-model="searchData.status" placeholder="请选择" clearable style="width: 200px">
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已拒绝" value="REJECTED" />
          </el-select>
        </el-form-item>
        <el-form-item prop="public_status" label="公开状态">
          <el-select v-model="searchData.public_status" placeholder="请选择" clearable style="width: 200px">
            <el-option label="未申请" value="NOT_APPLIED" />
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已拒绝" value="REJECTED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            查询
          </el-button>
          <el-button :icon="Refresh" @click="resetSearch">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card v-loading="loading" shadow="never">
      <div class="toolbar-wrapper">
        <div>
          <el-button type="primary" :icon="CirclePlus" @click="dialogVisible = true">
            新增课题
          </el-button>
        </div>
        <div>
          <el-tooltip content="下载">
            <el-button type="primary" :icon="Download" circle />
          </el-tooltip>
          <el-tooltip content="刷新当前页">
            <el-button type="primary" :icon="RefreshRight" circle @click="getSubjectData" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table :data="tableData">
          <el-table-column prop="title" label="课题标题" align="center" />
          <el-table-column prop="description" label="课题描述" align="center" />
          <el-table-column prop="creator.name" label="创建人" align="center" />
          <el-table-column prop="max_students" label="最大学生数" align="center" />
          <el-table-column prop="status_display" label="审核状态" align="center">
            <template #default="scope">
              <el-tag v-if="scope.row.status === 'APPROVED'" type="success" effect="plain">
                {{ scope.row.status_display }}
              </el-tag>
              <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" effect="plain">
                {{ scope.row.status_display }}
              </el-tag>
              <el-tag v-else type="warning" effect="plain">
                {{ scope.row.status_display }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="public_status_display" label="公开状态" align="center">
            <template #default="scope">
              <el-tag v-if="scope.row.public_status === 'APPROVED'" type="success" effect="plain">
                {{ scope.row.public_status_display }}
              </el-tag>
              <el-tag v-else-if="scope.row.public_status === 'REJECTED'" type="danger" effect="plain">
                {{ scope.row.public_status_display }}
              </el-tag>
              <el-tag v-else-if="scope.row.public_status === 'PENDING'" type="warning" effect="plain">
                {{ scope.row.public_status_display }}
              </el-tag>
              <el-tag v-else type="info" effect="plain">
                {{ scope.row.public_status_display }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" align="center" />
          <el-table-column fixed="right" label="操作" width="350" align="center">
            <template #default="scope">
              <el-button type="primary" text bg size="small" @click="handleViewDetail(scope.row)">
                查看
              </el-button>
              <el-button v-if="['ADMIN', 'TEACHER'].includes(userRole)" type="primary" text bg size="small" @click="handleUpdate(scope.row)">
                修改
              </el-button>
              <el-button v-if="userRole === 'ADMIN'" type="success" text bg size="small" @click="handleReview(scope.row)">
                审核
              </el-button>
              <el-button
                v-if="userRole === 'TEACHER' && scope.row.status === 'APPROVED' && scope.row.public_status === 'NOT_APPLIED'"
                type="primary"
                text
                bg
                size="small"
                @click="handleApplyPublic(scope.row)"
              >
                申请公开
              </el-button>
              <el-button
                v-if="userRole === 'ADMIN' && scope.row.public_status === 'PENDING'"
                type="success"
                text
                bg
                size="small"
                @click="handlePublicReview(scope.row)"
              >
                审核公开
              </el-button>
              <el-button v-if="['ADMIN', 'TEACHER'].includes(userRole)" type="danger" text bg size="small" @click="handleDelete(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pager-wrapper">
        <el-pagination
          background
          :layout="paginationData.layout"
          :page-sizes="paginationData.pageSizes"
          :total="paginationData.total"
          :page-size="paginationData.pageSize"
          :current-page="paginationData.currentPage"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/修改对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="formData.id === undefined ? '新增课题' : '修改课题'"
      width="50%"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="title" label="课题标题">
          <el-input v-model="formData.title" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="description" label="课题描述">
          <el-input v-model="formData.description" type="textarea" :rows="4" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="description_file" label="课题文件">
          <el-upload
            class="upload-demo"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            @change="handleFileChange"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item prop="max_students" label="最大学生数">
          <el-input-number v-model="formData.max_students" :min="1" :max="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="loading" @click="handleCreateOrUpdate">
          确认
        </el-button>
      </template>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog v-model="reviewDialogVisible" title="课题审核" width="50%">
      <el-form ref="reviewFormRef" :model="reviewData" label-width="100px" label-position="left">
        <el-form-item prop="status" label="审核结果">
          <el-radio-group v-model="reviewData.status">
            <el-radio label="APPROVED">通过</el-radio>
            <el-radio label="REJECTED">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item prop="review_comments" label="审核意见">
          <el-input v-model="reviewData.review_comments" type="textarea" :rows="4" placeholder="请输入审核意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="loading" @click="submitReview">
          确认
        </el-button>
      </template>
    </el-dialog>

    <!-- 公开审核对话框 -->
    <el-dialog v-model="publicReviewDialogVisible" title="公开审核" width="50%">
      <el-form ref="publicReviewFormRef" :model="publicReviewData" label-width="100px" label-position="left">
        <el-form-item prop="public_status" label="审核结果">
          <el-radio-group v-model="publicReviewData.public_status">
            <el-radio label="APPROVED">通过</el-radio>
            <el-radio label="REJECTED">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item prop="public_review_comments" label="审核意见">
          <el-input v-model="publicReviewData.public_review_comments" type="textarea" :rows="4" placeholder="请输入审核意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publicReviewDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="loading" @click="submitPublicReview">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.search-wrapper {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding-bottom: 2px;
  }
}

.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.table-wrapper {
  margin-bottom: 20px;
}

.pager-wrapper {
  display: flex;
  justify-content: flex-end;
}
</style>
