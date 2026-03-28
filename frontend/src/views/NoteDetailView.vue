<template>
  <div class="note-detail" v-if="note">
    <button @click="$router.back()" class="text-food-primary hover:underline mb-4 inline-flex items-center gap-1 text-sm">
      ← 返回笔记列表
    </button>

    <div class="food-card p-6 md:p-8 max-w-3xl mx-auto">
      <!-- 标题 -->
      <h1 class="text-2xl font-bold text-food-text mb-4">{{ note.title }}</h1>
      
      <!-- 作者信息 -->
      <div class="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
        <div class="w-12 h-12 rounded-full bg-food-secondary flex items-center justify-center text-lg">{{ note.author?.[0] }}</div>
        <div>
          <div class="font-bold text-food-text">{{ note.author }}</div>
          <div class="text-sm text-gray-400">{{ note.time }} · {{ note.read_count }}阅读</div>
        </div>
        <div class="ml-auto">
          <el-rate v-model="note.rating" disabled show-score text-color="#ff9900" />
        </div>
      </div>

      <!-- 图片 -->
      <div v-if="note.images?.length" class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
        <img v-for="(img, i) in note.images" :key="i" :src="img" class="rounded-xl w-full object-cover" />
      </div>

      <!-- 正文 -->
      <div class="text-gray-700 leading-relaxed whitespace-pre-wrap mb-6">{{ note.content }}</div>

      <!-- 标签 -->
      <div class="flex flex-wrap gap-2 mb-6">
        <el-tag v-for="tag in note.tags" :key="tag" effect="plain">{{ tag }}</el-tag>
      </div>

      <!-- 关联餐厅 -->
      <div v-if="note.restaurant" class="bg-food-bg rounded-xl p-4 flex items-center gap-3 mb-6 cursor-pointer hover:shadow-md transition-shadow"
           @click="$router.push(`/restaurant/${note.restaurant_id}`)">
        <div class="w-12 h-12 rounded-lg bg-food-primary/10 flex items-center justify-center text-xl">🍽️</div>
        <div>
          <div class="font-bold text-food-text">{{ note.restaurant }}</div>
          <div class="text-sm text-gray-400">{{ note.restaurant_rating }} · ¥{{ note.restaurant_price }}/人</div>
        </div>
        <span class="ml-auto text-food-primary text-sm">查看餐厅 →</span>
      </div>

      <!-- 互动 -->
      <div class="flex items-center gap-6 pt-4 border-t border-gray-100">
        <button @click="likeNote" class="flex items-center gap-2 text-gray-500 hover:text-red-500 transition-colors">
          <span class="text-xl">{{ liked ? '❤️' : '🤍' }}</span>
          <span>{{ note.likes }}</span>
        </button>
        <button class="flex items-center gap-2 text-gray-500 hover:text-food-primary transition-colors">
          💬 {{ note.comments }} 评论
        </button>
        <button class="flex items-center gap-2 text-gray-500 hover:text-food-primary transition-colors">
          ⭐ 收藏
        </button>
        <button class="flex items-center gap-2 text-gray-500 hover:text-food-primary transition-colors ml-auto">
          ↗️ 分享
        </button>
      </div>

      <!-- 评论区 -->
      <div class="mt-6 pt-6 border-t border-gray-100">
        <h3 class="font-bold text-food-text mb-4">💬 评论 ({{ note.comments }})</h3>
        <div class="flex gap-3 mb-4">
          <el-input v-model="commentText" placeholder="写下你的评论..." />
          <el-button type="primary" color="#ff6b35" @click="addComment">发送</el-button>
        </div>
        <div class="space-y-4">
          <div v-for="c in comments" :key="c.id" class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs shrink-0">{{ c.user?.[0] }}</div>
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium text-sm">{{ c.user }}</span>
                <span class="text-xs text-gray-400">{{ c.time }}</span>
              </div>
              <p class="text-sm text-gray-600">{{ c.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <el-skeleton v-else :rows="12" animated />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { noteApi } from '@/api'

const route = useRoute()
const note = ref<any>(null)
const liked = ref(false)
const commentText = ref('')
const comments = ref<any[]>([])

onMounted(async () => {
  const id = route.params.id as string
  try { note.value = (await noteApi.getById(id) as any)?.data } catch {
    note.value = {
      id, title: '蜀大侠探店记录｜毛肚太新鲜了！', content: '周末和朋友来吃蜀大侠火锅，体验非常棒！\n\n首先是环境，新装修的店面很宽敞明亮，座位间距也够大，不会觉得拥挤。服务员态度非常好，主动帮我们下围裙、递热毛巾。\n\n菜品方面，毛肚绝对是招牌，非常新鲜脆嫩，七上八下涮几秒就能吃了。黄喉也很推荐，口感Q弹。我们点了番茄+牛油双拼锅底，番茄锅底浓郁香甜，牛油锅底麻辣过瘾。\n\n手工虾滑也很惊艳，虾肉含量很高，入口弹牙。红糖糍粑作为甜品收尾也很不错。\n\n价格方面，人均120左右，性价比很高。强烈推荐！',
      author: '美食达人小王', time: '2天前', likes: 342, comments: 56, rating: 5, read_count: 2386,
      tags: ['火锅','川菜','探店','毛肚'],
      images: ['https://via.placeholder.com/600x400?text=火锅1','https://via.placeholder.com/600x400?text=火锅2','https://via.placeholder.com/600x400?text=火锅3'],
      restaurant: '蜀大侠火锅', restaurant_id: '1', restaurant_rating: '⭐ 4.8', restaurant_price: 120,
    }
    comments.value = [
      { id: '1', user: '火锅爱好者', time: '1天前', content: '毛肚确实好吃！下次去试试你推荐的虾滑' },
      { id: '2', user: '美食小白', time: '2天前', content: '看起来好棒，周末去打卡！' },
      { id: '3', user: '辣妹子', time: '3天前', content: '他们家的牛油锅底是真的辣，爱吃辣的必点' },
    ]
  }
})

const likeNote = () => { liked.value = !liked.value; note.value.likes += liked.value ? 1 : -1 }
const addComment = () => {
  if (!commentText.value.trim()) return
  comments.value.unshift({ id: Date.now().toString(), user: '我', time: '刚刚', content: commentText.value })
  commentText.value = ''
}
</script>
