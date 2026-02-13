import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { useAuthStore } from '@/stores/auth'
import { isAuth0Configured } from '@/lib/auth0'

const PUBLIC_ROUTES = ['login', 'auth-callback']

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'home',
      redirect: '/sports'
    },
    {
      path: '/story/:videoId/:category?',
      name: 'story',
      component: () => import('../views/StoryView.vue')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue')
    },
    {
      path: '/saved',
      name: 'saved',
      component: () => import('../views/SavedView.vue')
    },
    {
      path: '/pin-board',
      name: 'pin-board',
      component: () => import('../views/PinBoardView.vue')
    },
    {
      path: '/article/:url/:title?',
      name: 'article',
      component: () => import('../views/ArticleView.vue')
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('../views/AuthCallbackView.vue'),
      meta: { public: true }
    },
    {
      path: '/:category',
      name: 'category',
      component: () => import('../views/HomeView.vue')
    }
  ]
})

router.beforeEach(async (to, _from, next) => {
  if (!isAuth0Configured || to.meta.public || PUBLIC_ROUTES.includes(to.name as string)) {
    return next()
  }
  const authStore = useAuthStore()
  // Wait for Auth0 to finish checking session
  if (authStore.isLoading) {
    await new Promise<void>((resolve) => {
      const unwatch = authStore.$subscribe((_, state) => {
        if (!state.isLoading) {
          unwatch()
          resolve()
        }
      })
      // Timeout: if still loading after 3s, proceed (avoid infinite wait)
      setTimeout(() => {
        unwatch()
        resolve()
      }, 3000)
    })
  }
  if (authStore.isAuthenticated) {
    return next()
  }
  next({ path: '/login', query: { redirect: to.fullPath } })
})

export default router
