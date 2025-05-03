<script lang="ts" setup>
import type { FileNode } from "../apis/type"
import { Document, ArrowDown, ArrowRight } from "@element-plus/icons-vue"
import { ref, computed } from "vue"

const props = defineProps<{
  node: FileNode
}>()

const emit = defineEmits<{
  (e: "select", node: FileNode): void
}>()

const isExpanded = ref(false)
const hasChildren = computed(() => (props.node.children?.length || 0) > 0)

const toggleExpand = () => {
  if (hasChildren.value) {
    isExpanded.value = !isExpanded.value
  }
}

const handleClick = () => {
  if (hasChildren.value) {
    toggleExpand()
  } else {
    emit("select", props.node)
  }
}
</script>

<template>
  <div class="file-tree-node">
    <div class="node-content" @click="handleClick">
      <el-icon v-if="hasChildren" @click.stop="toggleExpand">
        <component :is="isExpanded ? ArrowDown : ArrowRight" />
      </el-icon>
      <el-icon v-else>
        <Document />
      </el-icon>
      <span>{{ node.name }}</span>
      <span v-if="node.isLeaf" class="file-size">{{ formatFileSize(node.size || 0) }}</span>
    </div>
    <div v-if="hasChildren && isExpanded" class="node-children">
      <FileTreeNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        @select="emit('select', $event)"
      />
    </div>
  </div>
</template>

<script lang="ts">
// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB", "TB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${Number.parseFloat((bytes / (k ** i)).toFixed(2))} ${sizes[i]}`
}
</script>

<style lang="scss" scoped>
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
</style>
