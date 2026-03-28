<template>
  <div class="profile-view">
    <div class="mb-6">
      <h2 class="text-3xl font-bold text-food-text mb-2">🎨 我的口味画像</h2>
      <p class="text-gray-500">基于你的饮食习惯，AI为你定制推荐</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左列 -->
      <div class="space-y-6">
        <!-- 口味雷达图 -->
        <TasteRadar :values="tasteValues" />

        <!-- 口味标签云 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-4">🏷️ 口味标签</h3>
          <div class="flex flex-wrap gap-3">
            <span v-for="tag in tasteTags" :key="tag.name"
                  class="px-4 py-2 rounded-full text-sm cursor-pointer transition-all hover:scale-105"
                  :style="{ backgroundColor: tag.color + '20', color: tag.color, fontSize: (tag.weight * 4 + 12) + 'px' }">
              {{ tag.emoji }} {{ tag.name }}
            </span>
          </div>
        </div>

        <!-- 偏好菜系饼图 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-4">🥧 偏好菜系</h3>
          <div class="space-y-3">
            <div v-for="cuisine in cuisinePrefs" :key="cuisine.name">
              <div class="flex justify-between text-sm mb-1">
                <span>{{ cuisine.emoji }} {{ cuisine.name }}</span>
                <span class="text-gray-400">{{ cuisine.percent }}%</span>
              </div>
              <div class="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500" 
                     :style="{ width: cuisine.percent + '%', backgroundColor: cuisine.color }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右列 -->
      <div class="space-y-6">
        <!-- 今日推荐 -->
        <div class="bg-gradient-to-br from-food-primary/10 to-food-secondary/30 rounded-2xl p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-food-text text-lg">✨ 今日为你推荐</h3>
            <span class="text-sm text-gray-400">基于口味画像</span>
          </div>
          <div class="space-y-4">
            <div v-for="rec in todayRecs" :key="rec.id" 
                 class="bg-white rounded-xl p-4 flex gap-3 cursor-pointer hover:shadow-md transition-shadow"
                 @click="$router.push(`/restaurant/${rec.id}`)">
              <img :src="rec.image || `https://via.placeholder.com/80x80?text=${rec.name}`" class="w-16 h-16 rounded-lg object-cover shrink-0" />
              <div class="flex-1 min-w-0">
                <h4 class="font-bold text-food-text">{{ rec.name }}</h4>
                <div class="flex items-center gap-2 mt-1 text-sm text-gray-500">
                  <span>⭐ {{ rec.rating }}</span>
                  <span>¥{{ rec.avg_price }}/人</span>
                </div>
                <p class="text-xs text-gray-400 mt-1">💡 {{ rec.reason }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 搜索历史 -->
        <div class="food-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-food-text">🔍 最近搜索</h3>
            <el-button text type="danger" size="small" @click="searchHistory = []">清空</el-button>
          </div>
          <div v-if="searchHistory.length" class="flex flex-wrap gap-2">
            <el-tag v-for="(h, i) in searchHistory" :key="i" closable @close="searchHistory.splice(i, 1)"
                    class="cursor-pointer" @click="$router.push(`/restaurants?q=${encodeURIComponent(h)}`)">
              {{ h }}
            </el-tag>
          </div>
          <div v-else class="text-center py-6 text-gray-400 text-sm">暂无搜索记录</div>
        </div>

        <!-- 偏好设置 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-4">⚙️ 偏好设置</h3>
          <div class="space-y-4">
            <div>
              <label class="text-sm text-gray-500 mb-1 block">辣度偏好</label>
              <el-slider v-model="spiceLevel" :min="0" :max="5" :format-tooltip="(v: number) => ['不吃辣','微辣','中辣','重辣','变态辣','🔥'][v]" />
            </div>
            <div>
              <label class="text-sm text-gray-500 mb-1 block">价格范围</label>
              <el-select v-model="pricePref" class="w-full">
                <el-option label="不限" value="all" />
                <el-option label="¥0-50 经济实惠" value="budget" />
                <el-option label="¥50-150 中等消费" value="mid" />
                <el-option label="¥150+ 品质消费" value="premium" />
              </el-select>
            </div>
            <el-button type="primary" color="#ff6b35" class="w-full" @click="savePrefs">保存偏好</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TasteRadar from '@/components/TasteRadar.vue'

const tasteValues = ref([0.8, 0.4, 0.3, 0.5, 0.9, 0.2])
const spiceLevel = ref(3)
const pricePref = ref('all')

const tasteTags = [
  { name: '超辣', emoji: '🌶️', weight: 5, color: '#dc2626' },
  { name: '鲜味', emoji: '🍄', weight: 4.5, color: '#16a34a' },
  { name: '微甜', emoji: '🍯', weight: 3, color: '#f59e0b' },
  { name: '酸辣', emoji: '🥭', weight: 3.5, color: '#ea580c' },
  { name: '清淡', emoji: '🥬', weight: 2, color: '#22c55e' },
  { name: '麻辣', emoji: '🔥', weight: 4, color: '#ef4444' },
  { name: '咸香', emoji: '🧂', weight: 3.5, color: '#78716c' },
  { name: '鲜辣', emoji: '🫑', weight: 4.2, color: '#65a30d' },
]

const cuisinePrefs = [
  { name: '川菜', emoji: '🌶️', percent: 35, color: '#dc2626' },
  { name: '火锅', emoji: '🍲', percent: 25, color: '#f97316' },
  { name: '日料', emoji: '🍣', percent: 15, color: '#e11d48' },
  { name: '烧烤', emoji: '🍢', percent: 10, color: '#a16207' },
  { name: '面食', emoji: '🍜', percent: 8, color: '#ca8a04' },
  { name: '其他', emoji: '🍽️', percent: 7, color: '#9ca3af' },
]

const todayRecs = ref([
  { id: '1', name: '巴奴毛肚火锅', rating: 4.9, avg_price: 150, image: '', reason: '根据你对鲜辣口味的偏好推荐' },
  { id: '2', name: '文和友老长沙', rating: 4.7, avg_price: 80, image: '', reason: '湘菜口味匹配，麻辣鲜香' },
  { id: '3', name: '太二酸菜鱼', rating: 4.6, avg_price: 75, image: '', reason: '符合你的中等消费偏好' },
])

const searchHistory = ref(['火锅', '川菜', '日料', '烧烤'])
const savePrefs = () => { /* api call */ }
</script>
