<script>
import axios from 'axios'

export default {
  props: {
    onSuccess: Function,
    onCancel: Function
  },
  data() {
    return {
      credentials: {
        email: '',
        password: ''
      },
      loading: false,
      error: ''
    }
  },
  methods: {
    async handleLogin() {
      try {
        this.loading = true;
        const response = await axios.post('/api/admin/login', this.credentials);
        
        // 1. Сохраняем токены
        localStorage.setItem('adminAccessToken', response.data.accessToken);
        localStorage.setItem('adminRefreshToken', response.data.refreshToken);
        
        // 2. Закрываем модальное окно
        this.$emit('login-success');
        
        // 3. Перенаправляем 
        this.$router.push('/admin');
        
      } catch (error) {
        this.error = error.response?.data?.error || 'Ошибка авторизации';
      } finally {
        this.loading = false;
      }
    },
    onCancel(){
      this.$router.push('/');
    }
  }
}
</script>



<template>
  <div class="modal-overlay">
    <div class="modal-content">
      <h2>Вход в админ-панель</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Email:</label>
          <input v-model="credentials.email" type="email" required>
        </div>
        <div class="form-group">
          <label>Пароль:</label>
          <input v-model="credentials.password" type="password" required>
        </div>
        <div class="error-message" v-if="error">{{ error }}</div>
        <div class="modal-actions">
          <button type="submit" :disabled="loading">
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>
          <button type="button" @click="onCancel" class="cancel-btn">
            Отмена
          </button>
        </div>
      </form>
    </div>
  </div>
</template>



<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 100%;
  max-width: 400px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.error-message {
  color: red;
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
}

button {
  padding: 0.5rem 1rem;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
}
</style>