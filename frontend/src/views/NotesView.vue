<template>
  <div class="notes-view">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-3xl font-bold text-food-text">📝 探店笔记</h2>
      <el-button type="primary" color="#ff6b35" @click="showPublish = true" round>✏️ 发布笔记</el-button>
    </div>

    <!-- 排序 -->
    <div class="flex items-center gap-4 mb-6">
      <el-radio-group v-model="sortBy" @change="fetchNotes">
        <el-radio-button value="hot">🔥 最热</el-radio-button>
        <el-radio-button value="new">🕐 最新</el-radio-button>
      </el-radio-group>
      <el-input v-model="searchKey" placeholder="搜索笔记" class="w-60" clearable size="small" prefix-icon="Search" />
    </div>

    <!-- 瀑布流笔记 -->
    <div class="columns-1 md:columns-2 lg:columns-3 gap-5 space-y-5">
      <div v-for="note in notes" :key="note.id" 
           class="break-inside-avoid food-card overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
           @click="$router.push(`/notes/${note.id}`)">
        <img v-if="note.images?.[0]" :src="note.images[0]" class="w-full h-48 object-cover" />
        <div class="p-4">
          <h3 class="font-bold text-food-text mb-2 line-clamp-2">{{ note.title }}</h3>
          <p class="text-sm text-gray-500 mb-3 line-clamp-3">{{ note.content }}</p>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-full bg-food-secondary flex items-center justify-center text-xs">{{ note.author?.[0] || '👤' }}</div>
              <span class="text-xs text-gray-500">{{ note.author }}</span>
            </div>
            <div class="flex items-center gap-3 text-xs text-gray-400">
              <span>❤️ {{ note.likes }}</span>
              <span>💬 {{ note.comments }}</span>
              <span>⭐ {{ note.rating }}</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-1 mt-2">
            <el-tag v-for="tag in (note.tags || []).slice(0, 3)" :key="tag" size="small" effect="plain" type="info">{{ tag }}</el-tag>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="!notes.length" description="暂无笔记" />

    <!-- 发布笔记对话框 -->
    <el-dialog v-model="showPublish" title="发布探店笔记" width="600px">
      <el-form :model="publishForm" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="publishForm.title" placeholder="分享你的探店体验" />
        </el-form-item>
        <el-form-item label="餐厅">
          <el-input v-model="publishForm.restaurant" placeholder="餐厅名称" />
        </el-form-item>
        <el-form-item label="评分">
          <el-rate v-model="publishForm.rating" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="publishForm.content" type="textarea" :rows="5" placeholder="详细说说你的感受..." />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="publishForm.tags" multiple filterable allow-create placeholder="添加标签" class="w-full">
            <el-option label="好吃" value="好吃" />
            <el-option label="环境好" value="环境好" />
            <el-option label="性价比高" value="性价比高" />
            <el-option label="排队" value="排队" />
          </el-select>
        </el-form-item>
        <el-form-item label="图片">
          <div class="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center cursor-pointer hover:border-food-primary transition-colors">
            <div class="text-4xl mb-2">📷</div>
            <p class="text-gray-400">点击上传图片</p>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPublish = false">取消</el-button>
        <el-button type="primary" color="#ff6b35" @click="publishNote">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { noteApi } from '@/api'

const notes = ref<any[]>([])
const sortBy = ref('hot')
const searchKey = ref('')
const showPublish = ref(false)
const publishForm = ref({ title: '', restaurant: '', rating: 5, content: '', tags: [] as string[], images: [] as string[] })

const mockNotes = () => [
  { id: '1', title: '蜀大侠探店记录｜毛肚太新鲜了！', content: '周末和朋友来吃，毛肚七上八下涮着吃太绝了。番茄锅底也很浓郁，推荐搭配手工虾滑。服务态度超好，主动加汤递围裙。', author: '美食达人小王', likes: 342, comments: 56, rating: 5, tags: ['火锅','川菜','探店'], images: ['https://via.placeholder.com/400x300?text=火锅1','https://via.placeholder.com/400x300?text=火锅2'] },
  { id: '2', title: '鮨一日料｜约会首选', content: '环境非常优雅，适合约会。刺身拼盘非常新鲜，甜虾入口即化。午市性价比很高，推荐168元套餐。', author: '吃货小姐姐', likes: 218, comments: 32, rating: 4, tags: ['日料','约会','刺身'], images: ['https://via.placeholder.com/400x200?text=日料'] },
  { id: '3', title: '太二酸菜鱼｜排队2小时值得吗？', content: '周末排了两个小时，酸菜鱼确实好吃，鱼肉嫩滑，汤底酸辣开胃。不过等太久有点累，建议工作日去。', author: '探店老司机', likes: 156, comments: 45, rating: 4, tags: ['酸菜鱼','排队','粤菜'], images: [] },
  { id: '4', title: '兰州拉面｜20年的老味道', content: '从上学就在吃的拉面馆，20年了味道一直没变。牛骨汤底浓郁，拉面劲道有嚼劲。加一份牛肉才8块钱，太良心了。', author: '老饕食客', likes: 89, comments: 12, rating: 5, tags: ['面食','老店','平价'], images: ['https://via.placeholder.com/400x300?text=拉面'] },
  { id: '5', title: '泰香米｜一口回到曼谷', content: '冬阴功汤酸辣过瘾，芒果糯米饭甜度刚好。青木瓜沙拉很清爽，推荐加辣版。整体性价比不错，两人吃200左右。', author: '旅行美食家', likes: 67, comments: 8, rating: 4, tags: ['泰国菜','东南亚'], images: ['https://via.placeholder.com/400x400?text=泰国菜'] },
  { id: '6', title: '海底捞服务天花板', content: '服务真的没话说，美甲、擦鞋、零食水果随便拿。番茄锅底+麻辣锅底双拼绝配。甩面表演也很精彩！', author: '火锅爱好者', likes: 203, comments: 28, rating: 5, tags: ['火锅','服务'], images: ['https://via.placeholder.com/400x250?text=海底捞'] },
]

onMounted(async () => { try { notes.value = (await noteApi.list({ sort: sortBy.value }) as any)?.data || [] } catch { notes.value = mockNotes() } })

const fetchNotes = async () => { notes.value = mockNotes().sort((a, b) => sortBy.value === 'hot' ? b.likes - a.likes : 0) }
const publishNote = async () => {
  try { await noteApi.create(publishForm.value) } catch {}
  showPublish.value = false
  notes.value.unshift({ id: Date.now().toString(), ...publishForm.value, author: '我', likes: 0, comments: 0 })
}
</script>

<style scoped>
.line-clamp-2, .line-clamp-3 { display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; }
.line-clamp-2 { -webkit-line-clamp: 2; }
.line-clamp-3 { -webkit-line-clamp: 3; }
</style>
