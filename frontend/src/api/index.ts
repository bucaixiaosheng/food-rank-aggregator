import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}, (error) => Promise.reject(error))

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// 餐厅相关
export const restaurantApi = {
  search: (params: Record<string, any>) => api.post('/search', { query: params.q || params.query || '', location: params.location, filters: params.filters }),
  list: (params?: Record<string, any>) => api.get('/restaurants', { params }),
  getById: (id: string | number) => api.get(`/restaurants/${id}`),
  getRatings: (id: string | number) => api.get(`/restaurants/${id}`).then(res => ({ ...res, data: res?.data?.platform_ratings || [] })),
  getReviews: (id: string | number, params?: Record<string, any>) => api.get('/notes', { params: { restaurant_id: id, ...params } }),
  getRecommendations: (params?: Record<string, any>) => api.get('/recommendations/daily', { params }).then(res => ({ ...res, data: res?.data?.recommendations || [] })),
  getNearby: (params: Record<string, any>) => api.get('/restaurants/filter', { params: { ...params, distance_max: params.radius || 5 } }),
  getDishes: (id: string | number) => Promise.resolve({ data: [] }), // 暂无菜品API，返回空数组
  getCoupons: (id: string | number) => Promise.resolve({ data: [] }), // 暂无优惠券API，返回空数组
}

// 搜索
export const searchApi = {
  hotTags: () => api.get('/users/taste-tags').then(res => ({ ...res, data: res?.data?.flavor_tags || [] })),
  history: () => Promise.resolve({ data: [] }), // 暂无搜索历史API
  suggest: (q: string) => api.post('/search', { query: q }).then(res => ({ ...res, data: res?.data?.data || [] })),
}

// 排行榜
export const rankingApi = {
  top: (params?: Record<string, any>) => api.get('/rankings', { params }),
  byTaste: () => api.get('/rankings', { params: { ranking_type: 'taste' } }),
  byValue: () => api.get('/rankings', { params: { ranking_type: 'value' } }),
  byDistance: (params: Record<string, any>) => api.get('/rankings', { params: { ranking_type: 'distance', ...params } }),
  byPopularity: () => api.get('/rankings', { params: { ranking_type: 'hot' } }),
  byNewStore: () => api.get('/rankings', { params: { ranking_type: 'new' } }),
}

// 笔记
export const noteApi = {
  list: (params?: Record<string, any>) => api.get('/notes', { params }),
  getById: (id: string | number) => api.get(`/notes/${id}`),
  create: (data: Record<string, any>) => api.post('/notes', data),
  update: (id: string | number, data: Record<string, any>) => Promise.resolve({ data: { message: '暂不支持更新' } }), // 暂无更新API
  delete: (id: string | number) => Promise.resolve({ data: { message: '暂不支持删除' } }), // 暂无删除API
  like: (id: string | number) => api.post(`/notes/${id}/like`),
}

// 用户/口味画像
export const profileApi = {
  getTasteProfile: () => api.get('/users/profile').then(res => ({ ...res, data: res?.data?.taste_profile || {} })),
  updateTasteProfile: (data: Record<string, any>) => api.put('/users/profile', data),
  getPreferences: () => api.get('/users/taste-tags'),
  getSearchHistory: () => Promise.resolve({ data: [] }), // 暂无搜索历史API
  getTodayRecommendations: () => api.get('/recommendations/daily').then(res => ({ ...res, data: res?.data?.recommendations || [] })),
}

// 收藏
export const favoriteApi = {
  list: (group?: string) => api.get('/favorites', { params: { target_type: group ? undefined : 'restaurant', group_name: group } }),
  add: (data: { restaurant_id: string | number; group: string }) => api.post('/favorites', { target_type: 'restaurant', target_id: data.restaurant_id, group_name: data.group }),
  remove: (id: string | number) => api.delete(`/favorites/${id}`),
  move: (id: string | number, group: string) => Promise.resolve({ data: { message: '暂不支持移动分组' } }), // 暂无移动API
  getGroups: () => Promise.resolve({ data: [] }), // 暂无分组API
  createGroup: (name: string) => Promise.resolve({ data: { message: '暂不支持创建分组' } }), // 暂无创建分组API
}

// 天气
export const weatherApi = {
  getCurrent: () => Promise.resolve({ data: { weather: 'sunny', temp: '26°C' } }), // 暂无当前天气API
  getRecommendation: () => api.get('/recommendations/weather'),
}

// 心情推荐
export const moodApi = {
  recommend: (mood: string) => api.post('/recommendations/mood', { mood }),
}

// 随机推荐
export const randomApi = {
  get: (params?: Record<string, any>) => api.get('/recommendations/random', { params }),
}

export default api
