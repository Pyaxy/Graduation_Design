import type { AxiosInstance, AxiosRequestConfig } from "axios"
import { useUserStore } from "@/pinia/stores/user"
import { getToken } from "@@/utils/cache/cookies"
import axios from "axios"
import { get, merge } from "lodash-es"
import { refreshTokenApi } from "./apis"
/**
 * @name 刷新访问令牌
 * @description 调用 refreshTokenApi 刷新访问令牌
 * @returns {Promise<AxiosResponse<any>>} 返回刷新后的访问令牌
 */
async function refreshAccessToken() {
  const userStore = useUserStore()
  const refresh_token = userStore.refresh_token

  if (!refresh_token) throw new Error("No refresh token available")

  try {
    const response = await refreshTokenApi({ refresh: refresh_token })

    // 更新 token 和用户信息
    userStore.setAccessToken(response.data.access)
    userStore.setUserInfo({
      user_id: response.data.user_id,
      role: response.data.role,
      name: response.data.name
    })

    return response
  } catch (error) {
    // refresh_token 失效，执行登出
    logout()
    throw error
  }
}

/**
 * @name 退出登录并强制刷新页面（会重定向到登录页）
 * @description 调用 useUserStore 的 logout 方法退出登录，并强制刷新页面
 */
function logout() {
  useUserStore().logout()
  location.reload()
}

/**
 * @name 创建请求实例
 * @description 创建一个 axios 实例命名为 instance
 * @returns {AxiosInstance} 返回 axios 实例
 */
function createInstance() {
  // 创建一个 axios 实例命名为 instance
  const instance = axios.create()
  /**
   * @name 添加 token 到请求头
   * @description 在发送请求之前，添加 token 到请求头
   * @param {AxiosRequestConfig} config 请求配置
   */
  function addTokenToHeader(config: AxiosRequestConfig) {
    // 不添加 token 的请求URL
    const noTokenUrls = [
      "/accounts/login/",
      "/accounts/refresh/"
    ]
    // 如果请求URL 不包含 noTokenUrls 中的任何一个，则添加 token 到请求头
    if (!noTokenUrls.some(url => config.url?.includes(url))) {
      const token = getToken()
      // 如果 token 存在，则添加 token 到请求头，过期会在拦截器中刷新
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
  }

  /**
   * @name 请求拦截器
   * @description 在发送请求之前，添加 token 到请求头
   * @param {AxiosRequestConfig} config 请求配置
   * @returns {AxiosRequestConfig} 返回请求配置
   */
  instance.interceptors.request.use(
    // 发送之前
    (config) => {
      addTokenToHeader(config)
      return config
    },
    // 发送失败
    error => Promise.reject(error)
  )

  /**
   * @name 响应拦截器
   * @description 在收到响应之后，处理响应数据，实现自动刷新 token
   * @param {AxiosResponse} response 响应
   * @returns {Promise<AxiosResponse<any>>} 返回响应
   */
  instance.interceptors.response.use(
    (response) => {
      // 在 axios 的响应拦截器中，response 参数只有在请求成功时才会传入，所以成功则返回响应数据
      return response.data
    },
    async (error) => {
      // 这里的 error 是 axios 在请求失败时自动传入的错误对象
      // 它包含了请求失败的所有信息，比如：
      // - error.response: HTTP 响应对象
      // - error.response.status: HTTP 状态码
      // - error.response.data: 服务器返回的错误信息
      // - error.message: 错误消息
      // - error.config: 请求配置信息
      const originalRequest = get(error, "config")
      // status 是 HTTP 状态码
      const status = get(error, "response.status")
      // 从响应中获取后端返回的错误消息
      const backendMessage = get(error, "response.data.message")
      // 处理 401 错误，尝试刷新 token
      if (status === 401
        && !originalRequest.url?.includes("/accounts/login")
        && !originalRequest._retry) {
        // 设置 _retry 为 true，防止重复刷新 token
        originalRequest._retry = true
        try {
          await refreshAccessToken()
          // 重试原始请求
          addTokenToHeader(originalRequest)
          return instance(originalRequest)
        } catch (refreshError) {
          // 刷新 token 失败，执行登出
          logout()
          return Promise.reject(refreshError)
        }
      }

      // 如果后端有返回错误信息，使用后端的错误信息
      if (backendMessage) {
        error.message = backendMessage
      } else {
        // 处理其他 HTTP 错误
        switch (status) {
          case 400:
            error.message = "请求错误"
            break
          case 403:
            error.message = "拒绝访问"
            break
          case 404:
            error.message = "请求地址出错"
            break
          case 408:
            error.message = "请求超时"
            break
          case 500:
            error.message = "服务器内部错误"
            break
          case 501:
            error.message = "服务未实现"
            break
          case 502:
            error.message = "网关错误"
            break
          case 503:
            error.message = "服务不可用"
            break
          case 504:
            error.message = "网关超时"
            break
          case 505:
            error.message = "HTTP 版本不受支持"
            break
        }
      }

      // 显示错误消息
      ElMessage.error(error.message)
      return Promise.reject(error)
    }
  )
  return instance
}

/**
 * @name 创建请求方法
 * @description 创建一个请求方法，用于发送请求
 * @param {AxiosInstance} instance 请求实例
 * @returns {Function} 返回请求方法
 */
function createRequest(instance: AxiosInstance) {
  return <T>(config: AxiosRequestConfig): Promise<T> => {
    // 默认配置
    const defaultConfig: AxiosRequestConfig = {
      // 接口地址
      baseURL: import.meta.env.VITE_BASE_URL,
      // 请求头
      headers: {
        "Content-Type": "application/json"
      },
      // 请求体
      data: {},
      // 请求超时
      timeout: 5000,
      // 跨域请求时是否携带 Cookies
      withCredentials: false
    }
    // 将默认配置 defaultConfig 和传入的自定义配置 config 进行合并成为 mergeConfig
    const mergeConfig = merge(defaultConfig, config)
    return instance(mergeConfig)
  }
}

/** 用于请求的实例 */
const instance = createInstance()

/** 用于请求的方法 */
export const request = createRequest(instance)
