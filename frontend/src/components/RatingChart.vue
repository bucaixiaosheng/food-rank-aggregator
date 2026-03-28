<template>
  <div class="rating-chart bg-white rounded-xl p-5 shadow-sm">
    <h3 class="font-bold text-food-text mb-4">📊 多平台评分对比</h3>
    <div class="space-y-4">
      <div v-for="platform in platforms" :key="platform.name" class="flex items-center gap-3">
        <span class="w-20 text-sm font-medium text-gray-600 shrink-0">{{ platform.name }}</span>
        <div class="flex-1 h-8 bg-gray-100 rounded-full overflow-hidden relative">
          <div class="h-full rounded-full transition-all duration-700 ease-out"
               :style="{ width: (platform.score / 5 * 100) + '%', backgroundColor: platform.color }">
          </div>
          <span class="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-700">
            {{ platform.score?.toFixed(1) || '--' }}
          </span>
        </div>
      </div>
    </div>
    <!-- 汇总 -->
    <div class="mt-5 pt-4 border-t border-gray-100 flex justify-between items-center">
      <span class="text-gray-500 text-sm">综合评分</span>
      <div class="flex items-center gap-1">
        <span class="text-3xl font-bold text-food-primary">{{ avgScore }}</span>
        <span class="text-gray-400 text-sm">/ 5.0</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Platform { name: string; score: number; color: string }
const props = defineProps<{ ratings: Platform[] }>()

const platforms = computed(() => {
  const defaults = [
    { name: '美团', color: '#ffc107' },
    { name: '大众点评', color: '#ff6b35' },
    { name: '小红书', color: '#fe2c55' },
  ]
  return defaults.map((d, i) => ({ ...d, ...props.ratings[i] }))
})

const avgScore = computed(() => {
  const valid = platforms.value.filter(p => p.score > 0)
  return valid.length ? (valid.reduce((s, p) => s + p.score, 0) / valid.length).toFixed(1) : '--'
})
</script>
