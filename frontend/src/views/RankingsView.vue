<template>
  <div class="rankings-view">
    <div class="mb-6">
      <h2 class="text-3xl font-bold text-food-text mb-2">🏆 全城美食排行榜</h2>
      <p class="text-gray-500">基于多平台数据与AI智能分析</p>
    </div>

    <!-- Tab切换 -->
    <div class="flex flex-wrap gap-2 mb-6">
      <el-button v-for="tab in tabs" :key="tab.key" 
                 :type="activeTab === tab.key ? 'primary' : ''"
                 :color="activeTab === tab.key ? '#ff6b35' : ''"
                 @click="activeTab = tab.key" round>
        {{ tab.emoji }} {{ tab.label }}
      </el-button>
    </div>

    <!-- 榜单列表 -->
    <div class="food-card overflow-hidden">
      <div v-for="(item, index) in rankings" :key="item.id"
           class="flex items-center gap-4 p-4 hover:bg-food-bg/50 transition-colors cursor-pointer border-b border-gray-50 last:border-0"
           @click="$router.push(`/restaurant/${item.id}`)">
        <!-- 排名 -->
        <div class="w-10 text-center shrink-0">
          <span v-if="index < 3" class="text-2xl">{{ ['🥇','🥈','🥉'][index] }}</span>
          <span v-else class="text-lg font-bold text-gray-400">{{ index + 1 }}</span>
        </div>
        <!-- 图片 -->
        <img :src="item.image || `https://via.placeholder.com/80x80?text=${item.name}`" 
             class="w-16 h-16 rounded-xl object-cover shrink-0" />
        <!-- 信息 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <h3 class="font-bold text-food-text truncate">{{ item.name }}</h3>
            <el-tag v-if="item.is_new" type="success" size="small">新店</el-tag>
            <el-tag v-if="item.discount" type="danger" size="small">{{ item.discount }}</el-tag>
          </div>
          <div class="flex flex-wrap gap-1 mt-1">
            <el-tag v-for="tag in (item.cuisine_tags || []).slice(0, 3)" :key="tag" size="small" type="info" effect="plain">{{ tag }}</el-tag>
          </div>
        </div>
        <!-- 评分 -->
        <div class="text-right shrink-0">
          <div class="text-xl font-bold text-food-primary">⭐ {{ item.rating?.toFixed(1) }}</div>
          <div class="text-xs text-gray-400">人均 ¥{{ item.avg_price }}</div>
          <div v-if="item.distance" class="text-xs text-gray-400">{{ item.distance }}km</div>
          <div class="flex items-center gap-1 mt-1 text-xs" :class="item.trend === 'up' ? 'text-green-500' : 'text-gray-400'">
            {{ item.trend === 'up' ? '↑' : item.trend === 'down' ? '↓' : '–' }}
            {{ item.trend_value || '' }}
          </div>
        </div>
      </div>
    </div>

    <div v-if="rankings.length < 50" class="text-center mt-6">
      <el-button @click="loadMore" :loading="loading" color="#ff6b35" round>加载更多</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { rankingApi } from '@/api'

const tabs = [
  { key: 'all', label: '综合榜', emoji: '👑' },
  { key: 'taste', label: '口味最佳', emoji: '👅' },
  { key: 'value', label: '性价比', emoji: '💰' },
  { key: 'distance', label: '距离最近', emoji: '📍' },
  { key: 'popularity', label: '最受欢迎', emoji: '🔥' },
  { key: 'new', label: '新店飙升', emoji: '🚀' },
]

const activeTab = ref('all')
const rankings = ref<any[]>([])
const loading = ref(false)

const mockRankings = () => {
  const names = ['蜀大侠火锅','鮨一·日本料理','老字号兰州拉面','小南国·本帮菜','泰香米泰国餐厅','张亮麻辣烫',
    '海底捞','外婆家','西贝莜面村','喜茶LAB店','太二酸菜鱼','文和友老长沙','巴奴毛肚火锅','鼎泰丰',
    '九毛九','半天妖烤鱼','探鱼','杨国福麻辣烫','必胜客','肯德基','星巴克臻选','奈雪的茶','乐乐茶',
    '绿茶餐厅','新白鹿','弄堂小笼','大董烤鸭','全聚德','花家怡园','眉州东坡']
  return names.map((name, i) => ({
    id: String(i + 1), name, rating: +(4.0 + Math.random() * 0.9).toFixed(1),
    avg_price: Math.floor(20 + Math.random() * 300),
    cuisine_tags: [['川菜','火锅'],['日料','刺身'],['面食'],['本帮菜'],['东南亚'],['川菜','快餐'],['火锅'],['浙菜'],
      ['西北菜'],['甜品'],['粤菜'],['湘菜'],['火锅'],['台菜'],['粤菜'],['烧烤'],['粤菜'],['川菜'],['西餐'],
      ['快餐'],['咖啡'],['甜品'],['甜品'],['浙菜'],['浙菜'],['小吃'],['京菜'],['京菜'],['京菜'],['川菜']][i % 20],
    distance: +(Math.random() * 10).toFixed(1),
    trend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'same',
    trend_value: Math.random() > 0.5 ? `+${Math.floor(Math.random() * 10)}` : `-${Math.floor(Math.random() * 5)}`,
    is_new: i > 25, discount: i === 3 ? '满100减20' : undefined,
  }))
}

onMounted(fetchRankings)
watch(activeTab, fetchRankings)

async function fetchRankings() {
  loading.value = true
  try {
    const fns: Record<string, () => Promise<any>> = {
      all: () => rankingApi.top(), taste: () => rankingApi.byTaste(), value: () => rankingApi.byValue(),
      distance: () => rankingApi.byDistance({ lat: 39.9, lng: 116.4 }), popularity: () => rankingApi.byPopularity(),
      new: () => rankingApi.byNewStore(),
    }
    const res: any = await (fns[activeTab.value]?.() || rankingApi.top())
    rankings.value = res.data || res || []
  } catch { rankings.value = mockRankings() }
  loading.value = false
}

const loadMore = () => { rankings.value = [...rankings.value, ...mockRankings().slice(0, 10)] }
</script>
