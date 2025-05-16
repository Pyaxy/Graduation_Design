<script lang="ts" setup>
import type { FormInstance } from "element-plus"
import type { PublicSubjectData } from "../apis/type"
import { useUserStore } from "@/pinia/stores/user"
import { usePagination } from "@@/composables/usePagination"
import { Download, Refresh, RefreshRight, Search } from "@element-plus/icons-vue"
import { storeToRefs } from "pinia"
import { useRouter } from "vue-router"
import { getPublicSubjectList } from "../apis/index"

defineOptions({
  name: "PublicSubjects"
})

const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)
const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const router = useRouter()

// #region 查看详情
function handleViewDetail(row: PublicSubjectData) {
  router.push(`/code_week/subject-detail/${row.id}?isPublic=true`)
}
// #endregion

// #region 查
const tableData = ref<PublicSubjectData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  search: "",
  languages: [] as string[]
})

const languageOptions = [
  { label: "Python", value: "PYTHON" },
  { label: "Java", value: "JAVA" },
  { label: "C++", value: "CPP" },
  { label: "C", value: "C" }
]

function getSubjectData() {
  loading.value = true
  getPublicSubjectList({
    page: paginationData.currentPage,
    page_size: paginationData.pageSize,
    search: searchData.search,
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
  searchData.languages = []
  handleSearch()
}
// #endregion

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
          <el-table-column prop="description" label="课题描述" align="center">
            <template #default="scope">
              <el-tooltip
                :content="scope.row.description"
                placement="top"
                :show-after="500"
              >
                <span class="description-text">{{ scope.row.description }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
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
          <el-table-column prop="created_at" label="公开时间" align="center" />
          <el-table-column prop="version" label="版本" align="center" />
          <el-table-column fixed="right" label="操作" width="120" align="center">
            <template #default="scope">
              <el-button type="primary" text bg size="small" @click="handleViewDetail(scope.row)">
                查看
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
  justify-content: flex-end;
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

.description-text {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
