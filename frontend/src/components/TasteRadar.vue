<template>
  <div class="taste-radar bg-white rounded-xl p-5 shadow-sm">
    <h3 class="font-bold text-food-text mb-4">🎨 我的口味画像</h3>
    <div class="flex justify-center">
      <svg viewBox="0 0 300 300" class="w-64 h-64">
        <!-- 背景网格 -->
        <polygon v-for="level in [0.2, 0.4, 0.6, 0.8, 1.0]" :key="level"
                 :points="gridPoints(level)" fill="none" stroke="#e5e7eb" stroke-width="1" />
        <!-- 轴线 -->
        <line v-for="(_, i) in labels" :key="'axis'+i"
              x1="150" y1="150" :x2="axisPoints[i].x" :y2="axisPoints[i].y" stroke="#d1d5db" stroke-width="1" />
        <!-- 数据区域 -->
        <polygon :points="dataPoints" fill="rgba(255,107,53,0.25)" stroke="#ff6b35" stroke-width="2" />
        <!-- 数据点 -->
        <circle v-for="(p, i) in dataPointList" :key="'dot'+i" :cx="p.x" :cy="p.y" r="4" fill="#ff6b35" />
        <!-- 标签 -->
        <text v-for="(label, i) in labels" :key="'label'+i"
              :x="labelPoints[i].x" :y="labelPoints[i].y"
              text-anchor="middle" dominant-baseline="middle" class="text-xs fill-gray-600">
          {{ label }}
        </text>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const labels = ['辣', '甜', '酸', '咸', '鲜', '清淡']
const props = withDefaults(defineProps<{
  values?: number[]
}>(), { values: () => [0.7, 0.5, 0.4, 0.6, 0.8, 0.3] })

const cx = 150, cy = 150, r = 110

const getPoint = (index: number, value: number) => {
  const angle = (Math.PI * 2 * index) / labels.length - Math.PI / 2
  return { x: cx + r * value * Math.cos(angle), y: cy + r * value * Math.sin(angle) }
}

const axisPoints = computed(() => labels.map((_, i) => getPoint(i, 1)))
const labelPoints = computed(() => labels.map((_, i) => getPoint(i, 1.18)))

const gridPoints = (level: number) =>
  labels.map((_, i) => { const p = getPoint(i, level); return `${p.x},${p.y}` }).join(' ')

const dataPointList = computed(() => props.values.map((v, i) => getPoint(i, v)))
const dataPoints = computed(() => dataPointList.value.map(p => `${p.x},${p.y}`).join(' '))
</script>
