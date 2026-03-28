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
  search: (params: Record<string, any>) => api.get('/restaurants/search', { params }),
  list: (params?: Record<string, any>) => api.get('/restaurants', { params }),
  getById: (id: string) => api.get(`/restaurants/${id}`),
  getRatings: (id: string) => api.get(`/restaurants/${id}/ratings`),
  getReviews: (id: string, params?: Record<string, any>) => api.get(`/restaurants/${id}/reviews`, { params }),
  getRecommendations: (params?: Record<string, any>) => api.get('/restaurants/recommendations', { params }),
  getNearby: (params: Record<string, any>) => api.get('/restaurants/nearby', { params }),
  getDishes: (id: string) => api.get(`/restaurants/${id}/dishes`),
  getCoupons: (id: string) => api.get(`/restaurants/${id}/coupons`),
}

// 搜索
export const searchApi = {
  hotTags: () => api.get('/search/hot-tags'),
  history: () => api.get('/search/history'),
  suggest: (q: string) => api.get('/search/suggest', { params: { q } }),
}

// 排行榜
export const rankingApi = {
  top: (params?: Record<string, any>) => api.get('/rankings', { params }),
  byTaste: () => api.get('/rankings/taste'),
  byValue: () => api.get('/rankings/value'),
  byDistance: (params: Record<string, any>) => api.get('/rankings/distance', { params }),
  byPopularity: () => api.get('/rankings/popularity'),
  byNewStore: () => api.get('/rankings/new'),
}

// 笔记
export const noteApi = {
  list: (params?: Record<string, any>) => api.get('/notes', { params }),
  getById: (id: string) => api.get(`/notes/${id}`),
  create: (data: Record<string, any>) => api.post('/notes', data),
  update: (id: string, data: Record<string, any>) => api.put(`/notes/${id}`, data),
  delete: (id: string) => api.delete(`/notes/${id}`),
  like: (id: string) => api.post(`/notes/${id}/like`),
}

// 用户/口味画像
export const profileApi = {
  getTasteProfile: () => api.get('/profile/taste'),
  updateTasteProfile: (data: Record<string, any>) => api.put('/profile/taste', data),
  getPreferences: () => api.get('/profile/preferences'),
  getSearchHistory: () => api.get('/profile/search-history'),
  getTodayRecommendations: () => api.get('/profile/today-recommendations'),
}

// 收藏
export const favoriteApi = {
  list: (group?: string) => api.get('/favorites', { params: { group } }),
  add: (data: { restaurant_id: string; group: string }) => api.post('/favorites', data),
  remove: (id: string) => api.delete(`/favorites/${id}`),
  move: (id: string, group: string) => api.put(`/favorites/${id}`, { group }),
  getGroups: () => api.get('/favorites/groups'),
  createGroup: (name: string) => api.post('/favorites/groups', { name }),
}

// 天气
export const weatherApi = {
  getCurrent: () => api.get('/weather'),
  getRecommendation: () => api.get('/weather/recommendation'),
}

// 心情推荐
export const moodApi = {
  recommend: (mood: string) => api.get('/mood/recommend', { params: { mood } }),
}

// 随机推荐
export const randomApi = {
  get: (params?: Record<string, any>) => api.get('/random', { params }),
}

export default api
