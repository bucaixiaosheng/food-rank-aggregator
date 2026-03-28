<template>
  <div class="restaurants-view">
    <!-- 搜索栏 -->
    <div class="mb-6">
      <SearchBar :model-value="(route.query.q as string) || ''" 
                 @search="handleSearch" :show-hot="false" />
    </div>

    <div class="flex gap-6">
      <!-- 左侧筛选 -->
      <aside class="hidden lg:block w-72 shrink-0">
        <FilterPanel @apply="handleFilter" />
      </aside>

      <!-- 主内容 -->
      <div class="flex-1">
        <!-- 顶部操作栏 -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <el-button @click="showMobileFilter = true" class="lg:hidden" size="small">
              <el-icon><Filter /></el-icon> 筛选
            </el-button>
            <span class="text-gray-500">找到 <b class="text-food-primary">{{ restaurants.length }}</b> 家餐厅</span>
          </div>
          <div class="flex gap-2">
            <el-button-group>
              <el-button :type="viewMode === 'grid' ? 'primary' : ''" @click="viewMode = 'grid'" size="small">
                <el-icon><Grid /></el-icon>
              </el-button>
              <el-button :type="viewMode === 'list' ? 'primary' : ''" @click="viewMode = 'list'" size="small">
                <el-icon><List /></el-icon>
              </el-button>
            </el-button-group>
            <el-button @click="$router.push('/map')" size="small">
              <el-icon><Location /></el-icon> 地图
            </el-button>
          </div>
        </div>

        <!-- 餐厅列表 -->
        <div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          <RestaurantCard v-for="(r, i) in restaurants" :key="r.id" :restaurant="{ ...r, discount: i === 0 ? '满100减20' : undefined }"
                          @click="$router.push(`/restaurant/${r.id}`)" />
        </div>
        <div v-else class="space-y-4">
          <div v-for="(r, i) in restaurants" :key="r.id" 
               class="food-card flex overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
               @click="$router.push(`/restaurant/${r.id}`)">
            <img :src="r.image || `https://via.placeholder.com/200x200?text=${r.name}`" class="w-40 h-40 object-cover shrink-0" />
            <div class="p-4 flex-1">
              <div class="flex items-center justify-between mb-1">
                <h3 class="font-bold text-lg text-food-text">{{ r.name }}</h3>
                <el-tag v-if="i === 0" type="danger" size="small">满100减20</el-tag>
              </div>
              <div class="flex flex-wrap gap-1 mb-2">
                <el-tag v-for="tag in (r.cuisine_tags || []).slice(0, 4)" :key="tag" size="small" type="warning" effect="plain">{{ tag }}</el-tag>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-500 mb-2">
                <span>⭐ {{ r.rating?.toFixed(1) }}</span>
                <span>人均 ¥{{ r.avg_price || '--' }}</span>
                <span>📍 {{ r.distance ? r.distance + 'km' : '--' }}</span>
              </div>
              <p v-if="r.ai_summary" class="text-sm text-gray-400 line-clamp-2">🤖 {{ r.ai_summary }}</p>
            </div>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="restaurants.length" class="text-center mt-8">
          <el-button @click="loadMore" :loading="loading" color="#ff6b35" round>加载更多</el-button>
        </div>
        <el-empty v-if="!restaurants.length && !loading" description="暂无符合条件的餐厅" />
      </div>
    </div>

    <!-- 移动端筛选抽屉 -->
    <el-drawer v-model="showMobileFilter" direction="ltr" size="80%">
      <FilterPanel @apply="handleFilter; showMobileFilter = false" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Filter, Grid, List, Location } from '@element-plus/icons-vue'
import SearchBar from '@/components/SearchBar.vue'
import FilterPanel from '@/components/FilterPanel.vue'
import RestaurantCard from '@/components/RestaurantCard.vue'
import { restaurantApi } from '@/api'

const route = useRoute()
const router = useRouter()
const restaurants = ref<any[]>([])
const viewMode = ref<'grid' | 'list'>('grid')
const loading = ref(false)
const showMobileFilter = ref(false)
const currentQuery = ref('')

onMounted(async () => {
  currentQuery.value = (route.query.q as string) || (route.query.tag as string) || ''
  await fetchRestaurants()
})

watch(() => route.query, async () => {
  currentQuery.value = (route.query.q as string) || (route.query.tag as string) || ''
  await fetchRestaurants()
})

const fetchRestaurants = async () => {
  loading.value = true
  try {
    const res: any = await restaurantApi.search({ q: currentQuery.value })
    restaurants.value = res.data || res || []
  } catch {
    restaurants.value = mockData()
  }
  loading.value = false
}

const mockData = () => [
  { id: '1', name: '蜀大侠火锅', rating: 4.8, avg_price: 120, cuisine_tags: ['川菜','火锅'], ai_summary: '正宗川味火锅，毛肚黄喉必点，周末需排队', distance: '1.2' },
  { id: '2', name: '鮨一·日本料理', rating: 4.7, avg_price: 280, cuisine_tags: ['日料','刺身'], ai_summary: '新鲜刺身拼盘，午市套餐性价比高', distance: '2.5' },
  { id: '3', name: '老字号兰州拉面', rating: 4.5, avg_price: 25, cuisine_tags: ['面食','西北'], ai_summary: '二十年老店，牛骨汤底浓郁，拉面劲道', distance: '0.8' },
  { id: '4', name: '小南国·本帮菜', rating: 4.6, avg_price: 180, cuisine_tags: ['本帮菜','江浙'], ai_summary: '红烧肉是一绝，浓油赤酱正宗上海味', distance: '3.1' },
  { id: '5', name: '泰香米泰国餐厅', rating: 4.4, avg_price: 95, cuisine_tags: ['东南亚','泰国菜'], ai_summary: '冬阴功汤酸辣开胃，芒果糯米饭甜品', distance: '1.8' },
  { id: '6', name: '张亮麻辣烫', rating: 4.2, avg_price: 35, cuisine_tags: ['川菜','快餐'], ai_summary: '食材新鲜自选，麻辣鲜香，性价比之选', distance: '0.5' },
]

const handleSearch = (q: string) => { router.push(`/restaurants?q=${encodeURIComponent(q)}`) }
const handleFilter = (filters: any) => { fetchRestaurants() }
const loadMore = () => { /* pagination */ }
</script>

<style scoped>
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
