<template>
  <div class="min-h-screen bg-food-bg">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-food-secondary">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <span class="text-3xl">🍽️</span>
            <h1 class="text-2xl font-bold text-food-primary">吃什么</h1>
          </div>
          <nav class="flex space-x-6">
            <router-link to="/" class="text-food-text hover:text-food-primary transition-colors">
              首页
            </router-link>
            <router-link to="/restaurants" class="text-food-text hover:text-food-primary transition-colors">
              发现美食
            </router-link>
            <router-link to="/notes" class="text-food-text hover:text-food-primary transition-colors">
              探店笔记
            </router-link>
            <router-link to="/profile" class="text-food-text hover:text-food-primary transition-colors">
              我的
            </router-link>
          </nav>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
      <router-view />
    </main>

    <!-- Sidebar -->
    <aside class="fixed right-4 top-1/2 transform -translate-y-1/2 bg-white rounded-lg shadow-lg p-4">
      <div class="space-y-4">
        <button class="food-button w-full">🔍 搜索</button>
        <button class="food-button w-full">📍 附近</button>
        <button class="food-button w-full">🔥 热门</button>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
// Layout组件
</script>

<style scoped>
</style>
