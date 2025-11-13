import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

interface AuthPayload {
  token: string
  account?: string
  role?: string
}

export const useAuthStore = defineStore(
  'auth',
  () => {
    const token = ref<string | null>(null)
    const account = ref<string | null>(null)
    const role = ref<string | null>(null)

    const isLoggedIn = computed(() => Boolean(token.value))
    const isAdmin = computed(() => role.value === 'admin')

    function applyAuthHeader(value: string | null) {
      if (value) {
        axios.defaults.headers.common.Authorization = `Bearer ${value}`
      } else {
        delete axios.defaults.headers.common.Authorization
      }
    }

    watch(
      token,
      value => {
        applyAuthHeader(value)
      },
      { immediate: true }
    )

    function setAuth(payload: AuthPayload) {
      token.value = payload.token
      account.value = payload.account ?? null
      role.value = payload.role ?? null
    }

    function clearAuth(options?: { keepAccount?: boolean }) {
      token.value = null
      role.value = null
      if (!options?.keepAccount) {
        account.value = null
      }
    }

    return {
      token,
      account,
      role,
      isLoggedIn,
      isAdmin,
      setAuth,
      clearAuth,
    }
  },
  {
    persist: true,
  }
)
