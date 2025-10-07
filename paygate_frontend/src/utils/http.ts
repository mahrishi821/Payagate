import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

class ApiClient {
  private axios: AxiosInstance
  private accessToken: string | null = null

  constructor() {
    this.axios = axios.create({
      withCredentials: true,
    })

    this.axios.interceptors.request.use((config) => {
      if (this.accessToken) {
        config.headers = config.headers ?? {}
        config.headers['Authorization'] = `Bearer ${this.accessToken}`
      }
      return config
    })

    this.axios.interceptors.response.use(
      (res) => res,
      async (error) => {
        const original: AxiosRequestConfig & { _retry?: boolean } = error.config || {}
        if (error.response?.status === 401 && !original._retry) {
          original._retry = true
          try {
            const refreshRes = await this.axios.post('/paygate/api/v1/auth/refresh/', {}, { withCredentials: true })
            const newAccess = refreshRes.data.access as string
            this.setAccessToken(newAccess)
            original.headers = original.headers ?? {}
            original.headers['Authorization'] = `Bearer ${newAccess}`
            return this.axios.request(original)
          } catch (e) {
            return Promise.reject(e)
          }
        }
        return Promise.reject(error)
      }
    )
  }

  setAccessToken(token: string | null) { this.accessToken = token }

  get urlBase() { return '' }

  get(path: string, config?: AxiosRequestConfig) { return this.axios.get(path, config) }
  post(path: string, data?: any, config?: AxiosRequestConfig) { return this.axios.post(path, data, config) }
}

export const api = new ApiClient()




