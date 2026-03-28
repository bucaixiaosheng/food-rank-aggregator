<template>
  <div class="mood-view">
    <div class="text-center mb-8">
      <h2 class="text-3xl font-bold text-food-text mb-2">😊 此刻心情如何？</h2>
      <p class="text-gray-500">选择你的心情，AI为你推荐最适合的美食</p>
    </div>

    <!-- 心情选择 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-10 max-w-2xl mx-auto">
      <button v-for="mood in moods" :key="mood.key"
              @click="selectMood(mood.key)"
              class="mood-card bg-white rounded-2xl p-6 text-center transition-all duration-300 hover:scale-105 hover:shadow-xl"
              :class="{ 'ring-4 ring-food-primary shadow-xl scale-105': selectedMood === mood.key, 'animate-bounce-once': animating === mood.key }">
        <div class="text-6xl mb-3 transition-transform duration-300" 
             :class="{ 'scale-125': selectedMood === mood.key }">{{ mood.emoji }}</div>
        <div class="font-bold text-food-text text-lg">{{ mood.label }}</div>
        <div class="text-sm text-gray-400 mt-1">{{ mood.desc }}</div>
      </button>
    </div>

    <!-- 推荐结果 -->
    <transition name="slide-up">
      <div v-if="recommendations.length" class="max-w-4xl mx-auto">
        <div class="text-center mb-6">
          <h3 class="text-xl font-bold text-food-primary">
            {{ moods.find(m => m.key === selectedMood)?.emoji }} 
            {{ selectedMood === 'happy' ? '开心就该吃好的！' : selectedMood === 'sad' ? '美食治愈一切' : selectedMood === 'tired' ? '补充能量时刻' : '庆祝就该好好吃！' }}
          </h3>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div v-for="(r, i) in recommendations" :key="r.id"
               class="food-card overflow-hidden"
               :style="{ animationDelay: (i * 0.15) + 's' }"
               :class="{ 'animate-fade-in-up': true }">
            <img :src="r.image || `https://via.placeholder.com/400x200?text=${r.name}`" class="w-full h-44 object-cover" />
            <div class="p-4">
              <h4 class="font-bold text-food-text mb-1">{{ r.name }}</h4>
              <div class="flex items-center gap-2 text-sm text-gray-500 mb-2">
                <span>⭐ {{ r.rating }}</span>
                <span>¥{{ r.avg_price }}/人</span>
              </div>
              <p class="text-sm text-gray-400 mb-3">💡 {{ r.reason }}</p>
              <el-button type="primary" color="#ff6b35" size="small" round @click="$router.push(`/restaurant/${r.id}`)">
                去看看
              </el-button>
            </div>
          </div>
        </div>

        <div class="text-center mt-6">
          <el-button @click="refreshRecommendations" :loading="loading" color="#ff6b35" round>
            🔄 换一批推荐
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { moodApi } from '@/api'

const moods = [
  { key: 'happy', emoji: '😄', label: '开心', desc: '心情大好' },
  { key: 'sad', emoji: '😢', label: '难过', desc: '需要治愈' },
  { key: 'tired', emoji: '😴', label: '疲惫', desc: '补充能量' },
  { key: 'celebrate', emoji: '🎉', label: '庆祝', desc: '值得纪念' },
]

const selectedMood = ref('')
const animating = ref('')
const recommendations = ref<any[]>([])
const loading = ref(false)

const moodRecommendations: Record<string, any[]> = {
  happy: [
    { id: '1', name: '海底捞', rating: 4.6, avg_price: 130, reason: '开心就要和朋友一起吃火锅！', image: '' },
    { id: '2', name: '星巴克臻选', rating: 4.5, avg_price: 45, reason: '来杯咖啡延续好心情', image: '' },
    { id: '3', name: '奈雪的茶', rating: 4.4, avg_price: 30, reason: '甜品让快乐加倍', image: '' },
  ],
  sad: [
    { id: '4', name: '外婆家', rating: 4.5, avg_price: 80, reason: '家常味道最治愈人心', image: '' },
    { id: '5', name: '一风堂拉面', rating: 4.6, avg_price: 65, reason: '一碗热汤面温暖你的胃', image: '' },
    { id: '6', name: '满记甜品', rating: 4.3, avg_price: 35, reason: '甜蜜的食物赶走不开心', image: '' },
  ],
  tired: [
    { id: '7', name: '西贝莜面村', rating: 4.3, avg_price: 110, reason: '营养均衡，补充能量', image: '' },
    { id: '8', name: '肯德基', rating: 4.2, avg_price: 35, reason: '快速便捷，性价比之选', image: '' },
    { id: '9', name: '赛百味', rating: 4.1, avg_price: 30, reason: '健康轻食，元气满满', image: '' },
  ],
  celebrate: [
    { id: '10', name: '鼎泰丰', rating: 4.8, avg_price: 200, reason: '米其林级别的小笼包', image: '' },
    { id: '11', name: '大董烤鸭', rating: 4.7, avg_price: 350, reason: '庆祝就要吃好的！', image: '' },
    { id: '12', name: '喜茶LAB店', rating: 4.6, avg_price: 35, reason: '一杯好茶庆祝美好时刻', image: '' },
  ],
}

const selectMood = async (key: string) => {
  animating.value = key
  selectedMood.value = key
  loading.value = true
  setTimeout(() => { animating.value = '' }, 600)
  try { recommendations.value = (await moodApi.recommend(key) as any)?.data || [] } catch {
    recommendations.value = moodRecommendations[key] || []
  }
  loading.value = false
}

const refreshRecommendations = () => {
  if (selectedMood.value) selectMood(selectedMood.value)
}
</script>

<style scoped>
.mood-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.animate-fade-in-up { animation: fadeInUp 0.5s ease-out forwards; opacity: 0; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.slide-up-enter-active { transition: all 0.4s ease-out; }
.slide-up-leave-active { transition: all 0.2s ease-in; }
.slide-up-enter-from { opacity: 0; transform: translateY(30px); }
.slide-up-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
