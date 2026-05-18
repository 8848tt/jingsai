import { defineStore } from 'pinia'
import api from '../api/http'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loaded: true,
  }),
  actions: {
    async fetchMe() {
      try {
        const { data } = await api.get('/auth/me/')
        this.user = data
      } catch {
        this.user = null
      }
    },
    async login(username, password) {
      await api.post('/auth/login/', { username, password })
      await this.fetchMe()
    },
    async register(payload) {
      await api.post('/auth/register/', payload)
      await this.fetchMe()
    },
    async logout() {
      await api.post('/auth/logout/')
      this.user = null
    },
  },
})
