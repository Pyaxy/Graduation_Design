import type { Router } from "vue-router"
import { usePermissionStore } from "@/pinia/stores/permission"
import { useUserStore } from "@/pinia/stores/user"
import { routerConfig } from "@/router/config"
import { isWhiteList } from "@/router/whitelist"
import { setRouteChange } from "@@/composables/useRouteListener"
import { useTitle } from "@@/composables/useTitle"
import { getToken } from "@@/utils/cache/cookies"
import NProgress from "nprogress"

NProgress.configure({ showSpinner: false })

const { setTitle } = useTitle()

const LOGIN_PATH = "/login"

/**
 * @name 注册导航守卫
 * @description 注册导航守卫，用于处理导航守卫
 * @param {Router} router 路由实例
 */
export function registerNavigationGuard(router: Router) {
  // 全局前置守卫
  router.beforeEach(async (to, _from) => {
    // 开始进度条
    NProgress.start()
    // 获取用户信息
    const userStore = useUserStore()
    // 获取权限信息，主要用于生成可访问的路由
    const permissionStore = usePermissionStore()
    // 如果没有登录
    if (!getToken()) {
      // 如果在免登录的白名单中，则直接进入
      if (isWhiteList(to)) return true
      // 其他没有访问权限的页面将被重定向到登录页面
      return LOGIN_PATH
    }
    // 如果已经登录，并准备进入 Login 页面，则重定向到主页
    if (to.path === LOGIN_PATH) {
      return true
    }
    // 如果用户已经获得其权限角色
    if (userStore.roles.length !== 0) {
      return true
    }
    // 否则要重新获取权限角色
    try {
      await userStore.getInfo()
      // 注意：角色必须是一个数组！ 例如: ["admin"] 或 ["developer", "editor"]
      const roles = userStore.roles
      // 生成可访问的 Routes
      routerConfig.dynamic ? permissionStore.setRoutes(roles) : permissionStore.setAllRoutes()
      // 只添加动态路由到路由实例中
      permissionStore.addRoutes.forEach(route => {
        if (!router.hasRoute(route.name as string)) {
          router.addRoute(route)
        }
      })
      // 设置 replace: true, 因此导航将不会留下历史记录
      return { ...to, replace: true }
    } catch (error) {
      // 过程中发生任何错误，都直接重置 Token，并重定向到登录页面
      userStore.resetToken()
      ElMessage.error((error as Error).message || "路由守卫发生错误")
      return LOGIN_PATH
    }
  })

  // 全局后置钩子
  router.afterEach((to) => {
    setRouteChange(to)
    setTitle(to.meta.title)
    NProgress.done()
  })
}
