<script>
import axios from 'axios';

export default {
  name: 'AdminPanel',
  data() {
    return {
      subscriptions: [],
      selectedSubscription: null,
      currentSubscription: null,
      showNewSubscriptionForm: false,
      newSubscription: {
        name: '',
        description: '',
        price: 0,
        renewalPeriod: 30,
        featuresInput: '',
        features: []
      },

      // Данные пользователей
      users: [],
      filteredUsers: [],
      loadingUsers: false,

      // Поиск и сортировка
      userSearchQuery: '',
      sortField: '_id',
      sortDirection: 'asc',

      // Пагинация
      currentPage: 1,
      perPage: 25,
      totalUsers: 0,
      // Редактирование пользователя
      selectedUser: null,
      isAuthenticated: false,
      loading: false,
      authChecked: false
    }
  },
  async created() {
    await this.checkAuth();
    if (this.isAuthenticated) {
      await this.loadData();
    }
  },
  computed: {
    // Пользователи для текущей страницы
    paginatedUsers() {
      // Если выбрано "все пользователи", возвращаем весь отфильтрованный список
      if (this.perPage === 'all') {
        return this.filteredUsers;
      }

      const start = (this.currentPage - 1) * this.perPage;
      const end = start + this.perPage;
      return this.filteredUsers.slice(start, end);
    },

    // Общее количество страниц
    totalPages() {
      if (this.perPage === 'all') return 1;
      return Math.ceil(this.filteredUsers.length / this.perPage);
    },

    // Номера страниц для отображения
    pagesToShow() {
      const pages = [];
      const maxVisible = 5;

      let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
      let end = Math.min(this.totalPages, start + maxVisible - 1);

      if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1);
      }

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      return pages;
    },

    // Первый и последний элемент на странице
    startItem() {
      if (this.filteredUsers.length === 0) return 0;
      return (this.currentPage - 1) * parseInt(this.perPage) + 1;
    },

    endItem() {
      if (this.perPage === 'all') return this.filteredUsers.length;
      const end = this.currentPage * parseInt(this.perPage);
      return end > this.filteredUsers.length ? this.filteredUsers.length : end;
    },

    // Иконка сортировки
    sortIcon() {
      return this.sortDirection === 'asc' ? '↑' : '↓';
    }
  },
  methods: {
    async checkAuth() {
      const accessToken = localStorage.getItem('adminAccessToken');
      const refreshToken = localStorage.getItem('adminRefreshToken');

      if (!accessToken && !refreshToken) {
        this.$router.push('/admin/login');
        return;
      }

      try {
        const response = await axios.get('/api/admin/check', {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        });

        this.isAuthenticated = true;
      } catch (error) {
        if (error.response?.status === 401 && refreshToken) {
          try {
            const refreshResponse = await axios.post('/api/admin/refresh-token', {
              refreshToken
            });

            localStorage.setItem('adminAccessToken', refreshResponse.data.accessToken);
            localStorage.setItem('adminRefreshToken', refreshResponse.data.refreshToken);
            this.isAuthenticated = true;
          } catch (refreshError) {
            this.logout();
          }
        } else {
          this.logout();
        }
      } finally {
        this.authChecked = true;
        this.loading = false;
      }
    },



    logout() {
      localStorage.removeItem('adminAccessToken');
      localStorage.removeItem('adminRefreshToken');
      this.$router.push('/admin/login');
    },

    async loadData() {
      try {
        await Promise.all([
          this.loadSubscriptions(),
          this.loadUsers()
        ]);
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
      }
    },

    // Методы для работы с подписками
    async loadSubscriptions() {
      try {
        const response = await axios.get('/api/plans');
        this.subscriptions = response.data;
        console.log(this.subscriptions)
      } catch (error) {
        console.error('Ошибка загрузки подписок:', error);
        alert('Не удалось загрузить подписки');
      }
    },

    async loadSubscriptionDetails() {
      if (!this.selectedSubscription) return;

      try {
        const response = await axios.get(`/api/plans/${this.selectedSubscription}`);
        if (!response.data) {
          throw new Error('Подписка не найдена');
        }
        this.currentSubscription = { ...response.data };
        // Преобразуем массив features в строку для редактирования
        if (this.currentSubscription.features && Array.isArray(this.currentSubscription.features)) {
          this.currentSubscription.features = [...this.currentSubscription.features];
        } else {
          this.currentSubscription.features = [];
        }
      } catch (error) {
        console.error('Ошибка загрузки деталей подписки:', error);
        this.$notify({
          type: 'error',
          text: error.response?.data?.error || error.message || 'Не удалось загрузить данные подписки'
        });
      }
    },

    showCreateSubscriptionForm() {
      this.showNewSubscriptionForm = true;
      this.newSubscription = {
        name: '',
        description: '',
        price: 0,
        renewalPeriod: 30,
        featuresInput: '',
        features: []
      };
    },

    cancelCreateSubscription() {
      this.showNewSubscriptionForm = false;
    },

    async createSubscription() {
      try {
        // Проверяем обязательные поля
        if (!this.newSubscription.name || !this.newSubscription.price) {
          this.$notify({
            type: 'error',
            text: 'Название и цена подписки обязательны'
          });
          return;
        }

        // Подготавливаем данные для отправки
        const subscriptionData = {
          name: this.newSubscription.name,
          description: this.newSubscription.description,
          price: parseFloat(this.newSubscription.price),
          renewalPeriod: parseInt(this.newSubscription.renewalPeriod) || 30,
          features: this.newSubscription.featuresInput
            .split(',')
            .map(f => f.trim())
            .filter(f => f.length > 0)
        };

        // Отправляем запрос на сервер
        const response = await axios.post('/api/admin/plans/create', subscriptionData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('adminAccessToken')}`
          }
        });

        if (response.data.success) {
          // Добавляем новую подписку в список
          this.subscriptions.push(response.data.plan);
          this.showNewSubscriptionForm = false;

          this.$notify({
            type: 'success',
            text: 'Подписка успешно создана'
          });

          // Сбрасываем форму
          this.newSubscription = {
            name: '',
            description: '',
            price: 0,
            renewalPeriod: 30,
            featuresInput: '',
            features: []
          };
        }
      } catch (error) {
        console.error('Ошибка создания подписки:', error);
        this.$notify({
          type: 'error',
          text: error.response?.data?.detail ||
            error.response?.data?.message ||
            'Не удалось создать подписку'
        });
      }
    },
    async deleteUser(userId) {

      try {
        const response = await axios.delete(
          `/api/admin/user/delete/${userId}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('adminAccessToken')}`
            }
          }
        );

        if (response.data.success) {
          this.$notify({
            type: 'success',
            text: 'Пользователь успешно удален'
          });
          await this.loadUsers();
        }
      } catch (error) {
        console.error('Delete user error:', error);
        this.$notify({
          type: 'error',
          text: error.response?.data?.detail ||
            error.response?.data?.message ||
            'Не удалось удалить пользователя'
        });
      }
    },

    async updateSubscription() {
      try {
        // Преобразуем features в массив, если это строка
        const features = Array.isArray(this.currentSubscription.features)
          ? this.currentSubscription.features
          : [this.currentSubscription.features].filter(Boolean);

        const planData = {
          ...this.currentSubscription,
          features
        };

        const response = await axios.put(
          `/api/admin/plans/change/${this.currentSubscription._id}`,
          planData,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('adminAccessToken')}`
            }
          }
        );

        // Обновляем список подписок
        const index = this.subscriptions.findIndex(
          sub => sub._id === this.currentSubscription._id
        );
        if (index !== -1) {
          this.subscriptions[index] = response.data.plan;
        }

        this.$notify({
          type: 'success',
          text: 'Подписка успешно обновлена'
        });
      } catch (error) {
        console.error('Ошибка обновления подписки:', error);
        this.$notify({
          type: 'error',
          text: error.response?.data?.error ||
            error.message ||
            'Не удалось обновить подписку'
        });
      }
    },

    async deleteSubscription() {
      if (!this.currentSubscription || !this.currentSubscription._id) {
        this.$notify({
          type: 'error',
          text: 'Не выбрана подписка для удаления'
        });
        return;
      }

      if (this.currentSubscription.price === 0) {
        this.$notify({
          type: 'error',
          text: 'Нельзя удалить базовый тарифный план'
        });
        return;
      }
      if (!confirm(`Вы уверены, что хотите удалить подписку "${this.currentSubscription.name}"? Это действие нельзя отменить.`)) {
        return;
      }

      try {
        const response = await axios.delete(
          `/api/admin/plans/delete/${this.currentSubscription._id}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('adminAccessToken')}`
            }
          }
        );

        if (response.data.success) {
          // Удаляем из списка
          this.subscriptions = this.subscriptions.filter(
            sub => sub._id !== this.currentSubscription._id
          );

          this.currentSubscription = null;
          this.selectedSubscription = null;

          this.$notify({
            type: 'success',
            text: 'Подписка успешно удалена'
          });
        }
      } catch (error) {
        console.error('Ошибка удаления подписки:', error);

        let errorMessage = 'Не удалось удалить подписку';
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message;
        }

        this.$notify({
          type: 'error',
          text: errorMessage
        });
      }
    },

    addFeature() {
      if (!this.currentSubscription.features) {
        this.currentSubscription.features = [];
      }
      this.currentSubscription.features.push('');
    },

    removeFeature(index) {
      this.currentSubscription.features.splice(index, 1);
    },

    // Методы для работы с пользователями
    async loadUsers() {
      this.loadingUsers = true;
      try {
        const response = await axios.get('/api/admin/users', {
          params: {
            page: this.currentPage,
            limit: this.perPage === 'all' ? 0 : this.perPage,
            search: this.userSearchQuery
          },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('adminAccessToken')}`
          }
        });

        console.log('Получены пользователи:', response.data.users); // Для отладки

        // Добавляем проверку и значение по умолчанию для wallet
        this.users = (response.data.users || []).map(user => ({
          ...user,
          wallet: user.wallet || { balance: 0 }
        }));

        this.filteredUsers = [...this.users];
        this.totalUsers = response.data.total || 0;
      } catch (error) {
        console.error('Ошибка загрузки пользователей:', error);
        this.$notify({
          type: 'error',
          text: error.response?.data?.error || 'Не удалось загрузить пользователей'
        });
      } finally {
        this.loadingUsers = false;
      }
    },

    handleSearchInput() {
      this.currentPage = 1;
      this.searchUsers();
    },

    searchUsers() {
      this.currentPage = 1;
      this.loadUsers(); // Теперь поиск выполняется на сервере
    },

    sortUsers(field) {
      if (this.sortField === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortField = field;
        this.sortDirection = 'asc';
      }

      this.filteredUsers.sort((a, b) => {
        let fieldA = this.getSortableValue(a, field);
        let fieldB = this.getSortableValue(b, field);

        // Для числовых значений (баланс)
        if (field === 'wallet.balance') {
          fieldA = Number(fieldA) || 0;
          fieldB = Number(fieldB) || 0;
          return this.sortDirection === 'asc' ? fieldA - fieldB : fieldB - fieldA;
        }

        // Для строковых значений (подписка и другие)
        if (typeof fieldA === 'string') fieldA = fieldA.toLowerCase();
        if (typeof fieldB === 'string') fieldB = fieldB.toLowerCase();

        if (fieldA < fieldB) return this.sortDirection === 'asc' ? -1 : 1;
        if (fieldA > fieldB) return this.sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    },

    getSortableValue(obj, fieldPath) {
      // Специальная обработка для подписки
      if (fieldPath === 'currentSubscription.planId') {
        const planId = obj.currentSubscription?.planId;
        return this.getSubscriptionName(planId) || 'Нет подписки';
      }

      // Обычная обработка вложенных полей
      const fields = fieldPath.split('.');
      let value = obj;
      for (const field of fields) {
        if (!value) return null;
        value = value[field];
      }
      return value;
    },

    getSubscriptionName(planId) {
      if (!planId) {
        console.log('No planId provided');
        return 'Нет подписки';
      }

      console.log('Looking for plan with ID:', planId, 'Type:', typeof planId);
      console.log('Available subscriptions:', this.subscriptions);

      // Если planId - это строка (ObjectId)
      if (typeof planId === 'string') {
        const sub = this.subscriptions.find(s => {
          console.log(`Comparing ${s._id} (${typeof s._id}) with ${planId} (${typeof planId})`);
          return s._id === planId || s._id.toString() === planId;
        });
        return sub ? sub.name : 'Неизвестная подписка';
      }

      // Если planId - это объект (при populate)
      if (typeof planId === 'object' && planId !== null) {
        return planId.name || 'Неизвестная подписка';
      }

      return 'Неизвестная подписка';
    },
    editUser(user) {
      console.log('Editing user:', user);
      console.log('User subscription planId:', user.currentSubscription?.planId);

      this.selectedUser = JSON.parse(JSON.stringify(user));

      // Убедимся, что все необходимые поля существуют
      if (!this.selectedUser.wallet) {
        this.selectedUser.wallet = { balance: 0 };
      }

      if (!this.selectedUser.currentSubscription) {
        this.selectedUser.currentSubscription = {
          planId: null,
          endDate: null,
          autoRenew: false,
          adminNote: ''
        };
      }

      // Если подписка есть, но planId это объект - преобразуем в строку
      if (this.selectedUser.currentSubscription?.planId &&
        typeof this.selectedUser.currentSubscription.planId === 'object') {
        console.log('Converting object planId to string:', this.selectedUser.currentSubscription.planId);
        this.selectedUser.currentSubscription.planId = this.selectedUser.currentSubscription.planId._id || this.selectedUser.currentSubscription.planId.id;
      }
    },

    async updateUser() {
      try {
        this.loading = true;

        // Подготавливаем данные для отправки
        const updateData = {
          username: this.selectedUser.username,
          email: this.selectedUser.email,
        };

        // Добавляем wallet если есть изменения
        if (this.selectedUser.wallet && this.selectedUser.wallet.balance !== undefined) {
          updateData.wallet = {
            balance: parseFloat(this.selectedUser.wallet.balance) || 0
          };
        }

        // Добавляем подписку если есть изменения
        if (this.selectedUser.currentSubscription) {
          updateData.currentSubscription = {
            planId: this.selectedUser.currentSubscription.planId || null,
            isActive: this.selectedUser.currentSubscription.isActive !== undefined
              ? this.selectedUser.currentSubscription.isActive
              : true,
            autoRenew: this.selectedUser.currentSubscription.autoRenew !== undefined
              ? this.selectedUser.currentSubscription.autoRenew
              : false,
            adminNote: this.selectedUser.currentSubscription.adminNote || ''
          };

          // Обработка даты окончания подписки
          if (this.selectedUser.currentSubscription.endDate) {
            updateData.currentSubscription.endDate =
              typeof this.selectedUser.currentSubscription.endDate === 'string'
                ? this.selectedUser.currentSubscription.endDate
                : this.selectedUser.currentSubscription.endDate.toISOString();
          }
        }

        console.log('Sending update data:', updateData); // Для отладки

        const response = await axios.put(
          `/api/admin/user/change/${this.selectedUser._id}`,
          updateData,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('adminAccessToken')}`
            }
          }
        );

        this.$notify({
          type: 'success',
          text: 'Данные пользователя успешно обновлены'
        });

        this.cancelUserEdit();
        await this.loadUsers();

      } catch (error) {
        console.error('Update error:', error);

        let errorMessage = 'Ошибка при обновлении пользователя';
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message;
        }

        this.$notify({
          type: 'error',
          text: errorMessage
        });
      } finally {
        this.loading = false;
      }
    },
    cancelUserEdit() {
      this.selectedUser = null;
    },

    // Методы пагинации
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },

    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },

    goToPage(page) {
      this.currentPage = page;
    },

    // Вспомогательные методы
    formatDate(dateString) {
      if (!dateString) return 'неизвестно';
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU');
    }
  },
  watch: {
    perPage() {
      this.currentPage = 1;
    }
  }
}
</script>


<template>
  <div v-if="authChecked">
    <div v-if="isAuthenticated" class="admin-container">
      <header class="admin-header">
        <h1>Административная панель</h1>
        <button @click="logout" class="btn btn-logout">
          Выйти
        </button>
      </header>

      <div class="admin-sections">
        <!-- Секция управления подписками -->
        <section class="admin-section">
          <h2>Управление подписками</h2>

          <div class="subscription-controls">
            <div class="form-group">
              <label>Создать новую подписку:</label>
              <button @click="showCreateSubscriptionForm" class="btn btn-primary">
                Создать подписку
              </button>
            </div>

            <div v-if="showNewSubscriptionForm" class="subscription-details">
              <div class="form-group">
                <label>Название подписки:*</label>
                <input type="text" v-model="newSubscription.name" class="form-control" required>
              </div>

              <div class="form-group">
                <label>Описание:</label>
                <textarea v-model="newSubscription.description" class="form-control" rows="4"></textarea>
              </div>

              <div class="form-group">
                <label>Цена (руб.):*</label>
                <input type="number" v-model.number="newSubscription.price" class="form-control" min="0" step="0.01"
                  required>
              </div>

              <div class="form-group">
                <label>Период продления (дней):</label>
                <input type="number" v-model.number="newSubscription.renewalPeriod" class="form-control" min="1"
                  value="30">
              </div>

              <div class="form-group">
                <label>Особенности (через запятую):</label>
                <input type="text" v-model="newSubscription.featuresInput" class="form-control"
                  placeholder="4K качество, Без рекламы, Оффлайн просмотр">
              </div>

              <div class="action-buttons">
                <button @click="createSubscription" class="btn btn-primary">
                  Создать подписку
                </button>
                <button @click="cancelCreateSubscription" class="btn btn-secondary">
                  Отменить
                </button>
              </div>
            </div>

            <div class="form-group">
              <label for="subscription-select">Выберите подписку:</label>
              <select id="subscription-select" v-model="selectedSubscription" @change="loadSubscriptionDetails"
                class="form-control">
                <option v-for="sub in subscriptions" :key="sub._id" :value="sub._id">
                  {{ sub.name }} ({{ sub.price }} руб.)
                </option>
              </select>
            </div>

            <div v-if="currentSubscription" class="subscription-details">
              <div class="form-group">
                <label>Название подписки:</label>
                <input type="text" v-model="currentSubscription.name" class="form-control">
              </div>

              <div class="form-group">
                <label>Описание:</label>
                <textarea v-model="currentSubscription.description" class="form-control" rows="4"></textarea>
              </div>

              <div class="form-group">
                <label>Цена (руб.):</label>
                <input type="number" v-model.number="currentSubscription.price" class="form-control">
              </div>

              <div class="form-group">
                <label>Период продления (дней):</label>
                <input type="number" v-model.number="currentSubscription.renewalPeriod" class="form-control">
              </div>

              <div class="form-group">
                <label>Особенности:</label>
                <div v-for="(feature, index) in currentSubscription.features" :key="index" class="feature-item">
                  <input type="text" v-model="currentSubscription.features[index]" class="form-control">
                  <button @click="removeFeature(index)" class="btn btn-sm btn-danger">×</button>
                </div>
                <button @click="addFeature" class="btn btn-sm btn-primary">
                  Добавить особенность
                </button>
              </div>

              <div class="action-buttons">
                <button @click="updateSubscription" class="btn btn-primary">
                  Сохранить изменения
                </button>
                <button @click="deleteSubscription" class="btn btn-danger" :disabled="currentSubscription.price === 0">
                  Удалить подписку
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Секция управления пользователями -->
        <section class="admin-section">
          <h2>Управление пользователями</h2>

          <div class="user-controls">
            <div class="form-group">
              <label for="user-search">Поиск пользователя:</label>
              <div class="search-input">
                <input id="user-search" type="text" v-model="userSearchQuery" placeholder="Введите email или имя"
                  class="form-control" @input="handleSearchInput">
                <button @click="searchUsers" class="btn btn-search">
                  <i class="search-icon">🔍</i>
                </button>
              </div>
            </div>

            <div class="users-per-page">
              <label>Пользователей на странице:</label>
              <select v-model="perPage" @change="loadUsers" class="form-control">
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="all">Все</option>
              </select>
            </div>
          </div>

          <div class="user-list">
            <table class="users-table">
              <thead>
                <tr>
                  <th @click="sortUsers('_id')">
                    ID <span v-if="sortField === '_id'">{{ sortIcon }}</span>
                  </th>
                  <th @click="sortUsers('email')">
                    Email <span v-if="sortField === 'email'">{{ sortIcon }}</span>
                  </th>
                  <th @click="sortUsers('username')">
                    Имя <span v-if="sortField === 'username'">{{ sortIcon }}</span>
                  </th>
                  <th @click="sortUsers('currentSubscription.planId')">
                    Подписка <span v-if="sortField === 'currentSubscription.planId'">{{ sortIcon }}</span>
                  </th>
                  <th @click="sortUsers('wallet.balance')">
                    Баланс <span v-if="sortField === 'wallet.balance'">{{ sortIcon }}</span>
                  </th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in paginatedUsers" :key="user._id">
                  <td>{{ user._id }}</td>
                  <td>{{ user.email }}</td>
                  <td>{{ user.username }}</td>
                  <td>
                    <span v-if="user.currentSubscription">
                      {{ getSubscriptionName(user.currentSubscription.planId) }}
                      <span v-if="user.currentSubscription.endDate">
                        (до {{ formatDate(user.currentSubscription.endDate) }})
                      </span>
                      <span v-else-if="user.currentSubscription.planId">(бессрочная)</span>
                    </span>
                    <span v-else>Нет подписки</span>
                  </td>
                  <td>{{ (user.wallet?.balance || 0).toFixed(2) }} руб.</td>
                  <td>
                    <button @click="editUser(user)" class="btn btn-sm btn-edit">
                      Редактировать
                    </button>
                    <button @click="deleteUser(user._id)" class="btn btn-sm btn-danger">
                      Удалить
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>

            <div v-if="loadingUsers" class="loading-indicator">
              Загрузка данных...
            </div>

            <div v-if="!loadingUsers && filteredUsers.length === 0" class="no-results">
              Пользователи не найдены
            </div>

            <div class="pagination-controls">
              <div class="pagination-info">
                Показано {{ endItem }} из {{ filteredUsers.length }}
              </div>

              <div class="pagination">
                <button @click="prevPage" :disabled="currentPage === 1" class="btn btn-pagination">
                  &lt;
                </button>

                <button v-for="page in pagesToShow" :key="page" @click="goToPage(page)"
                  :class="{ active: currentPage === page }" class="btn btn-pagination">
                  {{ page }}
                </button>

                <button @click="nextPage" :disabled="currentPage === totalPages" class="btn btn-pagination">
                  &gt;
                </button>
              </div>
            </div>
          </div>

          <!-- Модальное окно редактирования пользователя -->
          <div v-if="selectedUser" class="modal-overlay" @click.self="cancelUserEdit">
            <div class="modal-content">
              <div class="modal-header">
                <h3>Редактирование пользователя: {{ selectedUser.email }}</h3>
                <button @click="cancelUserEdit" class="btn btn-close">&times;</button>
              </div>

              <div class="modal-body">
                <div class="form-group">
                  <label>Имя:</label>
                  <input type="text" v-model="selectedUser.username" class="form-control">
                </div>

                <div class="form-group">
                  <label>Email:</label>
                  <input type="email" v-model="selectedUser.email" class="form-control">
                </div>

                <div class="form-group">
                  <label>Баланс:</label>
                  <input type="number" v-model.number="selectedUser.wallet.balance" class="form-control">
                </div>

                <div class="form-group">
                  <label>Подписка:</label>
                  <select v-model="selectedUser.currentSubscription.planId" class="form-control">
                    <option :value="null">Нет подписки</option>
                    <option v-for="sub in subscriptions" :key="sub._id" :value="sub._id">
                      {{ sub.name }}
                    </option>
                  </select>
                </div>

                <div v-if="selectedUser.currentSubscription.planId" class="form-group">
                  <label>Дата окончания подписки:</label>
                  <input type="date" v-model="selectedUser.currentSubscription.endDate" class="form-control">
                </div>

                <div v-if="selectedUser.currentSubscription.planId" class="form-group">
                  <label>Автопродление:</label>
                  <input type="checkbox" v-model="selectedUser.currentSubscription.autoRenew" class="form-checkbox">
                </div>

                <div class="form-group">
                  <label>Заметка администратора:</label>
                  <textarea v-model="selectedUser.currentSubscription.adminNote" class="form-control"
                    rows="3"></textarea>
                </div>
              </div>

              <div class="modal-footer">
                <button @click="updateUser" class="btn btn-primary">
                  Сохранить изменения
                </button>
                <button @click="cancelUserEdit" class="btn btn-secondary">
                  Отменить
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
    <div v-else class="auth-error">
      <h2>Доступ запрещен</h2>
      <p>Пожалуйста, войдите в систему</p>
      <button @click="$router.push('/admin/login')">Войти</button>
    </div>
  </div>
  <div v-else class="loading-screen">
    <p>Проверка авторизации...</p>
  </div>
</template>



<style scoped>
.admin-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.admin-sections {
  display: grid;
  grid-template-columns: minmax(300px, 1fr) minmax(600px, 2fr);
  gap: 30px;
  align-items: start;
}

.admin-section {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

h1,
h2,
h3 {
  color: #333;
}

h1 {
  margin-bottom: 30px;
  text-align: center;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ddd;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

textarea.form-control {
  min-height: 100px;
  resize: vertical;
}

.form-checkbox {
  margin-left: 10px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  white-space: nowrap;
}

/* Остальные стили кнопок остаются без изменений */

.user-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 15px;
}

.user-controls .form-group {
  flex: 1;
  min-width: 200px;
}

.users-per-page {
  min-width: 200px;
}

.user-list {
  overflow-x: auto;
  margin-top: 15px;
}

.users-table {
  width: 100%;
  min-width: 800px;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
  white-space: nowrap;
}

.users-table th {
  background-color: #f2f2f2;
  cursor: pointer;
  user-select: none;
  position: relative;
}

.users-table th:hover {
  background-color: #e6e6e6;
}

.users-table tr:hover {
  background-color: #f5f5f5;
}

/* Остальные стили остаются без изменений */

@media (max-width: 1200px) {
  .admin-sections {
    grid-template-columns: 1fr;
  }

  .user-controls {
    flex-direction: column;
    gap: 10px;
  }

  .users-per-page {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .admin-container {
    padding: 10px;
  }

  .admin-section {
    padding: 15px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
  
}
.btn-danger {
  background-color: #dc3545;
  color: white;
  margin-left: 5px;
}

.btn-danger:hover {
  background-color: #c82333;
}
</style>