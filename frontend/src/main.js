import App from './App.vue'

import { createApp } from 'vue'
import Antd from 'ant-design-vue';
import router from './router';
import { setupAxiosInterceptor } from './utils/auth';

console.log('当前API基地址:', import.meta.env.VITE_API_BASE)
const app = createApp(App);
app.use(Antd)
app.use(router)
app.mount('#app')
setupAxiosInterceptor();
