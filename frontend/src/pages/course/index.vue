<script lang="ts" setup>
import type { FormInstance, FormRules } from "element-plus"
import type { CreateOrUpdateCourseRequestData, CourseData } from "./apis/type"
import { useUserStore } from "@/pinia/stores/user"
import { usePagination } from "@@/composables/usePagination"
import { CirclePlus, Delete, Download, Refresh, RefreshRight, Search } from "@element-plus/icons-vue"
import dayjs from "dayjs"
import { cloneDeep } from "lodash-es"
import { storeToRefs } from "pinia"
import { useRouter } from "vue-router"
import { createCourse, deleteCourse, getCourseList, joinCourse, leaveCourse, updateCourse } from "./apis"

defineOptions({
  name: "Course"
})
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// #region 查看详情
const router = useRouter()

function handleViewDetail(row: CourseData) {
  router.push(`course-detail/${row.id}`)
}
// #endregion

// #region 增
const DEFAULT_FORM_DATA: CreateOrUpdateCourseRequestData = {
  id: undefined,
  name: "",
  description: "",
  start_date: "",
  end_date: ""
}
const dialogVisible = ref<boolean>(false)
const formRef = ref<FormInstance | null>(null)
const formData = ref<CreateOrUpdateCourseRequestData>(cloneDeep(DEFAULT_FORM_DATA))
const formRules: FormRules<CreateOrUpdateCourseRequestData> = {
  name: [{ required: true, trigger: "blur", message: "请输入课程名称" }],
  description: [],
  start_date: [{ required: true, trigger: "blur", message: "请选择开始日期" }],
  end_date: [{ required: true, trigger: "blur", message: "请选择结束日期" }]
}

function handleCreateOrUpdate() {
  formRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    loading.value = true
    const formDataObj = new FormData()
    const processedData = {
      ...formData.value,
      start_date: dayjs(formData.value.start_date).format("YYYY-MM-DD"),
      end_date: dayjs(formData.value.end_date).format("YYYY-MM-DD")
    }
    Object.entries(processedData).forEach(([key, value]) => {
      if (value !== undefined) {
        formDataObj.append(key, value.toString())
      }
    })

    const promise = formData.value.id === undefined
      ? createCourse(formDataObj)
      : updateCourse(formData.value.id, formDataObj)

    promise
      .then(() => {
        ElMessage.success("操作成功")
        dialogVisible.value = false
        getCourseData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}

function resetForm() {
  formRef.value?.clearValidate()
  formData.value = cloneDeep(DEFAULT_FORM_DATA)
}
// #endregion

// #region 删
function handleDelete(row: CourseData) {
  ElMessageBox.confirm(`正在删除课程：${row.name}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteCourse(row.id).then(() => {
      ElMessage.success("删除成功")
      getCourseData()
    })
  })
}
// #endregion

// #region 改
function handleUpdate(row: CourseData) {
  dialogVisible.value = true
  formData.value = cloneDeep({
    id: row.id,
    name: row.name,
    description: row.description,
    start_date: row.start_date,
    end_date: row.end_date
  })
}
// #endregion

// #region 查
const tableData = ref<CourseData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  search: "",
  status: "" as "not_started" | "in_progress" | "completed" | ""
})

function getCourseData() {
  loading.value = true
  getCourseList({
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
  paginationData.currentPage === 1 ? getCourseData() : (paginationData.currentPage = 1)
}

function resetSearch() {
  searchFormRef.value?.resetFields()
  searchData.search = ""
  searchData.status = ""
  handleSearch()
}
// #endregion

// #region 加入/退出课程
const joinDialogVisible = ref<boolean>(false)
const joinFormRef = ref<FormInstance | null>(null)
const joinData = reactive({
  course_code: ""
})

function handleJoin() {
  joinDialogVisible.value = true
}

function submitJoin() {
  joinFormRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    loading.value = true
    joinCourse(joinData)
      .then(() => {
        ElMessage.success("加入成功")
        joinDialogVisible.value = false
        getCourseData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}

function handleLeave(row: CourseData) {
  ElMessageBox.confirm(`正在退出课程：${row.name}，确认退出？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    leaveCourse(row.id).then(() => {
      ElMessage.success("退出成功")
      getCourseData()
    })
  })
}
// #endregion

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getCourseData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="search" label="课程名称或课程码">
          <el-input v-model="searchData.search" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="status" label="状态">
          <el-select v-model="searchData.status" placeholder="请选择" clearable style="width: 200px">
            <el-option label="未开始" value="not_started" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已结束" value="completed" />
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
          <el-button v-if="['ADMIN', 'TEACHER'].includes(userRole)" type="primary" :icon="CirclePlus" @click="dialogVisible = true">
            新增课程
          </el-button>
          <el-button v-if="userRole === 'STUDENT'" type="primary" :icon="CirclePlus" @click="handleJoin">
            加入课程
          </el-button>
        </div>
        <div>
          <el-tooltip content="下载">
            <el-button type="primary" :icon="Download" circle />
          </el-tooltip>
          <el-tooltip content="刷新当前页">
            <el-button type="primary" :icon="RefreshRight" circle @click="getCourseData" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table :data="tableData">
          <el-table-column prop="name" label="课程名称" align="center" />
          <el-table-column prop="description" label="课程描述" align="center" />
          <el-table-column prop="teacher.name" label="教师" align="center" />
          <el-table-column prop="course_code" label="课程码" align="center" />
          <el-table-column prop="status" label="状态" align="center">
            <template #default="scope">
              <el-tag v-if="scope.row.status === 'in_progress'" type="success" effect="plain">
                进行中
              </el-tag>
              <el-tag v-else-if="scope.row.status === 'completed'" type="info" effect="plain">
                已结束
              </el-tag>
              <el-tag v-else type="warning" effect="plain">
                未开始
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_date" label="开始日期" align="center" />
          <el-table-column prop="end_date" label="结束日期" align="center" />
          <el-table-column fixed="right" label="操作" width="250" align="center">
            <template #default="scope">
              <el-button type="primary" text bg size="small" @click="handleViewDetail(scope.row)">
                查看
              </el-button>
              <el-button v-if="['ADMIN', 'TEACHER'].includes(userRole)" type="primary" text bg size="small" @click="handleUpdate(scope.row)">
                修改
              </el-button>
              <el-button v-if="userRole === 'STUDENT'" type="danger" text bg size="small" @click="handleLeave(scope.row)">
                退出
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
      :title="formData.id === undefined ? '新增课程' : '修改课程'"
      width="50%"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="name" label="课程名称">
          <el-input v-model="formData.name" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="description" label="课程描述">
          <el-input v-model="formData.description" type="textarea" :rows="4" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="start_date" label="开始日期">
          <el-date-picker
            v-model="formData.start_date"
            type="date"
            placeholder="请选择"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item prop="end_date" label="结束日期">
          <el-date-picker
            v-model="formData.end_date"
            type="date"
            placeholder="请选择"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
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

    <!-- 加入课程对话框 -->
    <el-dialog v-model="joinDialogVisible" title="加入课程" width="50%">
      <el-form ref="joinFormRef" :model="joinData" label-width="100px" label-position="left">
        <el-form-item prop="course_code" label="课程码">
          <el-input v-model="joinData.course_code" placeholder="请输入课程码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="joinDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="loading" @click="submitJoin">
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
