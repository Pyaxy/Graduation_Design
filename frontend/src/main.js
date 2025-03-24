import App from './components/LoginForm.vue'

import { createApp } from 'vue'
import Antd from 'ant-design-vue';

const app = createApp(App);
app.use(Antd)
app.mount('#app')
