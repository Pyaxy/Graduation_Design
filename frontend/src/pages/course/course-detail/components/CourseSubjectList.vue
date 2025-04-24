<script lang="ts" setup>
import type { SubjectListResponse } from "../../apis/type"
import { useUserStore } from "@/pinia/stores/user"
import { usePagination } from "@@/composables/usePagination"
import { Delete, RefreshRight } from "@element-plus/icons-vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { storeToRefs } from "pinia"
import { onMounted, ref, watch } from "vue"
import { deleteSubjectFromCourse, getCourseSubjectList } from "../../apis"

const props = defineProps<{
  courseId: string
}>()

const _emit = defineEmits<{
  (e: "refresh"): void
}>()

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// 用户角色
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)
// 表格数据
const tableData = ref<SubjectListResponse["data"]["results"]>([])

// 获取课题列表数据
function getSubjectData() {
  loading.value = true
  window.console.log("开始获取课题列表数据")
  getCourseSubjectList(props.courseId, {
    page: paginationData.currentPage,
    page_size: paginationData.pageSize
  })
    .then((response) => {
      console.log("接口响应数据:", response)
      const data = response.data
      console.log("解析后的数据:", data)
      paginationData.total = data.count
      tableData.value = data.results
      console.log("设置后的表格数据:", tableData.value)
    })
    .catch((error) => {
      console.error("获取数据失败:", error)
      tableData.value = []
      paginationData.total = 0
    })
    .finally(() => {
      loading.value = false
    })
}

// 删除课题
function handleDelete(id: string) {
  ElMessageBox.confirm(
    "确定要删除这个课题吗？删除后无法恢复！",
    "删除确认",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
      center: true,
      showClose: false,
      closeOnClickModal: false,
      closeOnPressEscape: false
    }
  )
    .then(() => {
      loading.value = true
      deleteSubjectFromCourse(props.courseId, id)
        .then(() => {
          ElMessage.success("删除成功")
          getSubjectData()
          _emit("refresh")
        })
        .catch(() => {
          ElMessage.error("删除失败")
        })
        .finally(() => {
          loading.value = false
        })
    })
    .catch(() => {
      // 用户取消删除
    })
}

onMounted(() => {
  console.log("组件挂载，courseId:", props.courseId)
})

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getSubjectData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never">
      <div class="toolbar-wrapper">
        <div>
          <el-tooltip content="刷新当前页">
            <el-button type="primary" :icon="RefreshRight" circle @click="getSubjectData" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table :data="tableData" class="subject-table" stripe>
          <el-table-column label="ID" width="80" align="center">
            <template #default="scope">
              {{ scope.row.subject.id }}
            </template>
          </el-table-column>
          <el-table-column label="课题标题" align="center">
            <template #default="scope">
              {{ scope.row.subject.title }}
            </template>
          </el-table-column>
          <el-table-column label="课题描述" align="center">
            <template #default="scope">
              {{ scope.row.subject.description }}
            </template>
          </el-table-column>
          <el-table-column label="创建人" align="center">
            <template #default="scope">
              {{ scope.row.subject.creator.name }}
            </template>
          </el-table-column>
          <el-table-column label="适用语言" align="center">
            <template #default="scope">
              <el-tag
                v-for="lang in scope.row.subject.languages"
                :key="lang"
                class="mx-1"
                type="success"
                effect="plain"
              >
                {{ lang }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="课题类型" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.subject_type === 'PUBLIC' ? 'success' : 'warning'" effect="plain">
                {{ scope.row.subject_type === 'PUBLIC' ? '公共课题' : '私有课题' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="添加时间" align="center">
            <template #default="scope">
              {{ scope.row.created_at }}
            </template>
          </el-table-column>
          <el-table-column
            v-if="userRole === 'TEACHER' || userRole === 'ADMIN'"
            label="操作"
            width="120"
            align="center"
            fixed="right"
          >
            <template #default="scope">
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="handleDelete(scope.row.id)"
              />
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
</style>
