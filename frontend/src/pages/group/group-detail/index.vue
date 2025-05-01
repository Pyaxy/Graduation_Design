<script lang="ts" setup>
import type { GroupData, GroupCodeVersionList, GroupCodeVersionResponse, GroupCodeVersion, GroupCodeFile } from "./apis/type"
import CourseSubjectList from "@/pages/course/course-detail/components/CourseSubjectList.vue"
import { useUserStore } from "@/pinia/stores/user"
import { ElForm, ElMessage } from "element-plus"
import hljs from "highlight.js"
import { storeToRefs } from "pinia"
import { ref, onMounted, computed, h } from "vue"
import { useRoute, useRouter } from "vue-router"
import { createGroupCodeVersion, getGroupDetail, listGroupCodeVersions, selectSubject, unselectSubject, getGroupCodeVersion } from "./apis"
import "highlight.js/styles/github.css"
import { defineComponent, PropType } from "vue"
import { Document, ArrowDown, ArrowRight } from "@element-plus/icons-vue"
import FileTreeNode from "./components/FileTreeNode.vue"
import dayjs from "dayjs"

const route = useRoute()
const router = useRouter()
const courseId = route.params.courseId as string
const groupId = route.params.groupId as string
const loading = ref(false)
const groupInfo = ref<GroupData | null>(null)

// 用户角色
const userStore = useUserStore()
const { role: userRole } = storeToRefs(userStore)

const versionDialogVisible = ref(false)
const versionForm = ref({
  version: "",
  description: "",
  zipFile: null as File | null
})
const versionFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const versions = ref<Array<{ id: string, version: string }>>([])

const selectedVersion = ref<string>("")
const fileTree = ref<FileNode[]>([])
const selectedFile = ref<FileNode | null>(null)
const highlightedContent = ref("")
const versionDetail = ref<GroupCodeVersion | null>(null)

interface FileNode {
  name: string
  children?: FileNode[]
  path: string
  content?: string
  is_previewable?: boolean
  size?: number
  isLeaf?: boolean
}

const treeProps = {
  label: "name",
  children: "children"
}

// 获取小组详情
function getGroupDetailData() {
  loading.value = true
  return getGroupDetail(groupId)
    .then(({ data }) => {
      groupInfo.value = data
    })
    .finally(() => {
      loading.value = false
    })
}

// 处理选题
function handleSelectSubject(subjectId: string) {
  loading.value = true
  selectSubject(groupId, subjectId)
    .then(() => {
      ElMessage.success("选题成功")
      getGroupDetailData()
    })
    .catch((error: any) => {
      if (error.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error("选题失败")
      }
    })
    .finally(() => {
      loading.value = false
    })
}

// 处理退选
function handleUnselectSubject() {
  loading.value = true
  unselectSubject(groupId)
    .then(() => {
      ElMessage.success("退选成功")
      getGroupDetailData()
    })
    .catch((error: any) => {
      if (error.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error("退选失败")
      }
    })
    .finally(() => {
      loading.value = false
    })
}

function handleCreateVersion() {
  if (!versionFormRef.value) return

  versionFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      const formData = new FormData()
      formData.append("version", versionForm.value.version)
      formData.append("description", versionForm.value.description)
      if (versionForm.value.zipFile) {
        formData.append("zip_file", versionForm.value.zipFile)
      }

      try {
        await createGroupCodeVersion(groupId, formData)
        ElMessage.success("版本创建成功")
        versionDialogVisible.value = false
        versionForm.value = { version: "", description: "", zipFile: null }
        fetchVersions()
      } catch (error: any) {
        ElMessage.error(error.message || "版本创建失败")
      }
    }
  })
}

async function fetchVersions() {
  try {
    const response = await listGroupCodeVersions(groupId)
    if (response.data) {
      versions.value = response.data.results
    }
  } catch {
    ElMessage.error("获取版本列表失败")
  }
}

function handleViewVersion(version: any) {
  // TODO: 实现查看版本详情
  console.log("查看版本:", version)
}

async function fetchVersionFiles(versionId: string) {
  try {
    const response = await getGroupCodeVersion(groupId, versionId)
    if (response.data) {
      versionDetail.value = response.data
      fileTree.value = buildFileTree(response.data.files)
    }
  } catch {
    ElMessage.error("获取版本详情失败")
  }
}

function buildFileTree(files: GroupCodeFile[]) {
  const tree: FileNode[] = []
  const pathMap: Record<string, FileNode> = {}

  files.forEach((file) => {
    const pathParts = file.path.split("/")
    let currentPath = ""
    let currentNode = tree

    pathParts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part

      if (!pathMap[currentPath]) {
        const newNode: FileNode = {
          name: part,
          path: currentPath,
          children: [],
          isLeaf: index === pathParts.length - 1,
          ...(index === pathParts.length - 1
            ? {
                content: file.content || "",
                is_previewable: file.is_previewable,
                size: file.size
              }
            : {})
        }

        pathMap[currentPath] = newNode
        currentNode.push(newNode)
      }

      currentNode = pathMap[currentPath].children || []
    })
  })

  return tree
}

function handleFileClick(node: FileNode) {
  // 如果是文件夹，不进行任何操作
  if (!node.isLeaf) {
    return
  }

  // 只有文件才进行预览
  if (node.is_previewable) {
    selectedFile.value = node
    highlightedContent.value = hljs.highlightAuto(node.content || "").value
  } else {
    selectedFile.value = node
  }
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB", "TB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${Number.parseFloat((bytes / (k ** i)).toFixed(2))} ${sizes[i]}`
}

// 当前路径
const currentPath = computed(() => {
  if (!selectedFile.value) return []
  return selectedFile.value.path?.split("/") || []
})

onMounted(() => {
  getGroupDetailData()
  fetchVersions()
})
</script>

<template>
  <div class="app-container">
    <!-- 小组基本信息卡片 -->
    <el-card v-loading="loading" shadow="never" class="group-info-card">
      <template v-if="groupInfo">
        <div class="group-header">
          <h2>{{ groupInfo.name }}</h2>
          <div class="group-stats">
            <el-tag type="info">成员数：{{ groupInfo.students.length }}/{{ groupInfo.max_students }}</el-tag>
          </div>
        </div>
        <div class="group-meta">
          <div class="meta-item">
            <span class="label">课程ID：</span>
            <span class="value">{{ groupInfo.course }}</span>
          </div>
          <div class="meta-item">
            <span class="label">组长：</span>
            <span class="value">{{ groupInfo.creator.name }}</span>
            <el-tag size="small" type="success">{{ groupInfo.creator.role_display }}</el-tag>
          </div>
          <div class="meta-item">
            <span class="label">创建时间：</span>
            <span class="value">{{ groupInfo.created_at }}</span>
          </div>
          <div class="meta-item">
            <span class="label">更新时间：</span>
            <span class="value">{{ groupInfo.updated_at }}</span>
          </div>
        </div>
      </template>
    </el-card>

    <!-- 导航标签页 -->
    <el-card shadow="never" class="nav-card">
      <el-tabs>
        <el-tab-pane label="成员列表">
          <div class="tab-content">
            <el-table v-if="groupInfo" :data="groupInfo.students">
              <el-table-column prop="user_id" label="学号" align="center" />
              <el-table-column prop="name" label="姓名" align="center" />
              <el-table-column prop="role_display" label="角色" align="center">
                <template #default="scope">
                  <el-tag v-if="scope.row.user_id === groupInfo.creator.user_id" type="success">
                    组长
                  </el-tag>
                  <el-tag v-else type="info">
                    {{ scope.row.role_display }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        <el-tab-pane label="选题信息">
          <div class="tab-content">
            <template v-if="groupInfo?.group_subjects?.length > 0">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="课题名称">
                  {{ groupInfo.group_subjects[0].course_subject.subject.title }}
                </el-descriptions-item>
                <el-descriptions-item label="课题描述">
                  {{ groupInfo.group_subjects[0].course_subject.subject.description }}
                </el-descriptions-item>
                <el-descriptions-item label="课题类型">
                  <el-tag :type="groupInfo.group_subjects[0].course_subject.subject_type === 'PUBLIC' ? 'success' : 'warning'">
                    {{ groupInfo.group_subjects[0].course_subject.subject_type === 'PUBLIC' ? '公开课题' : '私有课题' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="编程语言">
                  <el-tag v-for="lang in groupInfo.group_subjects[0].course_subject.subject.languages" :key="lang" class="mr-2">
                    {{ lang }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建者">
                  {{ groupInfo.group_subjects[0].course_subject.subject.creator.name }}
                  <el-tag size="small" type="info" class="ml-2">
                    {{ groupInfo.group_subjects[0].course_subject.subject.creator.role_display }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="选题时间">
                  {{ groupInfo.group_subjects[0].created_at }}
                </el-descriptions-item>
                <el-descriptions-item>
                  <el-button type="danger" @click="handleUnselectSubject">退选课题</el-button>
                </el-descriptions-item>
              </el-descriptions>
            </template>
            <template v-else>
              <el-empty description="暂未选题" />
              <div class="select-subject-wrapper">
                <h3>可选课题列表</h3>
                <CourseSubjectList
                  :course-id="courseId"
                  :show-select-button="true"
                  @select="handleSelectSubject"
                />
              </div>
            </template>
          </div>
        </el-tab-pane>
        <el-tab-pane label="代码版本" name="code-version">
          <div class="tab-content">
            <div class="version-header">
              <el-select v-model="selectedVersion" placeholder="选择版本" @change="fetchVersionFiles">
                <el-option
                  v-for="version in versions"
                  :key="version.id"
                  :label="version.version"
                  :value="version.id"
                />
              </el-select>
              <el-button type="primary" @click="versionDialogVisible = true">创建新版本</el-button>
            </div>

            <div v-if="versionDetail" class="version-info">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="版本号">{{ versionDetail.version }}</el-descriptions-item>
                <el-descriptions-item label="描述">{{ versionDetail.description }}</el-descriptions-item>
                <el-descriptions-item label="文件总数">{{ versionDetail.total_files }}</el-descriptions-item>
                <el-descriptions-item label="总大小">{{ formatFileSize(versionDetail.total_size) }}</el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ dayjs(versionDetail.created_at).format('YYYY-MM-DD HH:mm:ss') }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="file-browser">
              <div class="file-tree-container">
                <div class="file-tree-header">
                  <el-breadcrumb>
                    <el-breadcrumb-item v-for="(item, index) in currentPath" :key="index">
                      {{ item }}
                    </el-breadcrumb-item>
                  </el-breadcrumb>
                </div>
                <div class="file-tree">
                  <FileTreeNode
                    v-for="node in fileTree"
                    :key="node.path"
                    :node="node"
                    @select="handleFileClick"
                  />
                </div>
              </div>
              <div class="file-preview-container">
                <div v-if="selectedFile" class="file-preview">
                  <div class="file-preview-header">
                    <div class="file-info">
                      <el-icon><Document /></el-icon>
                      <span>{{ selectedFile.name }}</span>
                      <el-tag size="small" type="info">{{ formatFileSize(selectedFile.size || 0) }}</el-tag>
                    </div>
                  </div>
                  <div class="file-content">
                    <div v-if="selectedFile.is_previewable" class="code-preview">
                      <pre><code v-html="highlightedContent"></code></pre>
                    </div>
                    <div v-else class="file-meta">
                      <el-icon><Document /></el-icon>
                      <p>文件不可预览</p>
                      <p>大小: {{ formatFileSize(selectedFile.size || 0) }}</p>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-preview">
                  <el-empty description="请选择文件" />
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建版本对话框 -->
    <el-dialog v-model="versionDialogVisible" title="创建新版本" width="50%">
      <el-form :model="versionForm" ref="versionFormRef" label-width="120px">
        <el-form-item label="版本号" prop="version" :rules="[{ required: true, message: '请输入版本号', trigger: 'blur' }]">
          <el-input v-model="versionForm.version" placeholder="请输入版本号" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="versionForm.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="上传ZIP文件" prop="zipFile" :rules="[{ required: true, message: '请上传ZIP文件', trigger: 'change' }]">
          <el-upload
            action=""
            :auto-upload="false"
            :on-change="(file: any) => (versionForm.zipFile = file.raw)"
            :file-list="[]"
            accept=".zip"
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="versionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateVersion">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.app-container {
  padding: 20px;
}

.group-info-card {
  margin-bottom: 20px;

  .group-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      margin-right: 16px;
    }
  }

  .group-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    margin-bottom: 16px;

    .meta-item {
      display: flex;
      align-items: center;
      gap: 8px;

      .label {
        color: #606266;
      }
    }
  }
}

.nav-card {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
}

.tab-content {
  padding: 20px 0;
}

:deep(.el-tabs__nav-wrap) {
  margin-bottom: 20px;
}

.mr-2 {
  margin-right: 8px;
}

.ml-2 {
  margin-left: 8px;
}

.select-subject-wrapper {
  margin-top: 20px;

  h3 {
    margin-bottom: 20px;
    font-size: 16px;
    font-weight: 500;
  }
}

.version-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.file-browser {
  display: flex;
  margin-top: 20px;
  height: calc(100vh - 400px);
  gap: 20px;
}

.file-tree-container {
  width: 300px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .file-tree-header {
    padding: 10px;
    border-bottom: 1px solid #ebeef5;
  }

  .file-tree {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
  }
}

.file-preview-container {
  flex: 1;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .file-preview {
    display: flex;
    flex-direction: column;
    height: 100%;

    .file-preview-header {
      padding: 10px;
      border-bottom: 1px solid #ebeef5;
      display: flex;
      align-items: center;

      .file-info {
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .file-content {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      background-color: #f9f9f9;

      .code-preview {
        pre {
          background: #f6f8fa;
          padding: 10px;
          border-radius: 4px;
          overflow-x: auto;
        }
      }

      .file-meta {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        gap: 16px;
        color: #909399;

        .el-icon {
          font-size: 48px;
        }
      }
    }
  }

  .empty-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
}

.file-tree-node {
  .node-content {
    display: flex;
    align-items: center;
    padding: 4px 8px;
    cursor: pointer;
    gap: 8px;

    &:hover {
      background-color: #f5f7fa;
    }

    .file-size {
      margin-left: auto;
      color: #909399;
      font-size: 12px;
    }
  }

  .node-children {
    margin-left: 16px;
  }
}

.version-info {
  margin: 20px 0;
}
</style>
