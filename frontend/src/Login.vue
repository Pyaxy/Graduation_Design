<script setup>
import axios from 'axios'
import { ref } from 'vue';

const email = ref('')
const password = ref('')

async function login() {
    try{
        const response = await axios.post('http://localhost:8000/accounts/login/', {
            'email': email.value,
            'password': password.value
        },{
            withCredentials: true,
            headers: {   
        'Content-Type': 'application/json'
            }
        }
)

        // 存储token
        localStorage.setItem('access_token', response.data.access)
        localStorage.setItem('refresh_token', response.data.refresh)

        alert('登录成功')
    } catch (error){
        let errorMessage = '登录失败'
        if (error.response) {
            // 请求已发出但服务器响应状态码不在 2xx 范围内
            errorMessage = error.response.data.detail || errorMessage
        } else if (error.request) {
            // 请求已发出但没有收到响应
            errorMessage = '服务器未响应'
        }
        alert(errorMessage)
        console.error('完整错误信息:', error)
        }
}
</script>
<template>
    <div>
        <input v-model="email" required placeholder="邮箱">
        <input type="password" v-model="password" required placeholder="密码">
        <button @click="login">登录</button> 
    </div>
</template>