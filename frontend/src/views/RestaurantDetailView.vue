<template>
  <div class="detail-view" v-if="restaurant">
    <!-- 顶部大图 -->
    <div class="relative rounded-2xl overflow-hidden mb-6 h-64 md:h-80">
      <img :src="restaurant.image || 'https://via.placeholder.com/1200x400?text=🍲'" class="w-full h-full object-cover" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent"></div>
      <div class="absolute bottom-0 left-0 right-0 p-6 text-white">
        <div class="flex items-end justify-between">
          <div>
            <h1 class="text-3xl font-bold mb-2">{{ restaurant.name }}</h1>
            <div class="flex items-center gap-3 text-sm">
              <span class="flex items-center gap-1">⭐ <b>{{ restaurant.rating?.toFixed(1) }}</b></span>
              <span>人均 ¥{{ restaurant.avg_price }}</span>
              <span>📍 {{ restaurant.address }}</span>
            </div>
          </div>
          <div class="flex gap-2">
            <el-button @click="toggleFavorite" circle size="large">
              {{ isFav ? '❤️' : '🤍' }}
            </el-button>
            <el-button @click="showMap = !showMap" circle size="large">🗺️</el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 左侧主内容 -->
      <div class="lg:col-span-2 space-y-6">
        <!-- 多平台评分 -->
        <RatingChart :ratings="ratings" />

        <!-- AI评论摘要 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-3">🤖 AI智能点评</h3>
          <p class="text-gray-600 leading-relaxed">{{ restaurant.ai_summary || '暂无AI点评数据，AI正在分析中...' }}</p>
          <div class="mt-3 flex gap-2">
            <el-tag v-for="tag in (restaurant.tags || ['环境优雅','口味正宗','服务热情'])" :key="tag" type="warning" effect="plain" size="small">{{ tag }}</el-tag>
          </div>
        </div>

        <!-- 推荐菜 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-4">🍽️ 招牌推荐</h3>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div v-for="dish in dishes" :key="dish.name" 
                 class="bg-food-bg rounded-xl p-3 text-center hover:shadow-md transition-shadow cursor-pointer">
              <div class="text-3xl mb-1">{{ dish.emoji }}</div>
              <div class="font-medium text-sm text-food-text">{{ dish.name }}</div>
              <div class="text-xs text-food-primary mt-1">¥{{ dish.price }}</div>
              <div class="text-xs text-gray-400 mt-1">👍 {{ dish.like_count }}人推荐</div>
            </div>
          </div>
        </div>

        <!-- 用户探店笔记 -->
        <div class="food-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-food-text">📝 探店笔记</h3>
            <el-button text type="primary" @click="$router.push('/notes')">查看全部 →</el-button>
          </div>
          <div class="space-y-4">
            <div v-for="note in notes" :key="note.id" class="flex gap-3 pb-4 border-b border-gray-50 last:border-0">
              <div class="w-10 h-10 rounded-full bg-food-secondary flex items-center justify-center shrink-0 text-sm">{{ note.user?.[0] || '👤' }}</div>
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-medium text-sm">{{ note.user }}</span>
                  <span class="text-xs text-gray-400">{{ note.time }}</span>
                </div>
                <p class="text-sm text-gray-600">{{ note.content }}</p>
                <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                  <span>❤️ {{ note.likes }}</span>
                  <span>💬 {{ note.comments }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧 -->
      <div class="space-y-6">
        <!-- 优惠券 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-3">🎁 优惠券</h3>
          <div class="space-y-3">
            <div v-for="coupon in coupons" :key="coupon.id" 
                 class="border-2 border-dashed border-food-primary/30 rounded-xl p-3 relative overflow-hidden">
              <div class="absolute top-0 left-0 w-1 h-full bg-food-primary"></div>
              <div class="pl-3">
                <div class="font-bold text-food-primary">{{ coupon.name }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ coupon.desc }}</div>
                <div class="text-xs text-gray-400 mt-1">有效期至 {{ coupon.expire }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-3">ℹ️ 餐厅信息</h3>
          <div class="space-y-3 text-sm">
            <div class="flex items-center gap-2 text-gray-600"><span>📍</span>{{ restaurant.address }}</div>
            <div class="flex items-center gap-2 text-gray-600"><span>📞</span>{{ restaurant.phone || '暂无' }}</div>
            <div class="flex items-center gap-2 text-gray-600"><span>🕐</span>{{ restaurant.hours || '10:00-22:00' }}</div>
            <div class="flex items-center gap-2 text-gray-600"><span>💬</span>{{ restaurant.review_count || 0 }}条评价</div>
          </div>
        </div>

        <!-- 附近推荐 -->
        <div class="food-card p-6">
          <h3 class="font-bold text-food-text mb-3">📌 附近推荐</h3>
          <div class="space-y-3">
            <div v-for="r in nearbyList" :key="r.id" class="flex items-center gap-3 cursor-pointer hover:bg-gray-50 rounded-lg p-2 -m-2"
                 @click="$router.push(`/restaurant/${r.id}`)">
              <img :src="r.image || `https://via.placeholder.com/60x60?text=${r.name}`" class="w-12 h-12 rounded-lg object-cover" />
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm truncate">{{ r.name }}</div>
                <div class="text-xs text-gray-400">⭐ {{ r.rating }} · ¥{{ r.avg_price }}</div>
              </div>
              <span class="text-xs text-gray-400 shrink-0">{{ r.distance }}km</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <el-skeleton v-else :rows="15" animated />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import RatingChart from '@/components/RatingChart.vue'
import { restaurantApi } from '@/api'

const route = useRoute()
const restaurant = ref<any>(null)
const isFav = ref(false)
const showMap = ref(false)
const ratings = ref([
  { name: '美团', score: 4.8, color: '#ffc107' },
  { name: '大众点评', score: 4.7, color: '#ff6b35' },
  { name: '小红书', score: 4.9, color: '#fe2c55' },
])

const dishes = ref([
  { name: '招牌毛肚', price: 68, emoji: '🥩', like_count: 328 },
  { name: '黄喉', price: 48, emoji: '🫀', like_count: 256 },
  { name: '鲜切牛肉', price: 58, emoji: '🥩', like_count: 412 },
  { name: '手工虾滑', price: 42, emoji: '🦐', like_count: 189 },
  { name: '鸭血豆腐', price: 28, emoji: '🫘', like_count: 156 },
  { name: '红糖糍粑', price: 18, emoji: '🍡', like_count: 298 },
])

const notes = ref([
  { id: '1', user: '美食达人小王', content: '毛肚非常新鲜，七上八下涮着吃绝了！环境也很好，服务员态度超好', time: '2天前', likes: 42, comments: 8 },
  { id: '2', user: '吃货小姐姐', content: '第二次来了，每次必点虾滑和毛肚，番茄锅底也很赞', time: '1周前', likes: 28, comments: 5 },
  { id: '3', user: '探店老司机', content: '周末排队大约30分钟，建议提前取号。味道确实不错，性价比很高', time: '2周前', likes: 15, comments: 3 },
])

const coupons = ref([
  { id: '1', name: '新人立减', desc: '新用户满100减30', expire: '2026-04-30' },
  { id: '2', name: '午市特惠', desc: '工作日11:00-14:00满80减15', expire: '2026-04-30' },
])

const nearbyList = ref([
  { id: '2', name: '鮨一·日本料理', rating: 4.7, avg_price: 280, distance: '0.5', image: '' },
  { id: '5', name: '泰香米泰国餐厅', rating: 4.4, avg_price: 95, distance: '0.8', image: '' },
  { id: '6', name: '张亮麻辣烫', rating: 4.2, avg_price: 35, distance: '1.1', image: '' },
])

onMounted(async () => {
  const id = route.params.id as string
  try {
    const res: any = await restaurantApi.getById(id)
    restaurant.value = res.data || res
  } catch {
    restaurant.value = {
      id, name: '蜀大侠火锅', rating: 4.8, avg_price: 120, address: '朝阳区建国路88号',
      cuisine_tags: ['川菜','火锅'], ai_summary: '正宗川味火锅，毛肚鲜嫩，锅底醇厚。服务热情周到，环境干净整洁。适合朋友聚餐、家庭聚会。午市有特惠套餐，建议提前预约。',
      review_count: 2386, phone: '010-88886666', hours: '11:00-次日02:00',
      tags: ['环境优雅','口味正宗','服务热情','停车方便'],
    }
  }
})

const toggleFavorite = () => { isFav.value = !isFav.value }
</script>
