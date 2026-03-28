<template>
  <div class="search-bar relative">
    <div class="relative flex items-center">
      <el-icon class="absolute left-4 text-gray-400 text-xl"><Search /></el-icon>
      <input v-model="query" type="text" :placeholder="placeholder"
             @keyup.enter="$emit('search', query)"
             class="w-full pl-12 pr-24 py-4 rounded-2xl border-2 border-food-secondary bg-white 
                    focus:border-food-primary focus:outline-none transition-colors text-lg shadow-sm" />
      <button @click="$emit('search', query)"
              class="absolute right-2 bg-food-primary text-white px-6 py-2 rounded-xl hover:bg-food-accent transition-colors font-medium">
        搜索
      </button>
    </div>
    <!-- 热门搜索 -->
    <div v-if="showHot && hotTags.length" class="mt-3 flex flex-wrap gap-2">
      <span class="text-sm text-gray-400">热门：</span>
      <button v-for="tag in hotTags" :key="tag" @click="query = tag; $emit('search', tag)"
              class="text-sm px-3 py-1 bg-food-secondary/50 rounded-full hover:bg-food-secondary transition-colors">
        {{ tag }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { searchApi } from '@/api'

const props = withDefaults(defineProps<{
  placeholder?: string; showHot?: boolean; modelValue?: string
}>(), { placeholder: '搜索餐厅、菜系、美食...', showHot: true, modelValue: '' })

const emit = defineEmits<{ search: [q: string]; 'update:modelValue': [q: string] }>()
const query = ref(props.modelValue)
const hotTags = ref<string[]>([])

onMounted(async () => {
  try { const res: any = await searchApi.hotTags(); hotTags.value = res.data || res || [] } catch {}
})
</script>
