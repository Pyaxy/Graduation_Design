import { useUserStore } from "@/pinia/stores/user"
import { getCurrentUserApi } from "@@/apis/users"
import { getToken } from "@@/utils/cache/cookies"

export function useTokenValidation() {
  const userStore = useUserStore()

  async function validateToken() {
    const token = getToken()
    if (!token) return false

    try {
      const { data } = await getCurrentUserApi()
      userStore.setUserInfo({
        user_id: data.user_id,
        role: data.role,
        name: data.name
      })
      return true
    } catch (_error: unknown) {
      // token 无效或过期
      userStore.resetToken()
      return false
    }
  }

  return {
    validateToken
  }
}
