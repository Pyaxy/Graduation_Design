import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../components/LoginForm.vue'
import TestView from '../components/test_token.vue'
import HomeView from '@/views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginView,
    meta: { title: '用户登录' }
  },
  {
    path: '/test',
    name: 'Test',
    component: TestView,
    meta: { title: '令牌测试' }
  },
  {
    path: '/role',
    name: 'role',
    component: HomeView,
    meta: { title: '角色测试'}
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 动态设置页面标题
router.beforeEach((to) => {
  document.title = to.meta.title || 'CodeCollab'
})

export default router
