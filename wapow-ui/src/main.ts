import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createAuth0 } from '@auth0/auth0-vue'

import App from './App.vue'
import router from './router'
import { auth0Config, isAuth0Configured } from './lib/auth0'

const app = createApp(App)

app.use(createPinia())
app.use(router)

if (isAuth0Configured) {
  app.use(
    createAuth0(auth0Config, {
      skipRedirectCallback: window.location.pathname === '/auth/callback'
    })
  )
}

app.mount('#app')
