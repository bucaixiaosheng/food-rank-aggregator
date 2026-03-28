<template>
  <div class="favorites-view">
    <div class="mb-6 flex items-center justify-between">
      <h2 class="text-3xl font-bold text-food-text">❤️ 我的收藏</h2>
      <el-button type="primary" color="#ff6b35" @click="showNewGroup = true" round>+ 新建分组</el-button>
    </div>

    <div class="flex gap-6">
      <!-- 左侧分组 -->
      <aside class="w-56 shrink-0">
        <div class="food-card p-4 space-y-1">
          <div v-for="group in groups" :key="group.id"
               @click="activeGroup = group.id"
               class="flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors"
               :class="activeGroup === group.id ? 'bg-food-primary/10 text-food-primary font-bold' : 'hover:bg-gray-50'">
            <div class="flex items-center gap-2">
              <span>{{ group.icon }}</span>
              <span>{{ group.name }}</span>
            </div>
            <el-badge :value="group.count" :max="99" type="info" />
          </div>
        </div>
      </aside>

      <!-- 右侧卡片网格 -->
      <div class="flex-1">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-food-text">{{ currentGroup?.name }} ({{ filteredList.length }})</h3>
          <div class="flex gap-2">
            <el-button-group>
              <el-button :type="layout === 'grid' ? 'primary' : ''" size="small" @click="layout = 'grid'">
                <el-icon><Grid /></el-icon>
              </el-button>
              <el-button :type="layout === 'list' ? 'primary' : ''" size="small" @click="layout = 'list'">
                <el-icon><List /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </div>

        <div v-if="layout === 'grid'" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          <div v-for="item in filteredList" :key="item.id"
               class="food-card overflow-hidden relative group"
               draggable="true" @dragstart="dragId = item.id">
            <img :src="item.image || `https://via.placeholder.com/400x200?text=${item.name}`" class="w-full h-40 object-cover" />
            <div class="p-4">
              <h4 class="font-bold text-food-text">{{ item.name }}</h4>
              <div class="text-sm text-gray-500 mt-1">⭐ {{ item.rating }} · ¥{{ item.avg_price }}</div>
            </div>
            <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
              <el-button circle size="small" type="danger" @click="removeFav(item.id)">✕</el-button>
            </div>
          </div>
        </div>
        <div v-else class="space-y-3">
          <div v-for="item in filteredList" :key="item.id"
               class="food-card p-4 flex items-center gap-4 cursor-pointer hover:shadow-md transition-shadow"
               draggable="true" @dragstart="dragId = item.id"
               @click="$router.push(`/restaurant/${item.id}`)">
            <img :src="item.image || `https://via.placeholder.com/60x60?text=${item.name}`" class="w-14 h-14 rounded-lg object-cover shrink-0" />
            <div class="flex-1 min-w-0">
              <div class="font-bold text-food-text truncate">{{ item.name }}</div>
              <div class="text-sm text-gray-400">⭐ {{ item.rating }} · ¥{{ item.avg_price }}</div>
            </div>
            <el-button text type="danger" size="small" @click.stop="removeFav(item.id)">移除</el-button>
          </div>
        </div>

        <el-empty v-if="!filteredList.length" description="这个分组还没有收藏哦" />
      </div>
    </div>

    <!-- 新建分组对话框 -->
    <el-dialog v-model="showNewGroup" title="新建分组" width="400px">
      <el-input v-model="newGroupName" placeholder="请输入分组名称" class="mb-4" />
      <div class="flex gap-2">
        <span v-for="emoji in ['📌','⭐','💡','🎯','🏠','💼']" :key="emoji" 
              class="text-2xl cursor-pointer hover:scale-125 transition-transform"
              @click="newGroupIcon = emoji" :class="newGroupIcon === emoji ? 'ring-2 ring-food-primary rounded' : ''">
          {{ emoji }}
        </span>
      </div>
      <template #footer>
        <el-button @click="showNewGroup = false">取消</el-button>
        <el-button type="primary" color="#ff6b35" @click="addGroup">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Grid, List } from '@element-plus/icons-vue'
import { favoriteApi } from '@/api'

const groups = ref([
  { id: 'want', name: '想去', icon: '🔴', count: 3 },
  { id: 'visited', name: '已去', icon: '✅', count: 5 },
  { id: 'saved', name: '收藏', icon: '⭐', count: 8 },
  { id: 'date', name: '约会', icon: '💕', count: 2 },
  { id: 'work', name: '工作餐', icon: '💼', count: 4 },
])

const activeGroup = ref('want')
const layout = ref<'grid' | 'list'>('grid')
const dragId = ref('')
const showNewGroup = ref(false)
const newGroupName = ref('')
const newGroupIcon = ref('📌')

const favorites = ref([
  { id: '1', name: '鮨一·日本料理', rating: 4.7, avg_price: 280, group: 'want', image: '' },
  { id: '2', name: '米其林一星餐厅', rating: 4.9, avg_price: 500, group: 'want', image: '' },
  { id: '3', name: '太二酸菜鱼', rating: 4.5, avg_price: 75, group: 'want', image: '' },
  { id: '4', name: '蜀大侠火锅', rating: 4.8, avg_price: 120, group: 'visited', image: '' },
  { id: '5', name: '海底捞', rating: 4.6, avg_price: 130, group: 'visited', image: '' },
  { id: '6', name: '西贝莜面村', rating: 4.3, avg_price: 110, group: 'visited', image: '' },
])

const currentGroup = computed(() => groups.value.find(g => g.id === activeGroup.value))
const filteredList = computed(() => favorites.value.filter(f => f.group === activeGroup.value))

const removeFav = (id: string) => {
  favorites.value = favorites.value.filter(f => f.id !== id)
  const g = groups.value.find(g => g.id === activeGroup.value)
  if (g) g.count--
}

const addGroup = () => {
  if (!newGroupName.value) return
  groups.value.push({ id: Date.now().toString(), name: newGroupName.value, icon: newGroupIcon.value, count: 0 })
  showNewGroup.value = false
  newGroupName.value = ''
}
</script>
