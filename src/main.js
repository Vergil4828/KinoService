  // Запросы к серверу
  import axios from "axios";
  axios.defaults.baseURL = 'http://localhost:3005';

  // Работа с датой
  import dayjs from 'dayjs';
  import 'dayjs/locale/ru';
  import relativeTime from 'dayjs/plugin/relativeTime';
  dayjs.locale('ru');
  dayjs.extend(relativeTime)

  // Всё для vue
  import { createApp } from 'vue'
  import App from './App.vue'
  import Notifications from '@kyvg/vue3-notification'
  import store from './store'
  import router from './router.js';
  import setupInterceptors from './axiosInterceptors';
  setupInterceptors(router);
  // Рендер в HTML
  const app = createApp(App)

  app.use(store)
  app.use(router)
  app.use(Notifications)

  // Инициализация аутентификации, затем монтируем приложение
  store.dispatch('initializeAuth').then(() => {
    app.mount('#app')
  })