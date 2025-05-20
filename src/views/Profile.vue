<script>
import { mapState, mapGetters, mapActions } from 'vuex'


export default {
  data() {
    return {
      isEditing: false,
      editForm: {
        name: '',
        email: '',
        newPassword: '',
        confirmPassword: ''
      },
      passwordError: '',
      fileInput: null,
      isLoading: false,
      depositAmount: 0,
      showDepositModal: false,
      showTransactions: false,
      canScrollLeft: false,
      canScrollRight: false,
      scrollContainer: null,
      error: null,
      subscriptionTimer: null,
      secondsLeft: 0
    }
  },
  mounted() {
    this.initScroll();
  },
  beforeDestroy() {
    if (this.scrollContainer) {
      this.scrollContainer.removeEventListener('scroll', this.handleScroll);
    }
  },

  watch: {
    walletTransactions() {
      this.$nextTick(() => {
        this.initScroll();
      });
    },
    userSubscription: {
      deep: true,
      handler(newVal) {
        
        if (newVal.daysLeft <= 3 && newVal.daysLeft > 0) {
          this.$notify({
            title: "Подписка истекает",
            text: `Ваша подписка истечет через ${newVal.daysLeft} ${this.declOfNum(newVal.daysLeft, ['день', 'дня', 'дней'])}`,
            type: "warning",
            duration: 10000
          });
        }
      }
    },
    '$store.state.user.subscription.currentPlan': {
      deep: true,
      handler(newVal) {
        if (newVal?.endDate) {
          // Сбрасываем флаг уведомления при изменении подписки
          if (this.$store.state.subscriptionNotification.subscriptionId !== newVal._id) {
            this.$store.commit('RESET_SUBSCRIPTION_NOTIFICATION');
          }
          this.startSubscriptionTimer(newVal.endDate);
        } else {
          if (this.subscriptionTimer) {
            clearInterval(this.subscriptionTimer);
          }
          this.secondsLeft = '∞';
          this.$store.commit('RESET_SUBSCRIPTION_NOTIFICATION');
        }
      }
    }
  },
  beforeDestroy() {
    if (this.subscriptionTimer) {
      clearInterval(this.subscriptionTimer);
    }
  },
  computed: {
    ...mapState(['auth']),
    ...mapGetters(['isAuthenticated', 'currentUser', 'userStats', 'userSubscription', 'walletTransactions', 'walletBalance']),
    formattedStats() {
      return {
        views: this.userStats?.views || 0,
        ratings: this.userStats?.ratings || 0,
        subscription: this.userSubscription.type || 'Базовый'
      };
    },
    formattedBalance() {
      return this.walletBalance.toFixed(2)
    },
    favoritesCount() {
      return this.userStats?.favorites?.length || 0
    },
    userAvatar() {
      return this.currentUser?.avatar || '/defaults/default-avatar.png'
    },
    userSubscription() {
      const sub = this.$store.state.user.subscription.currentPlan;

      if (!sub || !sub.planId) {
        return {
          type: 'Базовый',
          timeLeft: '∞',
          badgeClass: 'bg-blue-500/20 text-blue-400',
          isExpired: true,
          plan: null
        };
      }

      const now = new Date();
      const endDate = sub.endDate ? new Date(sub.endDate) : null;
      const secondsLeft = endDate ? Math.max(0, Math.floor((endDate - now) / 1000)) : '∞';

      return {
        type: sub.plan?.name || 'Неизвестный',
        timeLeft: secondsLeft,
        badgeClass: this.getBadgeClass(secondsLeft),
        isExpired: secondsLeft !== '∞' && secondsLeft <= 0,
        plan: sub.plan
      };
    }
  },

  created() {
    // Инициализируем форму текущими значениями
    this.initializeProfile();
  },
  methods: {
    ...mapActions([
      'fetchUser',
      'updateProfile',
      'updateAvatar',
      'addToFavorites',
      'fetchWallet',
      'deposit'
    ]),
    validateEmail(email) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(email);
    },
    async initializeProfile() {
      this.isLoading = true;
      try {
        if (this.isAuthenticated) {
          await this.fetchUser();
          await this.fetchWallet();
          await this.$store.dispatch('fetchCurrentSubscription');
          this.resetEditForm();
        }
      } catch (error) {
        console.error("Ошибка загрузки данных:", error);
      } finally {
        this.isLoading = false;
      }
    },
    async fetchUserData() {
      if (this.isAuthenticated) {
        await this.fetchUser();
      }
    },
    resetEditForm() {
      this.editForm = {
        name: this.currentUser?.username || '',
        email: this.currentUser?.email || '',
        newPassword: '',
        confirmPassword: ''
      },
        this.passwordError = '';
    },
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    async handleAvatarChange(event) {
      const file = event.target.files[0];
      if (!file) return;

      if (file.size > 2 * 1024 * 1024) {
        this.$notify({
            title: "Файл слишком большой",
            text: `2 МБ - максимальный размер файла`,
            type: "warning",
            duration: 10000
          });
        return
      }


      if (!file.type.startsWith('image/')) {
        this.passwordError = 'Пожалуйста, загрузите изображение';
        return;
      }

      try {
        const formData = new FormData()
        formData.append('avatar', file)

        const response = await this.$store.dispatch('updateAvatar', formData);

        if (this.$refs.avatarInput) {
          this.$refs.avatarInput.src = response.avatarUrl;
        }
        this.fetchUser()
        this.$notify({
          title: "Успех",
          text: "Аватар успешно обновлен",
          type: "success"
        });
      } catch (error) {
        this.passwordError = 'Ошибка загрузки аватара';
        console.error(error);
      }

    },

    async saveProfile() {

      if (!this.validateEmail(this.editForm.email)) {
        this.passwordError = 'Пожалуйста, введите корректный email';
        return;
      }

      if (!this.editForm.confirmPassword) {
        this.passwordError = 'Подтвердите пароль';
        return;
      }

      try {
        const profileData = {
          username: this.editForm.name,
          email: this.editForm.email,
          currentPassword: this.editForm.confirmPassword,
          ...(this.editForm.newPassword && { newPassword: this.editForm.newPassword })
        };

        const response = await this.$store.dispatch('updateProfile', profileData);

        if (response.success) { 
          this.isEditing = false;
          this.passwordError = '';
          this.initializeProfile();
          this.$notify({
            title: "Успех",
            text: "Профиль успешно сохранен",
            type: "success"
          });
        } else {
          this.passwordError = response.error || 'Неизвестная ошибка';
        }
      } catch (error) {
        // Ошибка сети или сервера (500, 400 и т.д.)
        this.passwordError = error.response?.data?.error || 'Ошибка обновления профиля';
        console.error('Ошибка при обновлении профиля:', error);
      }


    },

    cancelEdit() {
      this.isEditing = false;
      this.resetEditForm()
    },
    toggleEdit() {
      this.isEditing = !this.isEditing;
    },
    openDepositModal() {
      this.showDepositModal = true;
    },
    closeDepositModal() {
      this.showDepositModal = false;
      this.depositAmount = 0;
    },
    async handleDeposit() {
      if (this.depositAmount <= 0) {
        this.passwordError = 'Введите корректную сумму';
        return;
      }
      try {
        await this.$store.dispatch('deposit', this.depositAmount)
        this.$notify({
          title: "Успех",
          text: "Кошелек успешно пополнен",
          type: "success"
        });
        this.closeDepositModal();
      } catch (error) {
        this.passwordError = error.response?.data?.error || 'Ошибка пополнения';
      }
    },


    initScroll() {
      this.$nextTick(() => {
        this.scrollContainer = this.$refs.scrollContainer;
        if (this.scrollContainer) {
          this.checkScrollButtons();
          this.scrollContainer.addEventListener('scroll', this.handleScroll);
        }
      });
    },

    checkScrollButtons() {
      if (!this.scrollContainer) return;

      const { scrollLeft, scrollWidth, clientWidth } = this.scrollContainer;
      this.canScrollLeft = scrollLeft > 0;
      this.canScrollRight = scrollLeft < scrollWidth - clientWidth - 1; // -1 для округления
    },

    handleScroll() {
      this.checkScrollButtons();
    },

    scrollLeft() {
      if (this.scrollContainer) {
        this.scrollContainer.scrollBy({
          left: -200,
          behavior: 'smooth'
        });
      }
    },

    scrollRight() {
      if (this.scrollContainer) {
        this.scrollContainer.scrollBy({
          left: 200,
          behavior: 'smooth'
        });
      }
    },


    formatDate(date) {
      if (!date) return 'Дата не указана';

      // Если date - это строка (ISO format)
      const d = new Date(date);

      // Если date - это объект Date из MongoDB
      const dateObj = date instanceof Date ? date : d;

      return isNaN(dateObj.getTime())
        ? 'Некорректная дата'
        : dateObj.toLocaleDateString('ru-RU') + ' ' + dateObj.toLocaleTimeString('ru-RU');
    },
    declOfNum(number, titles) {
      const cases = [2, 0, 1, 1, 1, 2];
      return titles[
        number % 100 > 4 && number % 100 < 20 ? 2 : cases[number % 10 < 5 ? number % 10 : 5]
      ];
    },
    startSubscriptionTimer(endDate) {
      if (this.subscriptionTimer) {
        clearInterval(this.subscriptionTimer);
      }

      this.updateTimeLeft(endDate);

      this.subscriptionTimer = setInterval(() => {
        this.updateTimeLeft(endDate);
      }, 1000);
    },

    updateTimeLeft(endDate) {
      const now = new Date();
      const end = new Date(endDate);
      this.secondsLeft = Math.max(0, Math.floor((end - now) / 1000));
    },

    async handleSubscriptionExpired() {
      // Останавливаем таймер
      if (this.subscriptionTimer) {
        clearInterval(this.subscriptionTimer);
      }

      // Устанавливаем флаг, что подписка истекла
      this.secondsLeft = 0;

      // Показываем уведомление только если оно еще не было показано
      const sub = this.$store.state.user.subscription.currentPlan;
      const shouldShow = await this.$store.dispatch('showSubscriptionNotification', sub);

      if (shouldShow) {
        this.$notify({
          title: "Подписка истекла",
          text: "Ваша подписка завершена, активирован базовый тариф",
          type: "info",
          duration: 5000
        });
      }

      // Принудительно обновляем данные пользователя
      try {
        await this.$store.dispatch('fetchUser');
        await this.$store.dispatch('fetchCurrentSubscription');
      } catch (error) {
        console.error("Ошибка обновления данных подписки:", error);
      }
    },

    getBadgeClass(seconds) {
      if (seconds === '∞') return 'bg-blue-500/20 text-blue-400';
      if (seconds <= 0) return 'bg-gray-500/20 text-gray-400';

      const days = Math.floor(seconds / (24 * 60 * 60));
      if (days < 1) return 'bg-red-500/20 text-red-400';
      if (days < 3) return 'bg-yellow-500/20 text-yellow-400';
      return 'bg-teal-500/20 text-teal-400';
    },

    formatTime(seconds) {
      if (seconds === '∞') return 'Бессрочная';
      if (seconds <= 0) return 'Истекла';

      const days = Math.floor(seconds / (24 * 60 * 60));
      const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60));
      const mins = Math.floor((seconds % (60 * 60)) / 60);

      if (days > 0) {
        return `${days} ${this.declOfNum(days, ['день', 'дня', 'дней'])}`;
      } else if (hours > 0) {
        return `${hours} ${this.declOfNum(hours, ['час', 'часа', 'часов'])}`;
      } else {
        return `${mins} ${this.declOfNum(mins, ['минута', 'минуты', 'минут'])}`;
      }
    }



  },
  async mounted() {
    const sub = this.$store.state.user.subscription.currentPlan;
    if (sub?.endDate) {
      this.startSubscriptionTimer(sub.endDate);
    }
  }
}


</script>



<template>
  <div class="min-h-screen bg-gray-900 text-white py-8 px-4 sm:px-6 flex items-center justify-center">
    <div class="w-full max-w-4xl bg-gray-800 p-6 sm:p-10 rounded-xl shadow-2xl">
      <!-- Заголовок профиля -->
      <div class="text-center mb-10">
        <h1
          class="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent">
          Мой профиль
        </h1>
        <p class="text-gray-400 mt-3 text-sm sm:text-base">
          Управляйте настройками вашего аккаунта
        </p>
      </div>

      <!-- Аватар и основная информация -->
      <div class="flex flex-col md:flex-row gap-8 mb-10">
        <!-- Аватар -->
        <div class="flex-shrink-0 flex justify-center">
          <div class="relative group">
            <img :src="userAvatar" alt="User Avatar"
              class="rounded-full w-32 h-32 sm:w-40 sm:h-40 object-cover border-4 border-teal-500/50 shadow-xl group-hover:border-teal-500 transition-all duration-300" />
            <input type="file" ref="fileInput" @change="handleAvatarChange" accept="image/*" class="hidden" />
            <button @click="triggerFileInput"
              class="absolute bottom-2 right-2 bg-teal-600 text-white p-2 rounded-full shadow-lg hover:bg-teal-700 transition-all transform group-hover:scale-110">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Основная информация -->
        <div class="flex-grow space-y-4">
          <div
            class="bg-gray-700/50 p-4 rounded-lg backdrop-blur-sm shadow-inner hover:shadow-teal-500/10 transition-shadow ">
            <h3 class="text-lg font-medium text-teal-400">Имя пользователя</h3>
            <p class="text-white mt-1">{{ currentUser.username }}</p>
          </div>

          <div
            class="bg-gray-700/50 p-4 rounded-lg backdrop-blur-sm shadow-inner hover:shadow-teal-500/10 transition-shadow ">
            <h3 class="text-lg font-medium text-teal-400">Email</h3>
            <p class="text-white mt-1">{{ currentUser.email }}</p>
          </div>
        </div>

      </div>

      <!-- Статистика -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        <div
          class="bg-gradient-to-br from-gray-700 to-gray-800 p-5 rounded-xl text-center shadow-inner hover:shadow-teal-500/10 transition-shadow">
          <div class="text-teal-400 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <h4 class="text-sm text-gray-400">Просмотрено</h4>
          <p class="text-2xl font-bold">{{ formattedStats.views }}</p>
        </div>

        <div
          class="bg-gradient-to-br from-gray-700 to-gray-800 p-5 rounded-xl text-center shadow-inner hover:shadow-teal-500/10 transition-shadow">
          <div class="text-teal-400 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </div>
          <h4 class="text-sm text-gray-400">Оценок</h4>
          <p class="text-2xl font-bold">{{ formattedStats.ratings }}</p>
        </div>

        <div
          class="bg-gradient-to-br from-gray-700 to-gray-800 p-5 rounded-xl text-center shadow-inner hover:shadow-teal-500/10 transition-all">
          <div class="text-teal-400 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>

          <h4 class="text-sm text-gray-400 mb-1">Подписка</h4>
          <p class="text-xl font-bold mb-1 truncate px-2">
            {{ userSubscription.isExpired ? 'Базовый' : userSubscription.type }}
          </p>

          <div class="text-xs mt-1">
            <span :class="userSubscription.badgeClass + ' px-2 py-0.5 rounded-full'">
              {{ userSubscription.isExpired ? 'Бессрочная' : formatTime(userSubscription.timeLeft) }}
              <span v-if="!userSubscription.isExpired && userSubscription.timeLeft !== '∞'">
                осталось
              </span>
            </span>
          </div>
        </div>
      </div>

      

      <!-- Избранное и платежи -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <!-- Избранные фильмы -->
        <div
          class="bg-gray-700/50 p-5 rounded-xl backdrop-blur-sm hover:shadow-teal-500/10 transition-shadow shadow-inner hover:shadow-teal-500/10 transition-shadow">
          <h3 class="text-xl font-semibold mb-4 flex items-center text-teal-400">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            Избранные фильмы
          </h3>
          <p class="text-gray-300">У вас <span class="text-teal-400 font-medium">{{ favoritesCount }}</span> фильмов в
            избранном</p>
        </div>

        <!-- Способы оплаты -->
        <div
          class="bg-gray-700/50 p-5 rounded-xl backdrop-blur-sm shadow-inner hover:shadow-teal-500/10 transition-shadow">
          <h3 class="text-xl font-semibold mb-4 flex items-center text-teal-400">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            Способы оплаты
          </h3>
          <div class="flex justify-around mt-4">
            <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/visa/visa-original.svg"
              class="h-8 opacity-80 hover:opacity-100 transition" alt="Visa" />
            <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mastercard/mastercard-original.svg"
              class="h-8 opacity-80 hover:opacity-100 transition" alt="MasterCard" />
            <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/paypal/paypal-original.svg"
              class="h-8 opacity-80 hover:opacity-100 transition" alt="PayPal" />
          </div>
        </div>
      </div>



      <div v-if="showDepositModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <h3 class="text-xl font-bold mb-4 text-teal-400">Пополнение кошелька</h3>

          <div class="mb-4">
            <label class="block text-gray-400 mb-2">Сумма (RUB)</label>
            <input v-model.number="depositAmount" type="number" min="10" step="10"
              class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Введите сумму">
          </div>

          <div v-if="passwordError" class="text-red-400 mb-4">{{ passwordError }}</div>

          <div class="flex justify-end space-x-3">
            <button @click="closeDepositModal" class="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition">
              Отмена
            </button>
            <button @click="handleDeposit" class="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg transition">
              Пополнить
            </button>
          </div>
        </div>
      </div>

      <!-- Блок кошелька в профиле -->
      <div
        class="bg-gray-700/50 p-5 rounded-xl backdrop-blur-sm mt-6 shadow-inner hover:shadow-teal-500/10 transition-shadow">
        <h3 class="text-xl font-semibold mb-4 flex items-center text-teal-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24"
            stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          Мой кошелёк
        </h3>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-2xl font-bold text-teal-400">
              {{ formattedBalance }} ₽
            </p>
            <p class="text-gray-400 text-sm mt-1">Текущий баланс</p>
          </div>

          <button @click="openDepositModal" class="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg transition">
            Пополнить
          </button>
        </div>

        <div class="mt-4">
          <div class="flex items-center justify-between mb-2">
            <h4 class="text-teal-400 text-sm">История операций</h4>
            <div class="flex space-x-2">
              <button @click="scrollLeft" :disabled="!canScrollLeft" :class="{
                'text-teal-400 hover:text-teal-300': canScrollLeft,
                'text-gray-500 cursor-not-allowed': !canScrollLeft
              }">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24"
                  stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button @click="scrollRight" :disabled="!canScrollRight" :class="{
                'text-teal-400 hover:text-teal-300': canScrollRight,
                'text-gray-500 cursor-not-allowed': !canScrollRight
              }">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24"
                  stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>

          <div class="relative">
            <div ref="scrollContainer" class="scroll-container" @scroll="handleScroll">
              <div v-for="(tx, index) in walletTransactions" :key="index"
                class="transaction-item p-3 bg-gray-600/50 rounded-lg">
                <div class="flex justify-between">
                  <span class="text-sm truncate">{{ tx.description }}</span>
                  <span :class="tx.amount > 0 ? 'text-green-400' : 'text-red-400'">
                    {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }} ₽
                  </span>
                </div>
                <div class="text-gray-400 text-xs mt-1">
                  {{ formatDate(tx.createdAt || tx.date) }}
                </div>
              </div>

              <p v-if="!walletTransactions.length" class="text-gray-400 text-center py-2">
                Нет операций
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопка редактирования -->
      <div class="text-center mt-4">
        <button @click="toggleEdit"
          class="bg-gradient-to-r from-teal-500 to-blue-600 text-white px-8 py-3 rounded-lg font-medium shadow-lg hover:shadow-teal-500/20 hover:from-teal-600 hover:to-blue-700 transition-all duration-300">
          {{ isEditing ? 'Отменить редактирование' : 'Редактировать профиль' }}
        </button>
      </div>

      <!-- Форма редактирования -->
      <div v-if="isEditing"
        class="mt-10 p-6 bg-gray-800/80 rounded-xl backdrop-blur-sm border border-gray-700 shadow-2xl">
        <h3 class="text-2xl font-bold mb-6 text-center text-teal-400">Редактирование профиля</h3>

        <form @submit.prevent="saveProfile" class="space-y-5">
          <div>
            <label class="block text-gray-400 mb-2">Имя</label>
            <input v-model="editForm.name" type="text"
              class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent" />
          </div>

          <div>
            <label class="block text-gray-400 mb-2">Email</label>
            <input v-model="editForm.email" type="email" pattern="[^\s@]+@[^\s@]+\.[^\s@]+"
              title="Пожалуйста, введите корректный email (например, user@example.com)"
              class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent" />

          </div>

          <div>
            <label class="block text-gray-400 mb-2">Новый пароль</label>
            <input v-model="editForm.newPassword" type="password" placeholder="Оставьте пустым, если не хотите менять"
              class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent" />
          </div>

          <div>
            <label class="block text-gray-400 mb-2">Подтверждение пароля</label>
            <input v-model="editForm.confirmPassword" type="password"
              class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent" />
          </div>

          <div v-if="passwordError" class="text-red-400 text-sm">
            {{ passwordError }}
          </div>

          <div class="flex justify-between pt-4">
            <button type="button" @click="cancelEdit" class="px-6 py-2 text-gray-400 hover:text-white transition">
              Отмена
            </button>
            <button type="submit" class="px-8 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition">
              Сохранить изменения
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>



<style scoped>
/* Плавные переходы */
.transition {
  transition: all 0.3s ease;
}

/* Кастомный скролл */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.scroll-container {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  gap: 12px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.scroll-container::-webkit-scrollbar {
  display: none;
}

.transaction-item {
  scroll-snap-align: start;
  flex-shrink: 0;
  width: 192px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.scroll-smooth::-webkit-scrollbar {
  display: none;
}

.subscription-block {
  transition: all 0.3s ease;
}

.subscription-block:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(16, 185, 129, 0.1);
}
</style>