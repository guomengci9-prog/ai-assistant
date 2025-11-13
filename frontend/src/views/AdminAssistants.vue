<template>
  <div class="admin-assistants-page">
    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>Assistant Prompt Management</h2>
          <p class="panel-subtitle">Edit system prompts, scene prompts, and opening messages</p>
        </div>
        <div class="header-actions">
          <el-button @click="openCreateDialog">New Assistant</el-button>
          <el-button type="primary" :loading="loading" @click="fetchAssistants">
            Refresh
          </el-button>
        </div>
      </div>

      <el-table
        :data="assistants"
        border
        v-loading="loading"
        empty-text="No assistants"
        class="assistants-table"
      >
        <el-table-column prop="name" label="Name" min-width="160" />
        <el-table-column label="Icon" width="80">
          <template #default="{ row }">
            <img v-if="row.icon" :src="row.icon" alt="icon" class="icon-thumb" />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="Description" min-width="220" show-overflow-tooltip />
        <el-table-column label="System Prompt" min-width="200">
          <template #default="{ row }">
            <span class="ellipsis">{{ row.system_prompt || 'Not set' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="update_time" label="Updated At" min-width="170">
          <template #default="{ row }">
            {{ formatDate(row.update_time) }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" min-width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDrawer(row)">Edit</el-button>
            <el-button type="danger" link @click="deleteAssistant(row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer
      v-model="drawerVisible"
      :title="editingAssistant?.name || 'Edit Prompts'"
      size="40%"
      destroy-on-close
    >
      <el-form label-position="top" class="prompt-form" @submit.prevent>
        <el-form-item label="Name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="Icon URL">
          <el-input v-model="editForm.icon" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="editForm.description" />
        </el-form-item>
        <el-form-item label="System Prompt">
          <el-input
            v-model="editForm.system_prompt"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="For example: You are a professional consultant..."
          />
        </el-form-item>
        <el-form-item label="Scene Prompt">
          <el-input
            v-model="editForm.scene_prompt"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="Describe the scene or use case"
          />
        </el-form-item>
        <el-form-item label="User Prefill">
          <el-input
            v-model="editForm.user_prefill"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="Shown above the chat input"
          />
        </el-form-item>
        <el-form-item label="Opening Message">
          <el-input
            v-model="editForm.opening_message"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
        </el-form-item>
        <el-form-item label="Default Prompt (legacy)">
          <el-input
            v-model="editForm.prompt_content"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 5 }"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">Cancel</el-button>
          <el-button type="primary" :loading="saving" @click="savePrompts">
            Save
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>

  <el-dialog
    v-model="createDialogVisible"
    title="Create Assistant"
    width="520px"
    destroy-on-close
  >
    <el-form label-width="110px" :model="createForm" @submit.prevent>
      <el-form-item label="Name" required>
        <el-input v-model="createForm.name" placeholder="Assistant name" />
      </el-form-item>
      <el-form-item label="Icon URL">
        <el-input v-model="createForm.icon" placeholder="https://..." />
      </el-form-item>
      <el-form-item label="Description">
        <el-input v-model="createForm.description" placeholder="Short introduction" />
      </el-form-item>
      <el-form-item label="System Prompt">
        <el-input
          v-model="createForm.system_prompt"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
      </el-form-item>
      <el-form-item label="Scene Prompt">
        <el-input
          v-model="createForm.scene_prompt"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
      </el-form-item>
      <el-form-item label="User Prefill">
        <el-input
          v-model="createForm.user_prefill"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 3 }"
        />
      </el-form-item>
      <el-form-item label="Opening Message">
        <el-input
          v-model="createForm.opening_message"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 3 }"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="createDialogVisible = false">Cancel</el-button>
        <el-button type="primary" :loading="createSaving" @click="saveNewAssistant">
          Create
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { getAdminAssistants, type UpdatePromptPayload } from '@/api'
import axios from 'axios'
import type { Assistant } from '@/types'

const assistants = ref<Assistant[]>([])
const loading = ref(false)

const drawerVisible = ref(false)
const saving = ref(false)
const editingAssistant = ref<Assistant | null>(null)
const editForm = reactive<UpdatePromptPayload & { name: string; icon: string; description: string; model_parameters: Record<string, unknown>; knowledge_ids: number[] }>({
  name: '',
  icon: '',
  description: '',
  prompt_content: '',
  system_prompt: '',
  scene_prompt: '',
  user_prefill: '',
  opening_message: '',
  model_parameters: {},
  knowledge_ids: []
})

const createDialogVisible = ref(false)
const createSaving = ref(false)
const createForm = reactive({
  name: '',
  icon: '',
  description: '',
  system_prompt: '',
  scene_prompt: '',
  user_prefill: '',
  opening_message: '',
  prompt_content: '',
  model_parameters: {},
  knowledge_ids: []
})

onMounted(() => {
  fetchAssistants()
})

async function fetchAssistants() {
  loading.value = true
  try {
    const res = await getAdminAssistants()
    assistants.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (error) {
    console.error('Failed to fetch assistants', error)
    ElMessage.error('Failed to fetch assistants')
  } finally {
    loading.value = false
  }
}

function openDrawer(assistant: Assistant) {
  editingAssistant.value = assistant
  Object.assign(editForm, {
    name: assistant.name || '',
    icon: assistant.icon || '',
    description: assistant.description || '',
    prompt_content: assistant.prompt_content || assistant.defaultPrompt || '',
    system_prompt: assistant.system_prompt || '',
    scene_prompt: assistant.scene_prompt || '',
    user_prefill: assistant.user_prefill || '',
    opening_message: assistant.opening_message || '',
    model_parameters: assistant.model_parameters || {},
    knowledge_ids: assistant.knowledge_ids || []
  })
  drawerVisible.value = true
}

async function savePrompts() {
  if (!editingAssistant.value) return
  saving.value = true
  try {
    await axios.put(`/admin/assistants/${editingAssistant.value.id}`, {
      ...editForm,
    })
    ElMessage.success('Assistant updated')
    drawerVisible.value = false
    fetchAssistants()
  } catch (error: any) {
    console.error('Failed to update assistant', error?.response?.data || error)
    ElMessage.error(parseErrorMessage(error) || 'Save failed, please try again later')
  } finally {
    saving.value = false
  }
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

async function deleteAssistant(assistant: Assistant) {
  try {
    await ElMessageBox.confirm(`Delete assistant "${assistant.name}"?`, 'Confirm', {
      type: 'warning',
    })
    await axios.delete(`/admin/assistants/${assistant.id}`)
    ElMessage.success('Assistant deleted')
    fetchAssistants()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete assistant', (error as any)?.response?.data || error)
      ElMessage.error(parseErrorMessage(error) || 'Delete failed')
    }
  }
}

function openCreateDialog() {
  Object.assign(createForm, {
    name: '',
    icon: '',
    description: '',
    system_prompt: '',
    scene_prompt: '',
    user_prefill: '',
    opening_message: '',
    prompt_content: ''
  })
  createDialogVisible.value = true
}

async function saveNewAssistant() {
  if (!createForm.name.trim()) {
    ElMessage.warning('Name is required')
    return
  }
  createSaving.value = true
  try {
    await axios.post('/admin/assistants', { ...createForm })
    ElMessage.success('Assistant created')
    createDialogVisible.value = false
    fetchAssistants()
  } catch (error) {
    console.error('Failed to create assistant', (error as any)?.response?.data || error)
    ElMessage.error(parseErrorMessage(error) || 'Create failed')
  } finally {
    createSaving.value = false
  }
}

function parseErrorMessage(error: any): string | undefined {
  const detail = error?.response?.data?.detail
  if (!detail) return undefined
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item: any) => item?.msg || item?.detail || JSON.stringify(item))
      .join('; ')
  }
  if (typeof detail === 'object') {
    return detail.msg || detail.detail || JSON.stringify(detail)
  }
  return undefined
}
</script>

<style scoped>
.admin-assistants-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(99, 123, 255, 0.12);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
}

.panel-subtitle {
  margin: 4px 0 0;
  color: #8c94ad;
  font-size: 13px;
}

.assistants-table .ellipsis {
  display: inline-block;
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.icon-thumb {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.prompt-form {
  padding: 8px 12px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
