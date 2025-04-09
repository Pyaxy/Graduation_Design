<script lang="ts" setup>
import type { FormInstance } from "element-plus"
import type { SubjectData } from "./apis/type"
import { usePagination } from "@@/composables/usePagination"
import { Refresh, Search } from "@element-plus/icons-vue"
import { getSubjectList } from "./apis"

defineOptions({
  name: "SubjectStudent"
})

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// #region 查
const tableData = ref<SubjectData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  search: "",
  status: "APPROVED"
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
          <el-tooltip content="刷新当前页">
            <el-button type="primary" :icon="Refresh" circle @click="getSubjectData" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table :data="tableData">
          <el-table-column prop="title" label="课题标题" align="center" />
          <el-table-column prop="description" label="课题描述" align="center" />
          <el-table-column prop="creator.name" label="创建人" align="center" />
          <el-table-column prop="max_students" label="最大学生数" align="center" />
          <el-table-column prop="status_display" label="状态" align="center">
            <template #default="scope">
              <el-tag type="success" effect="plain">
                {{ scope.row.status_display }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" align="center" />
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
</style>
