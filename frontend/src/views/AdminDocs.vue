<template>
  <div class="admin-docs-page">
    <section class="panel upload-panel">
      <div class="panel-header">
        <h2>上传知识库文档</h2>
        <p class="panel-subtitle">支持为助手绑定文档并配置解析参数</p>
      </div>

      <el-form label-position="top" class="upload-form" @submit.prevent>
        <el-form-item label="选择文件" required>
          <input
            ref="fileInputRef"
            class="file-input"
            type="file"
            @change="handleFileChange"
            accept=".pdf,.doc,.docx,.txt,.md,.csv,.json,.xlsx,.ppt,.pptx"
          />
          <p v-if="selectedFileName" class="file-hint">已选：{{ selectedFileName }}</p>
        </el-form-item>

        <el-form-item label="绑定助手（可选）">
          <el-select
            v-model="uploadForm.assistantId"
            filterable
            clearable
            placeholder="选择助手"
            :loading="assistantLoading"
          >
            <el-option
              v-for="assistant in assistants"
              :key="assistant.id"
              :label="assistant.name"
              :value="assistant.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="文档描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="可选：说明文档用途，方便管理员区分"
          />
        </el-form-item>

        <el-form-item label="解析参数（JSON，可选）">
          <el-input
            v-model="uploadForm.parameters"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 5 }"
            placeholder='例如 {"chunk_size": 400, "embedding": "text-embedding"}'
          />
        </el-form-item>

        <div class="form-actions">
          <el-button type="primary" :loading="uploading" @click="submitUpload">
            上传文档
          </el-button>
          <el-button @click="resetUploadForm" :disabled="uploading">重置</el-button>
        </div>
      </el-form>
    </section>

    <section class="panel table-panel">
      <div class="panel-header">
        <div>
          <h2>文档列表</h2>
          <p class="panel-subtitle">查看上传记录，执行解析或删除操作</p>
        </div>
        <el-button type="primary" :loading="loadingDocs" @click="fetchDocs">
          刷新列表
        </el-button>
      </div>

      <el-table
        :data="docs"
        border
        v-loading="loadingDocs"
        class="docs-table"
        empty-text="暂无上传记录"
      >
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column label="绑定助手" min-width="150">
          <template #default="{ row }">
            <span v-if="row.assistant_id">
              {{ getAssistantName(row.assistant_id) }}
            </span>
            <span v-else class="text-muted">未绑定</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.parse_status)">
              {{ renderStatus(row.parse_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" min-width="90">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button
              size="small"
              text
              type="success"
              :loading="parseLoadingId === row.id"
              @click="handleParse(row.id)"
            >
              解析
            </el-button>
            <el-button
              size="small"
              text
              type="danger"
              :loading="deleteLoadingId === row.id"
              @click="handleDelete(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="editDialogVisible" title="编辑文档信息" width="480px">
      <el-form label-width="100px" @submit.prevent>
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
        </el-form-item>
        <el-form-item label="绑定助手">
          <el-select
            v-model="editForm.assistant_id"
            clearable
            filterable
            placeholder="选择助手"
          >
            <el-option
              v-for="assistant in assistants"
              :key="assistant.id"
              :label="assistant.name"
              :value="assistant.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="解析参数（JSON）">
          <el-input
            v-model="editForm.parameters"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="editSaving" @click="submitEdit">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminDocs,
  uploadAdminDoc,
  parseAdminDoc,
  deleteAdminDoc,
  updateAdminDoc,
  getAdminAssistants
} from '@/api'

interface DocumentItem {
  id: number
  name: string
  assistant_id?: number | null
  parse_status: string
  file_size: number
  upload_time?: string
  description?: string
  parameters?: Record<string, unknown>
}

interface AssistantItem {
  id: number
  name: string
}

const docs = ref<DocumentItem[]>([])
const assistants = ref<AssistantItem[]>([])
const loadingDocs = ref(false)
const assistantLoading = ref(false)

const uploadForm = reactive({
  assistantId: null as number | null,
  description: '',
  parameters: ''
})

const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const selectedFileName = ref('')
const uploading = ref(false)

const parseLoadingId = ref<number | null>(null)
const deleteLoadingId = ref<number | null>(null)

const editDialogVisible = ref(false)
const editSaving = ref(false)
const editForm = reactive({
  id: 0,
  name: '',
  description: '',
  assistant_id: null as number | null,
  parameters: ''
})

onMounted(() => {
  fetchDocs()
  fetchAssistants()
})

async function fetchDocs() {
  loadingDocs.value = true
  try {
    const res = await getAdminDocs()
    docs.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (error) {
    console.error(error)
    ElMessage.error('获取文档列表失败')
  } finally {
    loadingDocs.value = false
  }
}

async function fetchAssistants() {
  assistantLoading.value = true
  try {
    const res = await getAdminAssistants()
    assistants.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (error) {
    console.error(error)
    ElMessage.error('获取助手列表失败')
  } finally {
    assistantLoading.value = false
  }
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  selectedFile.value = file || null
  selectedFileName.value = file?.name || ''
}

function resetUploadForm() {
  uploadForm.assistantId = null
  uploadForm.description = ''
  uploadForm.parameters = ''
  selectedFile.value = null
  selectedFileName.value = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

async function submitUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择需要上传的文件')
    return
  }

  let parametersPayload = ''
  if (uploadForm.parameters.trim()) {
    try {
      JSON.parse(uploadForm.parameters)
      parametersPayload = uploadForm.parameters.trim()
    } catch (error) {
      ElMessage.error('解析参数必须是合法的 JSON')
      return
    }
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  if (uploadForm.assistantId) {
    formData.append('assistant_id', String(uploadForm.assistantId))
  }
  if (uploadForm.description.trim()) {
    formData.append('description', uploadForm.description.trim())
  }
  if (parametersPayload) {
    formData.append('parameters', parametersPayload)
  }

  uploading.value = true
  try {
    await uploadAdminDoc(formData)
    ElMessage.success('上传成功')
    resetUploadForm()
    fetchDocs()
  } catch (error) {
    console.error(error)
    ElMessage.error('上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
}

async function handleParse(docId: number) {
  parseLoadingId.value = docId
  try {
    await parseAdminDoc(docId)
    ElMessage.success('解析任务已触发')
    fetchDocs()
  } catch (error) {
    console.error(error)
    ElMessage.error('解析失败')
  } finally {
    parseLoadingId.value = null
  }
}

async function handleDelete(docId: number) {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？操作不可恢复', '提示', {
      type: 'warning'
    })
  } catch {
    return
  }

  deleteLoadingId.value = docId
  try {
    await deleteAdminDoc(docId)
    ElMessage.success('删除成功')
    fetchDocs()
  } catch (error) {
    console.error(error)
    ElMessage.error('删除失败')
  } finally {
    deleteLoadingId.value = null
  }
}

function openEditDialog(row: DocumentItem) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description || ''
  editForm.assistant_id = row.assistant_id ?? null
  editForm.parameters = row.parameters ? JSON.stringify(row.parameters, null, 2) : ''
  editDialogVisible.value = true
}

async function submitEdit() {
  if (!editForm.id) return

  let paramsPayload: Record<string, unknown> | undefined
  if (editForm.parameters.trim()) {
    try {
      paramsPayload = JSON.parse(editForm.parameters)
    } catch (error) {
      ElMessage.error('解析参数需为合法 JSON')
      return
    }
  }

  editSaving.value = true
  try {
    await updateAdminDoc(editForm.id, {
      name: editForm.name,
      description: editForm.description,
      assistant_id: editForm.assistant_id || undefined,
      parameters: paramsPayload
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchDocs()
  } catch (error) {
    console.error(error)
    ElMessage.error('保存失败')
  } finally {
    editSaving.value = false
  }
}

function getAssistantName(id: number) {
  return assistants.value.find(item => item.id === id)?.name || `#${id}`
}

function statusTagType(status: string) {
  switch (status) {
    case 'parsed':
      return 'success'
    case 'uploaded':
      return 'info'
    case 'missing_file':
      return 'warning'
    default:
      return 'info'
  }
}

function renderStatus(status: string) {
  const map: Record<string, string> = {
    parsed: '已解析',
    uploaded: '已上传',
    unparsed: '未解析',
    missing_file: '文件缺失'
  }
  return map[status] || status || '未知'
}

function formatSize(size: number) {
  if (!size || size <= 0) return '-'
  if (size < 1024) return `${size}B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)}KB`
  return `${(size / 1024 / 1024).toFixed(1)}MB`
}

function formatDate(value?: string) {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}
</script>

<style scoped>
.admin-docs-page {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  padding: 16px;
}

.panel {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(99, 123, 255, 0.12);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.panel-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2a44;
}

.panel-subtitle {
  margin: 4px 0 0;
  color: #8c94ad;
  font-size: 13px;
}

.upload-form {
  flex: 1;
}

.file-input {
  width: 100%;
}

.file-hint {
  margin-top: 6px;
  color: #59627a;
  font-size: 13px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.table-panel {
  overflow: hidden;
}

.docs-table {
  flex: 1;
}

.text-muted {
  color: #9ba3bc;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 960px) {
  .admin-docs-page {
    grid-template-columns: 1fr;
  }
}
</style>
