import { pinia } from "@/pinia"
import { resetRouter } from "@/router"
import { routerConfig } from "@/router/config"
import { getCurrentUserApi } from "@@/apis/users"
import { setToken as _setToken, getToken, removeToken } from "@@/utils/cache/cookies"
import { useSettingsStore } from "./settings"
import { useTagsViewStore } from "./tags-view"

export const useUserStore = defineStore("user", () => {
  const access_token = ref<string>(getToken() || "")
  const refresh_token = ref<string>(localStorage.getItem("refresh_token") || "")
  const roles = ref<string[]>([])
  const username = ref<string>("")
  const user_id = ref<string>("")
  const role = ref<string>("")

  const tagsViewStore = useTagsViewStore()
  const settingsStore = useSettingsStore()

  // 设置 Access Token
  const setAccessToken = (value: string) => {
    _setToken(value)
    access_token.value = value
  }

  // 设置 Refresh Token
  const setRefreshToken = (value: string) => {
    localStorage.setItem("refresh_token", value)
    refresh_token.value = value
  }

  // 设置用户信息
  const setUserInfo = (info: { user_id: string, role: string, name: string }) => {
    user_id.value = info.user_id
    role.value = info.role
    username.value = info.name
    roles.value = [info.role] // 将角色转换为数组格式
  }

  // 获取用户详情
  const getInfo = async () => {
    const { data } = await getCurrentUserApi()
    username.value = data.name
    // 将角色转换为数组格式
    roles.value = [data.role]
  }

  // 模拟角色变化
  const changeRoles = (newRole: string) => {
    const newToken = `token-${newRole}`
    access_token.value = newToken
    _setToken(newToken)
    // 使用 $patch 来确保响应式更新
    useUserStore().$patch({
      role: newRole,
      roles: [newRole]
    })
  }

  // 登出
  const logout = () => {
    removeToken()
    localStorage.removeItem("refresh_token")
    access_token.value = ""
    refresh_token.value = ""
    roles.value = []
    user_id.value = ""
    role.value = ""
    username.value = ""
    // 重置路由
    resetRouter()
    // 重置标签页
    resetTagsView()
    // 清除所有缓存
    window.location.href = "/"
  }

  // 重置 Token
  const resetToken = () => {
    removeToken()
    localStorage.removeItem("refresh_token")
    access_token.value = ""
    refresh_token.value = ""
    roles.value = []
    user_id.value = ""
    role.value = ""
    username.value = ""
  }

  // 重置 Visited Views 和 Cached Views
  const resetTagsView = () => {
    if (!settingsStore.cacheTagsView) {
      tagsViewStore.delAllVisitedViews()
      tagsViewStore.delAllCachedViews()
    }
  }

  return {
    access_token,
    refresh_token,
    roles,
    username,
    user_id,
    role,
    setAccessToken,
    setRefreshToken,
    setUserInfo,
    getInfo,
    changeRoles,
    logout,
    resetToken
  }
})

/**
 * @description 在 SPA 应用中可用于在 pinia 实例被激活前使用 store
 * @description 在 SSR 应用中可用于在 setup 外使用 store
 */
export function useUserStoreOutside() {
  return useUserStore(pinia)
}
