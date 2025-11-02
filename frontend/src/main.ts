import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// ✅ 引入所有 Element Plus 图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

app.use(router)
app.use(createPinia())
app.use(ElementPlus)

// ✅ 自动注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue as Record<string, any>)) {
  app.component(key, component)
}

app.mount('#app')
