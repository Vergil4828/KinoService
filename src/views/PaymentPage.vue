<script>
import axios from 'axios';
import { mapGetters, mapActions } from 'vuex';

export default {
  data() {
    return {
      planName: '',
      planPrice: 0,
      loading: false,
      showDepositModal: false,
      depositAmount: 0,
      error: null,
      planId: null,
      showYooMoneyForm: false, 
      cardNumber: '',
      cardExpiry: '',
      cardCvv: '',
      cardName: '',
      paymentProcessing: false
    };
  },
  computed: {
    ...mapGetters(['walletBalance']),
    missingAmount() {
      return Math.max(0, this.planPrice - this.walletBalance);
    },
    minDepositAmount() {
      return Math.max(this.missingAmount, 10);
    },
    isCardValid() {
      return (
        this.cardNumber.replace(/\s/g, '').length === 16 &&
        this.cardExpiry.length === 5 &&
        this.cardCvv.length === 3 &&
        this.cardName.trim().length > 0
      );
    }
  },
  async created() {
    this.planId = this.$route.params.planId;
    await this.fetchPlanDetails(this.planId);
    await this.fetchWallet();
    this.depositAmount = this.minDepositAmount;
  },
  methods: {
    ...mapActions(['fetchPlan', 'deposit', 'purchasePlan', 'fetchWallet']),

    async fetchPlanDetails(planId) {
      try {
        const response = await this.fetchPlan(planId);
        this.planName = response.data.name;
        this.planPrice = response.data.price;
      } catch (error) {
        this.error = 'Не удалось загрузить информацию о подписке';
        console.error(error);
      }
    },

    openDepositModal() {
      this.showDepositModal = true;
      this.error = null;
    },

    closeDepositModal() {
      this.showDepositModal = false;
    },

    toggleYooMoneyForm() {
      this.showYooMoneyForm = !this.showYooMoneyForm;
      this.error = null;
    },

    formatCardNumber() {
      this.cardNumber = this.cardNumber
        .replace(/\D/g, '')
        .replace(/(\d{4})(?=\d)/g, '$1 ');
    },

    formatExpiry() {
      this.cardExpiry = this.cardExpiry
        .replace(/\D/g, '')
        .replace(/(\d{2})(?=\d)/g, '$1/');
    },

    async handleDeposit() {
      if (this.depositAmount < this.minDepositAmount) {
        this.error = `Минимальная сумма пополнения: ${this.minDepositAmount} ₽`;
        return;
      }

      try {
        this.loading = true;
        await this.deposit(this.depositAmount);
        
        // Закрываем формы после успешного пополнения
        this.closeDepositModal();
        this.showYooMoneyForm = false;

        // Пытаемся купить подписку
        const result = await this.purchasePlan({ planId: this.planId });

        if (result.success) {
          this.$router.push('/profile');
          this.$notify({
            title: "Успех",
            text: "Подписка успешно оформлена",
            type: "success"
          });
        } else if (result.paymentRequired) {
          this.error = `Не хватает ${result.requiredAmount} ₽. Пополните счет.`;
        }
      } catch (error) {
        this.error = error.response?.data?.error || 'Ошибка при пополнении';
      } finally {
        this.loading = false;
        this.paymentProcessing = false;
      }
    },

    async processYooMoneyPayment() {
      if (!this.isCardValid) {
        this.error = 'Пожалуйста, заполните все поля карты правильно';
        return;
      }

      this.paymentProcessing = true;
      this.error = null;

      try {
        // Симулируем обработку платежа
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Устанавливаем сумму депозита равную недостающей сумме
        this.depositAmount = this.missingAmount;
        
        // Вызываем тот же метод, что и для обычного пополнения
        await this.handleDeposit();
      } catch (error) {
        this.error = error.response?.data?.error || 'Ошибка при оплате';
      }
    }
  }
};
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white py-20 px-4">
    <div class="max-w-md mx-auto text-center">
      <h1 class="text-3xl font-bold mb-6">Недостаточно средств</h1>

      <div class="bg-gray-800 rounded-xl p-8 mb-8">
        <p class="text-2xl mb-4">Для подписки "{{ planName }}" нужно {{ planPrice }} ₽</p>
        <p class="text-gray-400 mb-2">На вашем счету: {{ walletBalance }} ₽</p>
        <p class="text-red-400 font-medium mb-6">Не хватает: {{ missingAmount }} ₽</p>

        <div class="space-y-4">
          <button @click="openDepositModal" class="w-full py-3 bg-teal-600 hover:bg-teal-700 rounded-lg font-medium">
            Пополнить кошелек
          </button>

          <template v-if="!showYooMoneyForm">
            <button @click="toggleYooMoneyForm" :disabled="loading"
              class="w-full py-3 bg-yellow-500 hover:bg-yellow-600 rounded-lg font-medium">
              Оплатить через YooMoney
            </button>
          </template>
        </div>

        <!-- Форма YooMoney -->
        <div v-if="showYooMoneyForm" class="mt-6 p-4 bg-gray-700 rounded-lg text-left">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium">Оплата через YooMoney</h3>
            <button @click="toggleYooMoneyForm" class="text-gray-400 hover:text-white">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-gray-400 text-sm mb-1">Номер карты</label>
              <input v-model="cardNumber" @input="formatCardNumber" placeholder="1234 5678 9012 3456"
                maxlength="19" class="w-full p-3 bg-gray-600 border border-gray-500 rounded-lg">
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-gray-400 text-sm mb-1">Срок действия</label>
                <input v-model="cardExpiry" @input="formatExpiry" placeholder="MM/YY" maxlength="5"
                  class="w-full p-3 bg-gray-600 border border-gray-500 rounded-lg">
              </div>
              <div>
                <label class="block text-gray-400 text-sm mb-1">CVV/CVC</label>
                <input v-model="cardCvv" type="password" placeholder="123" maxlength="3"
                  class="w-full p-3 bg-gray-600 border border-gray-500 rounded-lg">
              </div>
            </div>

            <div>
              <label class="block text-gray-400 text-sm mb-1">Имя на карте</label>
              <input v-model="cardName" placeholder="IVAN IVANOV"
                class="w-full p-3 bg-gray-600 border border-gray-500 rounded-lg">
            </div>

            <div v-if="error" class="text-red-400 text-sm">{{ error }}</div>

            <button @click="processYooMoneyPayment" :disabled="!isCardValid || paymentProcessing"
              class="w-full py-3 bg-yellow-500 hover:bg-yellow-600 rounded-lg font-medium disabled:opacity-50">
              <span v-if="!paymentProcessing">Оплатить {{ missingAmount }} ₽</span>
              <span v-else>Обработка платежа...</span>
            </button>

            <div class="flex items-center text-gray-400 text-xs">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>Платежи защищены по стандарту PCI DSS</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Модальное окно пополнения -->
      <div v-if="showDepositModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <h3 class="text-xl font-bold mb-4 text-teal-400">Пополнение кошелька</h3>

          <div class="mb-4">
            <label class="block text-gray-400 mb-2">Сумма (RUB)</label>
            <input v-model.number="depositAmount" type="number" :min="missingAmount" step="100"
              class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500">
          </div>

          <div v-if="error" class="text-red-400 mb-4">{{ error }}</div>

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
    </div>
  </div>
</template>