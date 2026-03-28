<template>
  <div class="map-view">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-3xl font-bold text-food-text">🗺️ 美食打卡地图</h2>
      <div class="flex gap-2">
        <el-tag v-for="legend in legends" :key="legend.label" :color="legend.color" effect="dark" class="border-0">
          {{ legend.icon }} {{ legend.label }}
        </el-tag>
      </div>
    </div>

    <!-- 地图容器 -->
    <div class="food-card overflow-hidden rounded-2xl" style="height: 600px;">
      <div id="map-container" class="w-full h-full bg-gray-100 relative">
        <!-- 地图占位 / 高德地图将在此渲染 -->
        <div v-if="!mapLoaded" class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <div class="text-6xl mb-4">🗺️</div>
            <p class="text-gray-500 mb-2">正在加载地图...</p>
            <p class="text-sm text-gray-400">请配置高德地图API Key</p>
          </div>
        </div>
        <!-- 标记点列表（地图未加载时显示） -->
        <div v-else class="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur rounded-xl p-4 max-h-60 overflow-y-auto">
          <h4 class="font-bold text-food-text mb-3">附近美食</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div v-for="m in markers" :key="m.id" 
                 class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                 @click="selectMarker(m)">
              <span class="text-xl">{{ m.status === 'visited' ? '✅' : m.status === 'want' ? '🔴' : '🔵' }}</span>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm truncate">{{ m.name }}</div>
                <div class="text-xs text-gray-400">{{ m.rating }} · {{ m.distance }}km</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 选中餐厅弹窗 -->
    <el-dialog v-model="showPopup" :title="selectedMarker?.name" width="400px" round>
      <div v-if="selectedMarker" class="space-y-3">
        <div class="flex items-center gap-2 text-sm">
          <span>⭐ {{ selectedMarker.rating }}</span>
          <span>人均 ¥{{ selectedMarker.avg_price }}</span>
          <el-tag :type="selectedMarker.status === 'visited' ? 'success' : selectedMarker.status === 'want' ? 'danger' : 'primary'" size="small">
            {{ selectedMarker.status === 'visited' ? '已打卡' : selectedMarker.status === 'want' ? '想去' : '推荐' }}
          </el-tag>
        </div>
        <p class="text-gray-600 text-sm">{{ selectedMarker.desc }}</p>
        <div class="flex gap-2">
          <el-button type="primary" color="#ff6b35" @click="$router.push(`/restaurant/${selectedMarker.id}`)">查看详情</el-button>
          <el-button @click="showPopup = false">关闭</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const mapLoaded = ref(false)
const showPopup = ref(false)
const selectedMarker = ref<any>(null)

const legends = [
  { label: '已打卡', color: '#22c55e', icon: '✅' },
  { label: '想去', color: '#ef4444', icon: '🔴' },
  { label: '推荐', color: '#3b82f6', icon: '🔵' },
]

const markers = ref([
  { id: '1', name: '蜀大侠火锅', lat: 39.92, lng: 116.46, status: 'visited', rating: 4.8, avg_price: 120, distance: '1.2', desc: '正宗川味火锅，已打卡3次' },
  { id: '2', name: '鮨一·日本料理', lat: 39.93, lng: 116.47, status: 'want', rating: 4.7, avg_price: 280, distance: '2.5', desc: '一直想去试试的日料店' },
  { id: '3', name: '泰香米泰国餐厅', lat: 39.91, lng: 116.45, status: 'nearby', rating: 4.4, avg_price: 95, distance: '0.8', desc: 'AI推荐：冬阴功汤好评如潮' },
  { id: '4', name: '海底捞', lat: 39.94, lng: 116.48, status: 'visited', rating: 4.6, avg_price: 130, distance: '3.0', desc: '服务一如既往的好' },
  { id: '5', name: '太二酸菜鱼', lat: 39.90, lng: 116.44, status: 'want', rating: 4.5, avg_price: 75, distance: '1.5', desc: '酸菜鱼很赞，想去打卡' },
  { id: '6', name: '西贝莜面村', lat: 39.925, lng: 116.465, status: 'nearby', rating: 4.3, avg_price: 110, distance: '0.3', desc: '附近推荐：莜面好吃' },
])

onMounted(() => {
  // 高德地图JS API加载
  setTimeout(() => { mapLoaded.value = true }, 1500)
  /* 实际项目中:
  const script = document.createElement('script')
  script.src = 'https://webapi.amap.com/maps?v=2.0&key=YOUR_KEY'
  script.onload = () => { initMap() }
  document.head.appendChild(script)
  */
})

const selectMarker = (m: any) => { selectedMarker.value = m; showPopup.value = true }
</script>
