<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <h1>CodeCollab 协作平台</h1>
  <p>
    <strong>当前路由路径:</strong> {{ $route.fullPath }}
  </p>
  <nav>
    <RouterLink to="/" class="nav-link">登录页面</RouterLink>
    <RouterLink to="/test" class="nav-link">令牌测试</RouterLink>
    <RouterLink to="/role" class="nav-link">角色检测</RouterLink>
  </nav>
  
  <!-- 路由出口 -->
  <RouterView />
</template>

<style scoped>
.nav-link {
  margin: 0 1rem;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background-color: #f0f0f0;
  text-decoration: none;
  color: #2c3e50;
  transition: all 0.3s;
}

.nav-link:hover {
  background-color: #e0e0e0;
  transform: translateY(-2px);
}

.nav-link.router-link-active {
  background-color: #409eff;
  color: white;
}
</style>
