import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'
import { createApp } from 'vue' // Импортируем createApp напрямую
import AuthModal from '@/admin/views/AuthModal.vue' // Импортируем компонент напрямую
import store from '/src/store/index.js';
// 1. Создаем роутер и экспортируем его
const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'page1',
            component: () => import('./views/Page1.vue'),
        },
        {
            path: '/page2',
            name: 'page2',
            component: () => import('./views/Page2.vue')
        },
        {
            path: '/profile',
            name: 'profile',
            component: () => import('./views/Profile.vue'),
            meta: {
                requiresAuth: true
            }
        },
        {
            path: '/payment/:planId',
            name: 'payment',
            component: () => import('./views/PaymentPage.vue'),
            meta: { requiresAuth: true }
        },

        {
            path: '/admin',
            name: 'admin',
            component: () => import('@/admin/views/AdminPanel.vue'),
            meta: {
                requiresAdmin: true,
                hideHeaderFooter: true
            }
        },
        {
            path: '/admin/login',
            name: 'admin-login',
            component: () => import('@/admin/views/AuthModal.vue'),
            meta: {
              hideHeaderFooter: true
            }
          }
    ]
})


router.afterEach(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' }) // Плавная прокрутка
})

async function verifyAdminAuth() {
    const accessToken = localStorage.getItem('adminAccessToken')
    const refreshToken = localStorage.getItem('adminRefreshToken')
  
    if (!accessToken && !refreshToken) {
      return false
    }
  
    try {
      // Проверяем access token
      await axios.get('/api/admin/check', {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      })
      return true
    } catch (error) {
      if (error.response?.status === 401 && refreshToken) {
        // Пробуем обновить токен
        try {
          const response = await axios.post('/api/admin/refresh-token', { refreshToken })
          localStorage.setItem('adminAccessToken', response.data.accessToken)
          localStorage.setItem('adminRefreshToken', response.data.refreshToken)
          return true
        } catch (refreshError) {
          console.error('Refresh token failed:', refreshError)
          return false  
        }
      }
      return false
    }
  }

// Функция показа модалки авторизации
async function showAdminAuthModal() {
    return new Promise((resolve) => {
      const modalDiv = document.createElement('div')
      document.body.appendChild(modalDiv)
  
      // Импортирует компоненты
      const modalApp = createApp(AuthModal, {
        onSuccess: () => {
          modalApp.unmount()
          document.body.removeChild(modalDiv)
          resolve(true)
        },
        onCancel: () => {
          modalApp.unmount()
          document.body.removeChild(modalDiv)
          resolve(false)
        }
      })
  
      modalApp.mount(modalDiv)
    })
  }
  

  router.beforeEach(async (to, from, next) => {
    // Проверка обычных защищенных маршрутов 
    if (to.matched.some(record => record.meta.requiresAuth)) {
      // Если store еще не инициализирован, ждем загрузки пользователя
      if (!store.state.auth.initialized) {
        try {
          await store.dispatch('fetchUser')
        } catch (error) {
          console.error('Ошибка загрузки пользователя:', error)
        }
      }
      
      if (!store.getters.isAuthenticated) {
        next('/')
        return
      }
    }
  
    // Проверка админских маршрутов
    if (to.matched.some(record => record.meta.requiresAdmin)) {
      try {
        const isAuthenticated = await verifyAdminAuth()
        
        if (!isAuthenticated) {
          // Если пытаемся попасть на /admin - редирект на /admin/login
          if (to.path === '/admin') {
            next('/admin/login')
            return
          }
          
          // Для всех других админских маршрутов
          next('/admin/login?redirect=' + encodeURIComponent(to.fullPath))
          return
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        next('/admin/login')
        return
      }
    }
  
    // Если это страница входа админа и уже авторизован - редирект в админку
    if (to.path === '/admin/login') {
      const isAuthenticated = await verifyAdminAuth()
      if (isAuthenticated) {
        const redirectUrl = to.query.redirect || '/admin'
        next(redirectUrl)
        return
      }
    }
  
    // Во всех остальных случаях продолжаем навигацию
    next()
  })

export default router