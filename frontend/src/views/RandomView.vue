<template>
  <div class="random-view">
    <div class="text-center mb-8">
      <h2 class="text-3xl font-bold text-food-text mb-2">🎲 美食随机推荐</h2>
      <p class="text-gray-500">选择困难？让命运帮你决定！</p>
    </div>

    <!-- 转盘 -->
    <div class="flex justify-center mb-8">
      <div class="relative w-80 h-80">
        <div ref="wheelRef" 
             class="absolute inset-0 rounded-full border-8 border-food-primary overflow-hidden transition-transform duration-[4000ms] ease-out"
             :style="{ transform: `rotate(${rotation}deg)` }">
          <div v-for="(item, i) in wheelItems" :key="i"
               class="absolute w-1/2 h-1/2 origin-bottom-right"
               :style="{ transform: `rotate(${i * 60}deg)`, background: colors[i % colors.length] }">
            <span class="absolute top-4 left-4 text-white font-bold text-sm transform -rotate-45 whitespace-nowrap">
              {{ item.emoji }} {{ item.name }}
            </span>
          </div>
        </div>
        <!-- 中心按钮 -->
        <button @click="spin" :disabled="spinning"
                class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full bg-food-primary text-white font-bold text-lg shadow-lg hover:bg-food-accent transition-colors z-10 disabled:opacity-50">
          {{ spinning ? '🎲' : '开转！' }}
        </button>
        <!-- 指针 -->
        <div class="absolute -top-4 left-1/2 -translate-x-1/2 text-3xl z-10">👇</div>
      </div>
    </div>

    <!-- 结果展示 -->
    <transition name="pop">
      <div v-if="result" class="max-w-lg mx-auto">
        <div class="food-card overflow-hidden">
          <img :src="result.image || `https://via.placeholder.com/600x250?text=${result.name}`" class="w-full h-52 object-cover" />
          <div class="p-6 text-center">
            <div class="text-4xl mb-2">🎉</div>
            <h3 class="text-2xl font-bold text-food-text mb-2">{{ result.name }}</h3>
            <div class="flex items-center justify-center gap-4 text-gray-500 mb-4">
              <span>⭐ {{ result.rating }}</span>
              <span>¥{{ result.avg_price }}/人</span>
              <span>{{ result.cuisine }}</span>
            </div>
            <p class="text-gray-600 mb-6">{{ result.ai_summary }}</p>
            <div class="flex gap-3 justify-center">
              <el-button type="primary" color="#ff6b35" size="large" round @click="$router.push(`/restaurant/${result.id}`)">
                去看看 🍽️
              </el-button>
              <el-button size="large" round @click="spin">再转一次 🔄</el-button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { randomApi } from '@/api'

const wheelRef = ref<HTMLElement>()
const spinning = ref(false)
const rotation = ref(0)
const result = ref<any>(null)

const colors = ['#ff6b35', '#f7c59f', '#d62828', '#ffc107', '#22c55e', '#3b82f6']

const wheelItems = [
  { name: '火锅', emoji: '🍲', id: '1' },
  { name: '日料', emoji: '🍣', id: '2' },
  { name: '烧烤', emoji: '🍢', id: '3' },
  { name: '面食', emoji: '🍜', id: '4' },
  { name: '西餐', emoji: '🍝', id: '5' },
  { name: '川菜', emoji: '🌶️', id: '6' },
]

const allResults = [
  { id: '1', name: '蜀大侠火锅', rating: 4.8, avg_price: 120, cuisine: '川菜·火锅', image: '', ai_summary: '正宗川味火锅，毛肚黄喉必点，周末需排队约30分钟' },
  { id: '2', name: '鮨一·日本料理', rating: 4.7, avg_price: 280, cuisine: '日料', image: '', ai_summary: '新鲜刺身拼盘，午市套餐性价比高，适合约会' },
  { id: '3', name: '木屋烧烤', rating: 4.5, avg_price: 90, cuisine: '烧烤', image: '', ai_summary: '炭火烤串，羊肉串和烤鸡翅是招牌，配啤酒绝了' },
  { id: '4', name: '老字号兰州拉面', rating: 4.5, avg_price: 25, cuisine: '西北·面食', image: '', ai_summary: '二十年老店，牛骨汤底浓郁，拉面劲道' },
  { id: '5', name: 'Bistro Margot', rating: 4.6, avg_price: 220, cuisine: '法餐·西餐', image: '', ai_summary: '地道法式小酒馆，鹅肝和牛排都很惊艳' },
  { id: '6', name: '太二酸菜鱼', rating: 4.5, avg_price: 75, cuisine: '川菜', image: '', ai_summary: '酸菜鱼酸辣开胃，鱼肉嫩滑，性价比不错' },
]

const spin = async () => {
  if (spinning.value) return
  spinning.value = true
  result.value = null

  const extraSpins = 5 + Math.random() * 3
  const targetAngle = rotation.value + extraSpins * 360 + Math.random() * 360
  rotation.value = targetAngle

  setTimeout(async () => {
    spinning.value = false
    const idx = Math.floor(Math.random() * allResults.length)
    try { const res: any = await randomApi.get(); result.value = res?.data || res } catch {
      result.value = allResults[idx]
    }
  }, 4200)
}
</script>

<style scoped>
.pop-enter-active { animation: popIn 0.5s ease-out; }
@keyframes popIn { from { opacity: 0; transform: scale(0.8); } to { opacity: 1; transform: scale(1); } }
</style>
