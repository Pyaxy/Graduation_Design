<script lang="ts" setup>
import type { SubjectData } from "@/pages/subject/apis/type"
import type { FormInstance } from "element-plus"
import { addSubjectToCourse } from "@/pages/course/apis"
import { getSubjectList } from "@/pages/subject/apis"
import { usePagination } from "@@/composables/usePagination"
import { CirclePlus, Download, Refresh, RefreshRight, Search } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const props = defineProps<{
  courseId: string
  courseInfo: any
}>()

const emit = defineEmits<{
  (e: "refresh"): void
}>()

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// #region 查
const tableData = ref<SubjectData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  search: "",
  status: "" as "PENDING" | "APPROVED" | "REJECTED" | "",
  languages: [] as string[]
})

const languageOptions = [
  { label: "Python", value: "PYTHON" },
  { label: "Java", value: "JAVA" },
  { label: "C++", value: "CPP" },
  { label: "C", value: "C" }
]

// 选中的课题
const selectedSubjects = ref<SubjectData[]>([])

function getSubjectData() {
  loading.value = true
  getSubjectList({
    page: paginationData.currentPage,
    page_size: paginationData.pageSize,
    search: searchData.search,
    status: searchData.status,
    languages: searchData.languages.join(",")
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
  searchData.languages = []
  handleSearch()
}

// 处理课题选择
function handleSelectionChange(selection: SubjectData[]) {
  selectedSubjects.value = selection
}

// 添加选中的课题到课程
function handleAddSubjects() {
  if (selectedSubjects.value.length === 0) {
    ElMessage.warning("请选择要添加的课题")
    return
  }

  loading.value = true
  addSubjectToCourse(props.courseId, {
    subject_ids: selectedSubjects.value.map(subject => subject.id).join(","),
    subject_type: "PRIVATE"
  })
    .then(({ data }) => {
      if (data.success.count > 0) {
        ElMessage.success(`成功添加 ${data.success.count} 个课题`)
      }
      if (data.failed.count > 0) {
        ElMessage.error(`添加失败 ${data.failed.count} 个课题：${data.failed.details.map(detail => `\n课题 ${detail.id}: ${detail.reason}`).join("")}`)
      }
      emit("refresh")
    })
    .finally(() => {
      loading.value = false
    })
}

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getSubjectData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="search" label="课题标题或简介">
          <el-input v-model="searchData.search" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="languages" label="编程语言">
          <el-select
            v-model="searchData.languages"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="option in languageOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item prop="status" label="审核状态">
          <el-select v-model="searchData.status" placeholder="请选择" clearable style="width: 200px">
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
          <el-button type="primary" :loading="loading" @click="handleAddSubjects">
            添加选中课题
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
        <el-table
          :data="tableData"
          @selection-change="handleSelectionChange"
          class="subject-table"
          stripe
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column prop="title" label="课题标题" align="center" />
          <el-table-column prop="description" label="课题描述" align="center" />
          <el-table-column prop="creator.name" label="创建人" align="center" />
          <el-table-column prop="languages" label="适用语言" align="center">
            <template #default="scope">
              <el-tag
                v-for="lang in scope.row.languages"
                :key="lang"
                class="mx-1"
                type="success"
                effect="plain"
              >
                {{ languageOptions.find(opt => opt.value === lang)?.label }}
              </el-tag>
            </template>
          </el-table-column>
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

.mx-1 {
  margin: 0 4px;
}
</style>
