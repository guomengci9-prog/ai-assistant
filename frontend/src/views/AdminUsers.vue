<template>
  <div class="admin-users-page">
    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>User Management</h2>
          <p class="panel-subtitle">Create, edit, delete users and reset passwords</p>
        </div>
        <el-button type="primary" @click="openUserDialog()">New User</el-button>
      </div>

      <el-table
        :data="users"
        border
        v-loading="loading"
        empty-text="No users"
        class="users-table"
      >
        <el-table-column prop="username" label="Username" min-width="140" />
        <el-table-column prop="email" label="Email" min-width="180" />
        <el-table-column prop="role" label="Role" width="110" />
        <el-table-column prop="create_time" label="Created At" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" min-width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openUserDialog(row)">Edit</el-button>
            <el-button type="warning" link @click="resetPassword(row)">Reset Password</el-button>
            <el-button type="danger" link @click="deleteUser(row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingUser ? 'Edit User' : 'Create User'"
      width="420px"
      destroy-on-close
    >
      <el-form :model="userForm" label-width="80px" @submit.prevent>
        <el-form-item label="Username" required>
          <el-input v-model="userForm.username" :disabled="Boolean(editingUser)" autocomplete="off" />
        </el-form-item>

        <el-form-item label="Password" :required="!editingUser">
          <el-input
            v-model="userForm.password"
            type="password"
            autocomplete="new-password"
            placeholder="Leave empty to keep current"
          />
        </el-form-item>

        <el-form-item label="Email">
          <el-input v-model="userForm.email" autocomplete="off" />
        </el-form-item>

        <el-form-item label="Role">
          <el-select v-model="userForm.role" placeholder="Select role">
            <el-option label="User" value="user" />
            <el-option label="Admin" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" :loading="dialogSaving" @click="saveUser">Save</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

interface UserItem {
  username: string
  email?: string
  role: string
  create_time?: string
}

const users = ref<UserItem[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const dialogSaving = ref(false)
const editingUser = ref<UserItem | null>(null)

const userForm = reactive({
  username: '',
  password: '',
  email: '',
  role: 'user',
})

onMounted(fetchUsers)

async function fetchUsers() {
  loading.value = true
  try {
    const res = await axios.get('/admin/users')
    users.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (err) {
    console.error(err)
    ElMessage.error('Failed to load users')
  } finally {
    loading.value = false
  }
}

function openUserDialog(user?: UserItem) {
  editingUser.value = user || null
  userForm.username = user?.username || ''
  userForm.password = ''
  userForm.email = user?.email || ''
  userForm.role = user?.role || 'user'
  dialogVisible.value = true
}

async function saveUser() {
  if (!userForm.username.trim()) {
    ElMessage.warning('Username is required')
    return
  }
  if (!editingUser.value && !userForm.password.trim()) {
    ElMessage.warning('Password is required for new users')
    return
  }

  dialogSaving.value = true
  try {
    if (editingUser.value) {
      const normalizedEmail = userForm.email.trim()
      await axios.put(`/admin/users/${editingUser.value.username}`, {
        email: normalizedEmail === '' ? null : normalizedEmail,
        role: userForm.role,
      })
      if (userForm.password.trim()) {
        await axios.post(`/admin/users/${editingUser.value.username}/reset_password`, {
          new_password: userForm.password,
        })
      }
      ElMessage.success('User updated')
    } else {
      await axios.post('/admin/users', {
        username: userForm.username,
        password: userForm.password,
        email: userForm.email || undefined,
        role: userForm.role,
      })
      ElMessage.success('User created')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (err) {
    console.error(err)
    ElMessage.error('Save failed')
  } finally {
    dialogSaving.value = false
  }
}

async function resetPassword(user: UserItem) {
  try {
    const { value } = await ElMessageBox.prompt('Enter new password', 'Reset Password', {
      inputType: 'password',
      confirmButtonText: 'Confirm',
      cancelButtonText: 'Cancel',
    })
    if (!value) return
    await axios.post(`/admin/users/${user.username}/reset_password`, {
      new_password: value,
    })
    ElMessage.success('Password reset')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('Reset failed')
    }
  }
}

async function deleteUser(user: UserItem) {
  try {
    await ElMessageBox.confirm(`Delete user "${user.username}"?`, 'Confirm', {
      type: 'warning',
    })
    await axios.delete(`/admin/users/${user.username}`)
    ElMessage.success('Deleted')
    fetchUsers()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('Delete failed')
    }
  }
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
.admin-users-page {
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

.panel-header h2 {
  margin: 0;
  font-size: 20px;
}

.panel-subtitle {
  margin: 4px 0 0;
  color: #8c94ad;
  font-size: 13px;
}

.users-table {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
