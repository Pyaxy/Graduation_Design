import type { RouteRecordRaw } from "vue-router"
import { pinia } from "@/pinia"
import { constantRoutes, dynamicRoutes } from "@/router"
import { routerConfig } from "@/router/config"
import { flatMultiLevelRoutes } from "@/router/helper"

// 判断是否具有访问权限
function hasPermission(roles: string[], route: RouteRecordRaw, parentRoute?: RouteRecordRaw): boolean {
  const routeRoles = route.meta?.roles
  // 如果路由没有设置roles，则继承父路由的roles
  if (!routeRoles) {
    return parentRoute ? hasPermission(roles, parentRoute) : true
  }
  return roles.some(role => routeRoles.includes(role))
}

// 根据角色过滤并生成动态路由，返回可访问的路由，并生成二级路由
function filterDynamicRoutes(routes: RouteRecordRaw[], roles: string[]) {
  const res: RouteRecordRaw[] = []
  routes.forEach((route) => {
    const tempRoute = { ...route }
    // 判断是否具有访问权限
    if (hasPermission(roles, tempRoute)) {
      // 如果存在子路由，则递归过滤子路由
      if (tempRoute.children) {
        tempRoute.children = filterDynamicRoutes(tempRoute.children, roles).map(child => ({
          ...child,
          meta: { ...child.meta, roles: child.meta?.roles || tempRoute.meta?.roles }
        }))
      }
      // 将可访问的路由添加到结果数组中
      res.push(tempRoute)
    }
  })
  return res
}
/**
 * @name 权限store
 * @description 用于生成可访问的路由,在路由守卫中被加载
 */
export const usePermissionStore = defineStore("permission", () => {
  // 可访问的路由
  const routes = ref<RouteRecordRaw[]>([])

  // 有访问权限的动态路由
  const addRoutes = ref<RouteRecordRaw[]>([])

  // 根据角色生成可访问的 Routes（可访问的路由 = 常驻路由 + 有访问权限的动态路由）
  const setRoutes = (roles: string[]) => {
    const accessedRoutes = filterDynamicRoutes(dynamicRoutes, roles)
    set(accessedRoutes)
  }

  // 所有路由 = 所有常驻路由 + 所有动态路由
  const setAllRoutes = () => {
    set(dynamicRoutes)
  }

  const setCommonRoutes = () => {
    routes.value = constantRoutes
  }

  // 统一设置
  const set = (accessedRoutes: RouteRecordRaw[]) => {
    routes.value = constantRoutes.concat(accessedRoutes)
    addRoutes.value = routerConfig.thirdLevelRouteCache ? flatMultiLevelRoutes(accessedRoutes) : accessedRoutes
  }

  return { routes, addRoutes, setRoutes, setAllRoutes, setCommonRoutes }
})

/**
 * @description 在 SPA 应用中可用于在 pinia 实例被激活前使用 store
 * @description 在 SSR 应用中可用于在 setup 外使用 store
 */
export function usePermissionStoreOutside() {
  return usePermissionStore(pinia)
}
