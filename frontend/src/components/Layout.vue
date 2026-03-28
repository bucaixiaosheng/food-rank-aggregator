<template>
  <div class="min-h-screen bg-food-bg">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-food-secondary sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2 cursor-pointer" @click="$router.push('/')">
            <span class="text-3xl">🍽️</span>
            <h1 class="text-2xl font-bold text-food-primary">吃什么</h1>
          </div>
          <nav class="hidden md:flex space-x-5">
            <router-link to="/" class="nav-link">首页</router-link>
            <router-link to="/restaurants" class="nav-link">发现美食</router-link>
            <router-link to="/rankings" class="nav-link">排行榜</router-link>
            <router-link to="/notes" class="nav-link">探店笔记</router-link>
            <router-link to="/map" class="nav-link">美食地图</router-link>
            <router-link to="/favorites" class="nav-link">收藏</router-link>
            <router-link to="/profile" class="nav-link">我的</router-link>
          </nav>
          <!-- Mobile menu -->
          <button class="md:hidden text-2xl" @click="showMobileMenu = !showMobileMenu">☰</button>
        </div>
      </div>
      <!-- Mobile nav -->
      <div v-if="showMobileMenu" class="md:hidden bg-white border-t px-4 py-3 space-y-2">
        <router-link v-for="link in navLinks" :key="link.path" :to="link.path"
                     class="block px-3 py-2 rounded-lg hover:bg-food-bg text-food-text"
                     @click="showMobileMenu = false">
          {{ link.icon }} {{ link.label }}
        </router-link>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-100 mt-12 py-8">
      <div class="max-w-7xl mx-auto px-4 text-center text-sm text-gray-400">
        <p>🍽️ 吃什么 - 多平台餐饮聚合推荐平台</p>
        <p class="mt-1">AI驱动 · 美味生活从此开始</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const showMobileMenu = ref(false)
const navLinks = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/restaurants', icon: '🔍', label: '发现美食' },
  { path: '/rankings', icon: '🏆', label: '排行榜' },
  { path: '/notes', icon: '📝', label: '探店笔记' },
  { path: '/map', icon: '🗺️', label: '美食地图' },
  { path: '/favorites', icon: '❤️', label: '收藏' },
  { path: '/mood', icon: '😊', label: '心情推荐' },
  { path: '/random', icon: '🎲', label: '随机推荐' },
  { path: '/profile', icon: '👤', label: '我的' },
]
</script>

<style scoped>
.nav-link {
  color: #2d2d2d;
  transition: color 0.2s;
  font-weight: 500;
  font-size: 0.875rem;
}
.nav-link:hover, .nav-link.router-link-active {
  color: #ff6b35;
}
.nav-link.router-link-active {
  font-weight: 700;
}
</style>
