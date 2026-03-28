<template>
  <div class="restaurant-card food-card overflow-hidden cursor-pointer" @click="$emit('click')">
    <div class="relative">
      <img :src="restaurant.image || 'https://via.placeholder.com/400x200?text=🍲'" 
           :alt="restaurant.name" class="w-full h-48 object-cover" />
      <div v-if="restaurant.discount" 
           class="absolute top-2 left-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
        {{ restaurant.discount }}
      </div>
      <div v-if="restaurant.is_new" 
           class="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
        新店
      </div>
      <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
        <div class="flex items-center text-white text-sm">
          <span class="mr-1">⭐</span>
          <span class="font-bold">{{ restaurant.rating?.toFixed(1) || '暂无' }}</span>
          <span class="mx-2 text-white/70">|</span>
          <span>人均 ¥{{ restaurant.avg_price || '--' }}</span>
        </div>
      </div>
    </div>
    <div class="p-4">
      <h3 class="text-lg font-bold text-food-text mb-2 truncate">{{ restaurant.name }}</h3>
      <div class="flex flex-wrap gap-1 mb-2">
        <el-tag v-for="tag in (restaurant.cuisine_tags || []).slice(0, 3)" 
                :key="tag" size="small" type="warning" effect="plain" class="text-xs">
          {{ tag }}
        </el-tag>
      </div>
      <p v-if="restaurant.ai_summary" class="text-sm text-gray-500 mb-2 line-clamp-2">
        🤖 {{ restaurant.ai_summary }}
      </p>
      <div class="flex items-center justify-between text-sm text-gray-400">
        <span>📍 {{ restaurant.address || restaurant.distance ? restaurant.distance + 'km' : '--' }}</span>
        <span v-if="restaurant.review_count">{{ restaurant.review_count }}条评价</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Restaurant {
  id?: string; name: string; image?: string; rating?: number; avg_price?: number
  cuisine_tags?: string[]; ai_summary?: string; address?: string; distance?: number
  review_count?: number; discount?: string; is_new?: boolean
}
defineProps<{ restaurant: Restaurant }>()
defineEmits<{ click: [] }>()
</script>

<style scoped>
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
