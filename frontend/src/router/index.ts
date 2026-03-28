import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/restaurants', name: 'restaurants', component: () => import('@/views/RestaurantsView.vue') },
    { path: '/restaurant/:id', name: 'restaurant-detail', component: () => import('@/views/RestaurantDetailView.vue') },
    { path: '/rankings', name: 'rankings', component: () => import('@/views/RankingsView.vue') },
    { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue') },
    { path: '/map', name: 'map', component: () => import('@/views/MapView.vue') },
    { path: '/favorites', name: 'favorites', component: () => import('@/views/FavoritesView.vue') },
    { path: '/notes', name: 'notes', component: () => import('@/views/NotesView.vue') },
    { path: '/notes/:id', name: 'note-detail', component: () => import('@/views/NoteDetailView.vue') },
    { path: '/mood', name: 'mood', component: () => import('@/views/MoodView.vue') },
    { path: '/random', name: 'random', component: () => import('@/views/RandomView.vue') },
  ],
})

export default router
