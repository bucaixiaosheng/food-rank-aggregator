<template>
  <div class="filter-panel bg-white rounded-xl shadow-sm p-5">
    <h3 class="font-bold text-food-text mb-4">筛选条件</h3>
    
    <!-- 价格范围 -->
    <div class="mb-5">
      <h4 class="text-sm font-semibold text-gray-500 mb-2">人均价格</h4>
      <el-slider v-model="filters.priceRange" :min="0" :max="500" :step="10" range
                 :format-tooltip="(v: number) => `¥${v}`" />
      <div class="flex justify-between text-xs text-gray-400 mt-1">
        <span>¥{{ filters.priceRange[0] }}</span>
        <span>¥{{ filters.priceRange[1] }}</span>
      </div>
    </div>

    <!-- 距离 -->
    <div class="mb-5">
      <h4 class="text-sm font-semibold text-gray-500 mb-2">距离范围</h4>
      <el-radio-group v-model="filters.distance" size="small" class="flex flex-wrap gap-1">
        <el-radio-button :value="1">1km</el-radio-button>
        <el-radio-button :value="3">3km</el-radio-button>
        <el-radio-button :value="5">5km</el-radio-button>
        <el-radio-button :value="10">10km</el-radio-button>
        <el-radio-button :value="0">不限</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 评分 -->
    <div class="mb-5">
      <h4 class="text-sm font-semibold text-gray-500 mb-2">最低评分</h4>
      <el-rate v-model="filters.minRating" show-text :texts="['不限','3.0','3.5','4.0','4.5']" />
    </div>

    <!-- 菜系 -->
    <div class="mb-5">
      <h4 class="text-sm font-semibold text-gray-500 mb-2">菜系</h4>
      <div class="flex flex-wrap gap-2">
        <el-check-tag v-for="cuisine in cuisines" :key="cuisine" 
                      :checked="filters.cuisines.includes(cuisine)"
                      @change="toggleCuisine(cuisine)"
                      class="text-sm">{{ cuisine }}</el-check-tag>
      </div>
    </div>

    <!-- 排序 -->
    <div class="mb-4">
      <h4 class="text-sm font-semibold text-gray-500 mb-2">排序方式</h4>
      <el-select v-model="filters.sortBy" class="w-full" size="small">
        <el-option label="综合推荐" value="default" />
        <el-option label="评分最高" value="rating" />
        <el-option label="距离最近" value="distance" />
        <el-option label="价格最低" value="price_asc" />
        <el-option label="价格最高" value="price_desc" />
        <el-option label="好评最多" value="reviews" />
      </el-select>
    </div>

    <el-button type="primary" @click="$emit('apply', filters)" class="w-full" color="#ff6b35">
      应用筛选
    </el-button>
    <el-button @click="resetFilters" class="w-full mt-2">重置</el-button>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const cuisines = ['川菜','粤菜','湘菜','日料','韩料','西餐','火锅','烧烤','东南亚','甜品','面食','快餐']

const defaultFilters = () => ({
  priceRange: [0, 500] as number[],
  distance: 5,
  minRating: 0,
  cuisines: [] as string[],
  sortBy: 'default',
})

const filters = reactive(defaultFilters())

const emit = defineEmits<{ apply: [f: typeof filters] }>()

const toggleCuisine = (c: string) => {
  const idx = filters.cuisines.indexOf(c)
  idx >= 0 ? filters.cuisines.splice(idx, 1) : filters.cuisines.push(c)
}

const resetFilters = () => Object.assign(filters, defaultFilters())
watch(filters, () => emit('apply', filters), { deep: true })
</script>
