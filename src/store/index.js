import { createStore } from 'vuex'
import axios from 'axios'
import router from '../router'

export default createStore({
  state: {
    user: {
      // Основная информация
      id: null,
      username: '',
      email: '',
      avatar: '/defaults/default-avatar.png',
      createdAt: null,

      // Статистика и активность
      stats: {
        views: 0,          
        ratings: 0,        
        favorites: 0,      
        watchlist: 0       
      },

      // Подписка и настройки
      subscription: {
        currentPlan: null,       // Текущий активный план
        plans: [],               // Все доступные планы
        history: [],             // История подписок
        loading: false,
        error: null
      },

      // Настройки уведомлений
      notifications: {
        email: true,
        push: false,
        newsletter: true
      },

      wallet: {
        balance: 0,
        transactions: []
      }
    },

    // Состояние аутентификации
    auth: {
      isAuthenticated: false,
      initialized: false,
      error: null,
      loading: false,
    },

    // UI состояния
    ui: {
      isMenuOpen: false,
      modals: {
        login: false,
        register: false
      },
      forms: {
        login: {
          email: '',
          password: ''
        },
        register: {
          username: '',
          email: '',
          password: '',
          confirmPassword: ''
        }
      }
    },
    subscriptionNotification: {
      shown: false,
      subscriptionId: null,
      lastShown: null
    }
  },
  mutations: {
    SET_USER(state, userData) {
      state.user = {
        ...state.user,
        ...userData,
        stats: {
          ...state.user.stats,
          ...(userData.stats || {})
        },
        subscription: {
          ...state.user.subscription,
          currentPlan: userData.subscription?.currentPlan || null,
          history: userData.subscription?.history || []
        },
        notifications: {
          ...state.user.notifications,
          ...(userData.notifications || {})
        },
        wallet: {
          balance: userData.wallet?.balance || 0,
          transactions: userData.wallet?.transactions || []
        }
      }
    },

    UPDATE_USER_STATS(state, stats) {
      state.user.stats = {
        ...state.user.stats,
        ...stats
      }
    },

    UPDATE_USER_SUBSCRIPTION(state, subscription) {
      state.user.subscription = {
        ...state.user.subscription,
        ...subscription
      }
    },

    // Мутации аутентификации
    SET_AUTH(state, { isAuthenticated, error = null }) {
      state.auth.isAuthenticated = isAuthenticated
      state.auth.error = error
    },

    SET_AUTH_LOADING(state, isLoading) {
      state.auth.loading = isLoading
    },

    // Мутации UI
    TOGGLE_MENU(state) {
      state.ui.isMenuOpen = !state.ui.isMenuOpen
    },

    OPEN_MODAL(state, { type }) {
      state.ui.modals[type] = true
      document.body.classList.add('overflow-hidden')
    },

    CLOSE_MODAL(state, type) {
      state.ui.modals[type] = false
      const hasOpenModals = Object.values(state.ui.modals).some(Boolean)
      if (!hasOpenModals) {
        document.body.classList.remove('overflow-hidden')
      }
    },

    RESET_FORM(state, { formType }) {
      state.ui.forms[formType] = {
        email: '',
        password: '',
        ...(formType === 'register' ? {
          username: '',
          confirmPassword: ''
        } : {})
      }
    },

    UPDATE_FORM_FIELD(state, { formType, field, value }) {
      if (state.ui.forms[formType]) {
        state.ui.forms[formType][field] = value
      }
    },
    SET_WALLET_DATA(state, { balance, transactions }) {
      state.user.wallet.balance = balance;
      state.user.wallet.transactions = transactions;
    },
    UPDATE_BALANCE(state, newBalance) {
      state.user.wallet.balance = newBalance;
    },
    ADD_TRANSACTION(state, transaction) {
      state.user.wallet.transactions.unshift(transaction);
    },

    SET_PLANS(state, plans) {
      state.user.subscription.plans = plans;
    },
    SET_CURRENT_SUBSCRIPTION(state, subscription) {
      state.user.subscription.currentPlan = subscription;
    },
    ADD_SUBSCRIPTION_HISTORY(state, subscription) {
      state.user.subscription.history.unshift(subscription);
    },
    SET_SUBSCRIPTION_LOADING(state, loading) {
      state.user.subscription.loading = loading;
    },
    SET_SUBSCRIPTION_ERROR(state, error) {
      state.user.subscription.error = error;
    },

    SET_INITIALIZED(state, initialized) {
      state.auth.initialized = initialized;
    },

    SET_SUBSCRIPTION_NOTIFICATION(state, payload) {
      state.subscriptionNotification = {
        ...state.subscriptionNotification,
        ...payload
      };
    },
    RESET_SUBSCRIPTION_NOTIFICATION(state) {
      state.subscriptionNotification = {
        shown: false,
        subscriptionId: null,
        lastShown: null
      };
    }


  },
  actions: {
    // Аутентификация


    async initializeAuth({ commit, dispatch }) {
      try {
        await dispatch('fetchUser')
      } finally {
        commit('SET_INITIALIZED', true)
      }
    },
    async fetchUser({ commit }) {
      commit('SET_AUTH_LOADING', true)
      try {
        const token = localStorage.getItem('accessToken')
        if (!token) {
          commit('SET_AUTH', { isAuthenticated: false })
          return
        }

        const response = await axios.get('/api/user/data')
        commit('SET_USER', response.data.user)
        commit('SET_AUTH', { isAuthenticated: true })
      } catch (error) {
        commit('SET_AUTH', {
          isAuthenticated: false,
          error: error.response?.data?.error || 'Ошибка авторизации'
        })
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
      } finally {
        commit('SET_AUTH_LOADING', false)
      }
    },

    async login({ commit, dispatch }, credentials) {
      commit('SET_AUTH_LOADING', true);
      try {
        const response = await axios.post('/api/login/user', credentials);
        localStorage.setItem('accessToken', response.data.accessToken);
        localStorage.setItem('refreshToken', response.data.refreshToken);
        commit('SET_USER', response.data.user);
        await dispatch('fetchUser');
        commit('SET_AUTH', {
          isAuthenticated: true,
          error: null
        });
        commit('CLOSE_MODAL', 'login');
        commit('CLOSE_MODAL', 'register');
        router.push('/');
      } catch (error) {
        commit('SET_AUTH', {
          isAuthenticated: false,
          error: error.response?.data?.error || 'Ошибка входа'
        });
        throw error;
      } finally {
        commit('SET_AUTH_LOADING', false);
      }
    },

    async register({ commit }, userData) {
      commit('SET_AUTH_LOADING', true)
      try {
        const registrationData = {
          username: userData.username,
          email: userData.email,
          password: userData.password,
          confirmPassword: userData.confirmPassword,
          notifications: {
            email: userData.receiveNotifications || false
          }
        }
        const response = await axios.post('/api/create/user', registrationData)
        console.log('Ответ сервера:', response.data)
        localStorage.setItem('accessToken', response.data.accessToken)
        localStorage.setItem('refreshToken', response.data.refreshToken)
        commit('SET_USER', response.data.user)
        commit('SET_AUTH', {
          isAuthenticated: true,
          error: null
        })
        commit('CLOSE_MODAL', 'register')
        commit('CLOSE_MODAL', 'login')
        router.push('/')
      } catch (error) {
        commit('SET_AUTH', {
          isAuthenticated: false,
          error: error.response?.data?.error || 'Ошибка регистрации'
        })
        throw error
      } finally {
        commit('SET_AUTH_LOADING', false)
      }
    },

    async logout({ commit }) {
      commit('SET_AUTH_LOADING', true);
      try {
        await axios.post('/api/logout');
      } finally {
        // Удаляем все типы токенов при выходе
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('adminAccessToken');
        localStorage.removeItem('adminRefreshToken');
        commit('SET_AUTH', { isAuthenticated: false });
        commit('SET_USER', {
          id: null,
          username: '',
          email: '',
          avatar: '/default-avatar.png'
        });
        router.push('/');
        commit('SET_AUTH_LOADING', false);
      }
    },

    // Действия с пользователем
    async updateAvatar({ commit }, formData) {
      try {
        const response = await axios.post('/api/user/avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        commit('SET_USER', {
          avatar: response.data.avatarUrl,
          ...response.data.user
        })

        return response.data;
      } catch (error) {
        throw error;
      }
    },

    async addToFavorites({ commit }, movieId) {
      const response = await axios.post(`/api/user/favorites/${movieId}`)
      commit('UPDATE_USER_STATS', { favorites: response.data.count })
    },
    async updateProfile({ commit }, profileData) {
      try {

        if (!profileData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileData.email)) {
          throw new Error('Пожалуйста, введите корректный email');
        }

        const response = await axios.put('/api/update/user', profileData);

        if (response.data.success) {
          commit('SET_USER', response.data.user); // Обновляем данные в хранилище
          return response.data; // Возвращаем полный ответ
        } else {
          throw new Error(response.data.error || 'Ошибка обновления профиля');
        }
      } catch (error) {
        console.error('Ошибка в updateProfile:', error);
        throw error; 
      }
    },
    updateFormField({ commit }, payload) {
      commit('UPDATE_FORM_FIELD', payload)
    },
    // UI действия
    toggleMenu({ commit }) {
      commit('TOGGLE_MENU')
    },

    openModal({ commit }, modalType) {
      commit('OPEN_MODAL', { type: modalType })
      commit('RESET_FORM', { formType: modalType })
    },

    closeModal({ commit }, modalType) {
      commit('CLOSE_MODAL', modalType)
    },

    async fetchWallet({ commit }) {
      try {
        const response = await axios.get('/api/wallet');
        commit('SET_WALLET_DATA', {
          balance: response.data.balance,
          transactions: response.data.transactions
        });
        return response.data;
      } catch (error) {
        console.error('Ошибка загрузки кошелька:', error);
        throw error;
      }
    },
    async deposit({ commit }, amount) {
      try {
        const response = await axios.post('/api/wallet/deposit', { amount });
        commit('UPDATE_BALANCE', response.data.newBalance);
        commit('ADD_TRANSACTION', response.data.transaction);
        return response.data;
      } catch (error) {
        console.error('Ошибка пополнения:', error);
        throw error;
      }
    },

    async fetchPlans({ commit }) {
      try {
        const response = await axios.get('/api/plans');
        commit('SET_PLANS', response.data);
        return response.data;
      } catch (error) {
        commit('SET_SUBSCRIPTION_ERROR', 'Не удалось загрузить планы подписки');
        throw error;
      }
    },
    async fetchPlan({ commit }, planId) {
      try {
        const response = await axios.get(`/api/plans/${planId}`);
        return response;
      } catch (error) {
        commit('SET_SUBSCRIPTION_ERROR', 'Не удалось загрузить информацию о подписке');
        throw error;
      }
    },
    async fetchCurrentSubscription({ commit }) {
      try {
        const response = await axios.get('/api/subscriptions/current');
        commit('SET_CURRENT_SUBSCRIPTION', response.data);
        return response.data;
      } catch (error) {
        commit('SET_SUBSCRIPTION_ERROR', 'Не удалось загрузить текущую подписку');
        throw error;
      }
    },
    async purchasePlan({ commit }, { planId }) {
      commit('SET_SUBSCRIPTION_LOADING', true);
      commit('SET_SUBSCRIPTION_ERROR', null);

      try {
        // --- УДАЛЕНО: validateStatus: function (status) { return status >= 200 && status < 500; } ---
        // Теперь интерцептор будет обрабатывать 401 как ошибку
        const response = await axios.post('/api/subscriptions/purchase', { planId }); // Используем `api`

        if (!response.data) {
          throw new Error('Сервер не вернул данные');
        }

        // Этот блок теперь будет срабатывать только для статусов, которые интерцептор
        // не посчитал ошибкой и вернул как успешный ответ, но при этом они указывают на "логическую" ошибку.
        // В идеале, после настройки интерцептора, сюда будут попадать только 2xx статусы.
        // Если сюда попал 401, это значит, что что-то не так с настройкой интерцептора
        // или с тем, как axios обрабатывает validateStatus.
        if (response.status >= 400) { 
           const errorMsg = response.data?.error || `Ошибка ${response.status}`;
           throw new Error(errorMsg);
        }

        // Обработка успешного ответа
        if (response.data.paymentRequired) {
          return {
            paymentRequired: true,
            requiredAmount: response.data.requiredAmount || 0
          };
        }

        // Обновление состояния только при успехе
        if (response.data.success) {
          if (response.data.newBalance !== undefined) {
            commit('UPDATE_BALANCE', response.data.newBalance);
          }
          if (response.data.transaction) {
            commit('ADD_TRANSACTION', response.data.transaction);
          }
          if (response.data.subscription) {
            commit('SET_CURRENT_SUBSCRIPTION', response.data.subscription);
            commit('ADD_SUBSCRIPTION_HISTORY', response.data.subscription); // Если у вас есть такая мутация
          }
          return { success: true };
        }

        // Если success=false, но нет paymentRequired, выбрасываем ошибку
        throw new Error(response.data.error || 'Неизвестная ошибка');

      } catch (error) {
        // Здесь мы ловим ошибки, которые выбросил интерцептор (например, 401 после неудачной попытки refresh)
        // или другие ошибки, которые не были обработаны интерцептором (например, 500)
        console.error("Ошибка в purchasePlan (после интерцептора):", error.response?.data || error.message);
        const errorMessage = error.response?.data?.error || error.message || 'Ошибка при покупке подписки';
        commit('SET_SUBSCRIPTION_ERROR', errorMessage);
        throw error; // Очень важно перебросить ошибку дальше, чтобы компонент мог ее поймать
      } finally {
        commit('SET_SUBSCRIPTION_LOADING', false);
      }
    },
    async showSubscriptionNotification({ commit, state }, subscription) {
      // Если подписка не истекла или это базовая подписка - сбрасываем флаг
      if (!subscription?.endDate || subscription.planId?.price === 0) {
        commit('RESET_SUBSCRIPTION_NOTIFICATION');
        return false;
      }

      const now = new Date();
      const endDate = new Date(subscription.endDate);

      // Если подписка еще активна - не показываем уведомление
      if (endDate > now) {
        return false;
      }

      // Проверяем, было ли уже показано уведомление для этой подписки
      if (state.subscriptionNotification.subscriptionId === subscription._id &&
        state.subscriptionNotification.shown) {
        return false;
      }

      // Обновляем состояние уведомления
      commit('SET_SUBSCRIPTION_NOTIFICATION', {
        shown: true,
        subscriptionId: subscription._id,
        lastShown: now
      });

      return true;
    }
  },

  getters: {
    // Геттеры пользователя
    currentUser: state => state.user,
    userStats: state => state.user.stats,
    userSubscription: state => {
      return {
        type: state.user.subscription.type,
        expiresAt: state.user.subscription.expiresAt,
        active: state.user.subscription.active
      }
    },
    activeSubscriptionPlanId: (state) => {
      if (!state.auth.isAuthenticated) return null;

      // Получаем текущий план из разных возможных мест в структуре
      const currentPlan = state.user.subscription?.currentPlan;

      // Проверяем разные варианты, где может быть ID плана
      return currentPlan?.planId?._id ||  // Если planId - это объект с _id
        currentPlan?.planId ||       // Если planId - это строка
        currentPlan?._id ||         // Если ID плана находится в корне currentPlan
        '67f437687b06d9a11720a6ce';                       // Если ничего не найдено
    },
    hasActiveSubscription: (state, getters) => {
      return getters.activeSubscriptionPlanId !== null;
    },

    walletBalance: state => state.user.wallet.balance,
    walletTransactions: state => state.user.wallet.transactions || [],


    // Геттеры аутентификации
    isAuthenticated: state => state.auth.isAuthenticated,
    authError: state => state.auth.error,
    isLoading: state => state.auth.loading,

    // Геттеры UI
    isMenuOpen: state => state.ui.isMenuOpen,
    modalOpen: state => modalType => state.ui.modals[modalType] || false,
    form: state => formType => state.ui.forms[formType],
    plans: state => state.user.subscription.plans
  }
})
