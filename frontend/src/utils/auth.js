import axios from "axios";

// 创建 axios 实例
export const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE,
    timeout: 10000
});

// 请求拦截器
export function setupAxiosInterceptor() {
    apiClient.interceptors.request.use(config => {
        // 登录请求以及刷新令牌时不处理
        if (!config.url.includes('/accounts/login/') && 
        !config.url.includes('/accounts/refresh/')){
            const token = sessionStorage.getItem('access_token');
            console.log("拦截成功：" + token)
            if(token){
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    });

    // 相应拦截器处理token刷新
    apiClient.interceptors.response.use(
        response => response, 
        async error => {
            console.log("认证错误拦截成功!")
            const originalRequest = error.config;
            // 登录接口不触发用户刷新
            if (error.request?.status === 401 && 
                !originalRequest.url.includes('/accounts/login') &&
                !originalRequest._retry) {
                console.log('Access Token 已过期！')
                originalRequest._retry = true;
                try {
                    const refreshResponse = await refreshAccessToken();
                    sessionStorage.setItem('access_token', refreshResponse.access);
                    sessionStorage.setItem('role', refreshResponse.role);
                    sessionStorage.setItem('user_id', refreshResponse.user_id);
                    sessionStorage.setItem('name', refreshResponse.name);
                    originalRequest.headers.Authorization = `Bearer ${newToken}`;
                    return apiClient(originalRequest);
                } catch(refreshError) {
                    // 跳转登陆
                    // window.location.href = '/';
                    return Promise.reject(refreshError);
                }
            }
            return Promise.reject(error);
        }
    );
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token') || document.cookie.replace(/(?:(?:^|.*;\s*)refresh_token\s*=\s*([^;]*).*$)|^.*$/, '$1');

    if(!refreshToken) throw new Error('No refresh token avaiable');

    const response = await apiClient.post('/accounts/refresh/', {
        refresh: refreshToken
    });
    return response.data;
}