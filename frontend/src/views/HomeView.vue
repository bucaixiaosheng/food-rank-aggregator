<template>
  <div class="home-view">
    <!-- Hero搜索区 -->
    <section class="bg-gradient-to-br from-orange-400 via-food-primary to-red-500 rounded-3xl p-8 md:p-12 mb-8 text-white relative overflow-hidden">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-4 left-10 text-8xl">🍜</div>
        <div class="absolute bottom-4 right-10 text-8xl">🍣</div>
        <div class="absolute top-20 right-20 text-6xl">🥘</div>
      </div>
      <div class="relative z-10">
        <h2 class="text-3xl md:text-4xl font-bold mb-2">今天吃什么？</h2>
        <p class="text-white/80 mb-6">多平台聚合，AI推荐，发现你身边的好味道</p>
        <div class="relative max-w-2xl">
          <el-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-xl"><Search /></el-icon>
          <input v-model="searchQuery" type="text" placeholder="搜索餐厅、菜系、美食..."
                 @keyup.enter="doSearch"
                 class="w-full pl-12 pr-24 py-4 rounded-2xl bg-white text-gray-800 text-lg focus:outline-none shadow-lg" />
          <button @click="doSearch" class="absolute right-2 top-1/2 -translate-y-1/2 bg-food-primary text-white px-6 py-2 rounded-xl hover:bg-food-accent transition-colors">
            搜索
          </button>
          <button class="absolute right-20 top-1/2 -translate-y-1/2 text-gray-400 hover:text-food-primary transition-colors" title="语音搜索">
            🎤
          </button>
        </div>
      </div>
    </section>

    <!-- 热门口味标签云 -->
    <section class="mb-8">
      <h3 class="text-xl font-bold text-food-text mb-4">🔥 热门口味</h3>
      <div class="flex flex-wrap gap-3">
        <button v-for="tag in tasteTags" :key="tag.label"
                @click="searchByTag(tag.label)"
                class="px-5 py-2 rounded-full text-sm font-medium transition-all hover:scale-105 shadow-sm hover:shadow-md"
                :class="selectedTag === tag.label ? 'bg-food-primary text-white' : 'bg-white text-food-text'">
          <span class="mr-1">{{ tag.emoji }}</span>{{ tag.label }}
        </button>
      </div>
    </section>

    <!-- 天气推荐 -->
    <section v-if="weatherRec" class="mb-8 food-card p-6 bg-gradient-to-r from-blue-50 to-orange-50">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-bold text-food-text mb-1">🌤️ {{ weatherRec.weather }} · {{ weatherRec.temp }}</h3>
          <p class="text-gray-500 text-sm">{{ weatherRec.suggestion }}</p>
        </div>
        <el-button type="primary" color="#ff6b35" round @click="$router.push('/restaurants?tag=' + encodeURIComponent(weatherRec.recommend_tag))">
          查看推荐
        </el-button>
      </div>
    </section>

    <!-- 今日推荐 -->
    <section class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-bold text-food-text">✨ 今日推荐</h3>
        <button @click="$router.push('/profile')" class="text-food-primary text-sm hover:underline">查看更多 →</button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <RestaurantCard v-for="r in recommendations" :key="r.id" :restaurant="r" @click="$router.push(`/restaurant/${r.id}`)" />
      </div>
      <div v-if="!recommendations.length" class="text-center py-8 text-gray-400">加载中...</div>
    </section>

    <!-- 快捷入口 -->
    <section class="mb-8 grid grid-cols-2 md:grid-cols-4 gap-4">
      <router-link v-for="entry in quickEntries" :key="entry.path" :to="entry.path"
                   class="food-card p-5 text-center hover:scale-105 transition-transform group">
        <div class="text-4xl mb-2">{{ entry.emoji }}</div>
        <div class="font-semibold text-food-text group-hover:text-food-primary transition-colors">{{ entry.label }}</div>
      </router-link>
    </section>

    <!-- 美食排行榜入口 -->
    <section class="mb-8">
      <div class="bg-gradient-to-r from-food-primary to-food-accent rounded-2xl p-6 text-white flex items-center justify-between">
        <div>
          <h3 class="text-xl font-bold">🏆 全城美食排行榜</h3>
          <p class="text-white/80 text-sm mt-1">发现全城最受欢迎的美食</p>
        </div>
        <el-button round @click="$router.push('/rankings')" class="bg-white text-food-primary hover:bg-gray-100 font-bold">
          查看榜单 →
        </el-button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import RestaurantCard from '@/components/RestaurantCard.vue'
import { restaurantApi, weatherApi } from '@/api'

const router = useRouter()
const searchQuery = ref('')
const selectedTag = ref('')

const tasteTags = [
  { emoji: '🌶️', label: '辣' }, { emoji: '🥬', label: '清淡' }, { emoji: '🍰', label: '甜' },
  { emoji: '🍋', label: '酸' }, { emoji: '🧂', label: '咸' }, { emoji: '🍄', label: '鲜' },
  { emoji: '🔥', label: '火锅' }, { emoji: '🍣', label: '日料' }, { emoji: '🍝', label: '西餐' },
  { emoji: '🍢', label: '烧烤' }, { emoji: '🥟', label: '面食' }, { emoji: '🧋', label: '甜品' },
]

const quickEntries = [
  { emoji: '🎲', label: '随机推荐', path: '/random' },
  { emoji: '😊', label: '心情推荐', path: '/mood' },
  { emoji: '🗺️', label: '美食地图', path: '/map' },
  { emoji: '❤️', label: '我的收藏', path: '/favorites' },
]

const recommendations = ref<any[]>([])
const weatherRec = ref<any>(null)

onMounted(async () => {
  try { recommendations.value = (await restaurantApi.getRecommendations() as any)?.data || [] } catch { 
    recommendations.value = [
      { id: '1', name: '蜀大侠火锅', rating: 4.8, avg_price: 120, cuisine_tags: ['川菜','火锅'], image: '', ai_summary: '正宗川味火锅，毛肚黄喉必点', distance: '1.2' },
      { id: '2', name: '鮨一·日本料理', rating: 4.7, avg_price: 280, cuisine_tags: ['日料','刺身'], image: '', ai_summary: '新鲜刺身，环境优雅，适合约会', distance: '2.5' },
      { id: '3', name: '老字号兰州拉面', rating: 4.5, avg_price: 25, cuisine_tags: ['面食','西北'], image: '', ai_summary: '二十年老店，牛肉面一绝', distance: '0.8', discount: '满20减5' },
    ]
  }
  try { weatherRec.value = (await weatherApi.getRecommendation() as any)?.data || null } catch {
    weatherRec.value = { weather: '晴', temp: '26°C', suggestion: '今天天气不错，适合约朋友聚餐', recommend_tag: '火锅' }
  }
})

const doSearch = () => { if (searchQuery.value.trim()) router.push(`/restaurants?q=${encodeURIComponent(searchQuery.value)}`) }
const searchByTag = (tag: string) => { selectedTag.value = tag; router.push(`/restaurants?tag=${encodeURIComponent(tag)}`) }
</script>
