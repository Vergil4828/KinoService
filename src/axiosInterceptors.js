import axios from 'axios';
import router from './router.js';
import store from './store'; // Путь к схрону
const setupInterceptors = (router) => {
  // Request interceptor
  axios.interceptors.request.use(config => {
    const token = localStorage.getItem('accessToken');
    console.log('Токен из localStorage:', token);  // Логируем
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Добавляем токен в заголовок:', config.headers.Authorization);  // Логируем
    }
    return config;
  });

  // Response interceptor
  axios.interceptors.response.use(
    response => response,
    async error => {
      const originalRequest = error.config;

      // Пропускаем запросы на refresh-token и login (обычные и админские)
      if (originalRequest.url.includes('/api/refresh-token') ||
        originalRequest.url.includes('/api/login') ||
        originalRequest.url.includes('/api/admin/refresh-token') ||
        originalRequest.url.includes('/api/admin/login')) {
        return Promise.reject(error);
      }

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        // Определяем, админский ли это запрос
        const isAdminRequest = originalRequest.url.includes('/api/admin/');
        const refreshTokenKey = isAdminRequest ? 'adminRefreshToken' : 'refreshToken';
        const refreshToken = localStorage.getItem(refreshTokenKey);

        if (!refreshToken) {
          await store.dispatch('logout');
          return Promise.reject(error);
        }

        try {
          const refreshEndpoint = isAdminRequest
            ? '/api/admin/refresh-token'
            : '/api/refresh-token';

          const { data } = await axios.post(refreshEndpoint, { refreshToken });

          // Сохраняем токены с правильными ключами
          const tokenKey = isAdminRequest ? 'adminAccessToken' : 'accessToken';
          const newRefreshTokenKey = isAdminRequest ? 'adminRefreshToken' : 'refreshToken';

          localStorage.setItem(tokenKey, data.accessToken);
          if (data.refreshToken) {
            localStorage.setItem(newRefreshTokenKey, data.refreshToken);
          }

          originalRequest.headers.Authorization = `Bearer ${data.token}`;
          return axios(originalRequest);
        } catch (err) {
          await store.dispatch('logout');
          return Promise.reject(err);
        }
      }

      return Promise.reject(error);
    }
  );
};

export default setupInterceptors;