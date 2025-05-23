import type { RouteRecordRaw } from "vue-router"
import { routerConfig } from "@/router/config"
import { registerNavigationGuard } from "@/router/guard"
import { createRouter } from "vue-router"
import { flatMultiLevelRoutes } from "./helper"

const Layouts = () => import("@/layouts/index.vue")

/**
 * @name 常驻路由
 * @description 除了 redirect/403/404/login 等隐藏页面，其他页面建议设置唯一的 Name 属性；
 * @description 只能放入无权限访问的路由，有访问权限的路由必须放在动态路由中
 */
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: "/register",
    component: () => import("@/pages/register/index.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/redirect",
    component: Layouts,
    meta: {
      hidden: true
    },
    children: [
      {
        path: ":path(.*)",
        component: () => import("@/pages/redirect/index.vue")
      }
    ]
  },
  {
    path: "/403",
    component: () => import("@/pages/error/403.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/404",
    component: () => import("@/pages/error/404.vue"),
    meta: {
      hidden: true
    },
    alias: "/:pathMatch(.*)*"
  },
  {
    path: "/login",
    component: () => import("@/pages/login/index.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/",
    component: Layouts,
    meta: {
      title: "首页",
      svgIcon: "dashboard",
      affix: true,
      hidden: false
    },
    children: [
      {
        path: "",
        component: () => import("@/pages/dashboard/index.vue"),
        name: "Dashboard",
        meta: {
          title: "首页",
          svgIcon: "dashboard",
          affix: true,
          hidden: false
        }
      }
    ]
  },
  {
    path: "/demo",
    component: Layouts,
    redirect: "/demo/unocss",
    name: "Demo",
    meta: {
      title: "示例集合",
      elIcon: "DataBoard",
      hidden: true
    },
    children: [
      {
        path: "unocss",
        component: () => import("@/pages/demo/unocss/index.vue"),
        name: "UnoCSS",
        meta: {
          title: "UnoCSS"
        }
      },
      {
        path: "element-plus",
        component: () => import("@/pages/demo/element-plus/index.vue"),
        name: "ElementPlus",
        meta: {
          title: "Element Plus",
          keepAlive: true
        }
      },
      {
        path: "vxe-table",
        component: () => import("@/pages/demo/vxe-table/index.vue"),
        name: "VxeTable",
        meta: {
          title: "Vxe Table",
          keepAlive: true
        }
      },
      {
        path: "level2",
        component: () => import("@/pages/demo/level2/index.vue"),
        redirect: "/demo/level2/level3",
        name: "Level2",
        meta: {
          title: "二级路由",
          alwaysShow: true
        },
        children: [
          {
            path: "level3",
            component: () => import("@/pages/demo/level2/level3/index.vue"),
            name: "Level3",
            meta: {
              title: "三级路由",
              keepAlive: true
            }
          }
        ]
      },
      {
        path: "composable-demo",
        redirect: "/demo/composable-demo/use-fetch-select",
        name: "ComposableDemo",
        meta: {
          title: "组合式函数",
          hidden: true
        },
        children: [
          {
            path: "use-fetch-select",
            component: () => import("@/pages/demo/composable-demo/use-fetch-select.vue"),
            name: "UseFetchSelect",
            meta: {
              title: "useFetchSelect"
            }
          },
          {
            path: "use-fullscreen-loading",
            component: () => import("@/pages/demo/composable-demo/use-fullscreen-loading.vue"),
            name: "UseFullscreenLoading",
            meta: {
              title: "useFullscreenLoading"
            }
          },
          {
            path: "use-watermark",
            component: () => import("@/pages/demo/composable-demo/use-watermark.vue"),
            name: "UseWatermark",
            meta: {
              title: "useWatermark"
            }
          }
        ]
      }
    ]
  },
  {
    path: "/link",
    meta: {
      title: "文档链接",
      elIcon: "Link",
      hidden: true
    },
    children: [
      {
        path: "https://juejin.cn/post/7445151895121543209",
        component: () => {},
        name: "Link1",
        meta: {
          title: "中文文档"
        }
      },
      {
        path: "https://juejin.cn/column/7207659644487139387",
        component: () => {},
        name: "Link2",
        meta: {
          title: "新手教程"
        }
      }
    ]
  }
]

/**
 * @name 动态路由
 * @description 用来放置有权限 (Roles 属性) 的路由，凡是需要权限访问的页面，必须放到这里
 * @description 必须带有唯一的 Name 属性
 */
export const dynamicRoutes: RouteRecordRaw[] = [
  {
    path: "/permission",
    component: Layouts,
    redirect: "/permission/page-level",
    name: "Permission",
    meta: {
      title: "权限演示",
      elIcon: "Lock",
      roles: ["ADMIN"],
      alwaysShow: true,
      hidden: true
    },
    children: [
      {
        path: "page-level",
        component: () => import("@/pages/demo/permission/page-level.vue"),
        name: "PermissionPageLevel",
        meta: {
          title: "页面级",
          roles: ["ADMIN"]
        }
      },
      {
        path: "button-level",
        component: () => import("@/pages/demo/permission/button-level.vue"),
        name: "PermissionButtonLevel",
        meta: {
          title: "按钮级",
          roles: ["ADMIN"]
        }
      }
    ]
  },
  {
    path: "/student",
    component: Layouts,
    name: "Student",
    meta: {
      title: "学生测试栏1",
      roles: ["STUDENT"],
      hidden: true
    },
    children: [
      {
        path: "stu-test",
        component: () => import("@/pages/student/stu-test.vue"),
        name: "StudentTest",
        meta: {
          title: "学生权限测试",
          roles: ["STUDENT"]
        }
      },
      {
        path: "stu-test2",
        component: () => import("@/pages/student/stu-test2.vue"),
        name: "StudentTest2",
        meta: {
          title: "学生权限测试2",
          roles: ["STUDENT"]
        }
      }
    ]
  },
  {
    path: "/code_week",
    component: Layouts,
    name: "CodeWeek",
    meta: {
      title: "程序设计课",
      roles: ["TEACHER", "ADMIN", "STUDENT"],
      elIcon: "Coin"
    },
    children: [
      {
        path: "subject-list",
        component: () => import("@/pages/subject/index.vue"),
        name: "Subject-Manage",
        meta: {
          title: "课题列表",
          roles: ["TEACHER", "ADMIN", "STUDENT"]
        }
      },
      {
        path: "course-manage",
        component: () => import("@/pages/course/index.vue"),
        name: "Course-Manage",
        meta: {
          title: "课程列表",
          roles: ["TEACHER", "ADMIN"]
        }
      },
      {
        path: "course-list",
        component: () => import("@/pages/course/student.vue"),
        name: "Course-List",
        meta: {
          title: "课程列表",
          roles: ["STUDENT"]
        }
      },
      {
        path: "course-detail/:id",
        component: () => import("@/pages/course/course-detail/index.vue"),
        name: "Course-Detail",
        meta: {
          title: "课程详情",
          roles: ["TEACHER", "ADMIN", "STUDENT"],
          hidden: true
        }
      },
      {
        path: "group-detail/:courseId/:groupId",
        component: () => import("@/pages/group/group-detail/index.vue"),
        name: "Group-Detail",
        meta: {
          title: "小组详情",
          roles: ["TEACHER", "ADMIN", "STUDENT"],
          hidden: true
        }
      },
      {
        path: "subject-detail/:id",
        component: () => import("@/pages/subject/detail.vue"),
        name: "Subject-Detail",
        meta: {
          title: "课题详情",
          roles: ["TEACHER", "ADMIN", "STUDENT"],
          hidden: true
        }
      }
    ]
  },
  {
    path: "/teacher",
    component: Layouts,
    redirect: "/teacher/create",
    name: "Teacher",
    meta: {
      title: "教师管理",
      elIcon: "User",
      roles: ["ADMIN"]
    },
    children: [
      {
        path: "create",
        component: () => import("@/pages/teacher/CreateTeacher.vue"),
        name: "CreateTeacher",
        meta: {
          title: "创建教师账号",
          elIcon: "User"
        }
      }
    ]
  }
]
/** 路由实例 */
export const router = createRouter({
  history: routerConfig.history,
  routes: routerConfig.thirdLevelRouteCache ? flatMultiLevelRoutes(constantRoutes) : constantRoutes
})

/** 重置路由 */
export function resetRouter() {
  try {
    // 按照 Name 属性删除路由，所以 Name 属性必须唯一
    router.getRoutes().forEach((route) => {
      const { name, meta } = route
      if (name && meta.roles?.length) {
        router.hasRoute(name) && router.removeRoute(name)
      }
    })
  } catch {
    // 强制刷新浏览器也行，只是交互体验不是很好
    location.reload()
  }
}

// 注册路由导航守卫
registerNavigationGuard(router)
