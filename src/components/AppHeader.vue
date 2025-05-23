<script>
import axios from 'axios';
import { mapState, mapGetters, mapActions } from 'vuex'

export default {
    data() {
        return {
            touchedFields: {
                login: {
                    email: false,
                    password: false
                },
                register: {
                    email: false,
                    password: false,
                    confirmPassword: false
                }
            }
        }
    },
    computed: {
        ...mapGetters([
            'currentUser',
            'isAuthenticated',
            'authError',
            'isLoading',
            'isMenuOpen',
            'modalOpen',
            'form',
        ]),
        userAvatar() {
            return this.currentUser?.avatar || '/default-avatar.png'
        },
        currentModal() {
            if (this.modalOpen('login')) return 'login'
            if (this.modalOpen('register')) return 'register'
            return null;
        },
        receiveNotifications() {
            return this.currentUser?.notifications?.email || false
        }
    },
    methods: {
        ...mapActions([
            'fetchUser',
            'login',
            'register',
            'logout',
            'toggleMenu',
            'openModal',
            'closeModal',
            'updateFormField'
        ]),
        goRoute(name) {
            if (this.$route.name !== name) {
                this.$router.push({ name })
            }
            this.toggleMenu(false)
            if (this.currentModal) {
                this.closeModal(this.currentModal)
            }
        },
        handleBlur(formType, field) {
            this.touchedFields[formType][field] = true;
        },
        handleInput(formType, field, value) {
            // Сбрасываем флаг touched при начале ввода
            if (field === 'email') {
                this.touchedFields[formType][field] = false;
            }
            this.updateFormField({
                formType,
                field,
                value
            });
        },
        showEmailError(formType) {
            return this.touchedFields[formType].email &&
                this.form(formType).email &&
                !this.validateEmail(this.form(formType).email);
        },
        showPasswordError(formType) {
            return this.touchedFields[formType].password &&
                this.form(formType).password &&
                this.form(formType).password.length < 8;
        },

        showConfirmPasswordError() {
            return this.touchedFields.register.confirmPassword &&
                this.form('register').confirmPassword &&
                this.form('register').password !== this.form('register').confirmPassword;
        },

        handleBackdropClick(e) {
            if (e.target.classList.contains('modal-backdrop') && this.currentModal) {
                this.closeModal(this.currentModal)
            }
        },

        async userLogin() {
            try {
                if (!this.validateEmail(this.form('login').email)) {
                    throw new Error('Пожалуйста, введите корректный email');
                }
                await this.login(this.form('login'))
            } catch (err) {
                alert(err.message || "Wrong email or password")
            }
        },

        async userRegister() {
            try {
                if (!this.validateEmail(this.form('register').email)) {
                    throw new Error('Пожалуйста, введите корректный email');
                }

                if (this.form('register').password.length < 8) {
                    throw new Error('Пароль должен содержать минимум 8 символов');
                }

                if (this.form('register').password !== this.form('register').confirmPassword) {
                    throw new Error('Пароли не совпадают');
                }
                const formData = {
                    ...this.form('register'),
                    notifications: {
                        email: this.receiveNotifications
                    }
                }
                console.log(formData)
                await this.register(formData)
            } catch (err) {
                    this.$notify({
                        title: 'Ошибка',
                        message: err.message || 'Произошла ошибка при регистрации',
                        type: 'error',
                        duration: 5000
                    });
            }
        },
        validateEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },
        switchModal(modalType) {
            if (this.currentModal) {
                this.closeModal(this.currentModal)
            }
            this.openModal(modalType)
        },
        updateField({ type, field, value }) {
            if (type === 'notification') {
                this.updateFormField({
                    formType: 'register',
                    field: 'receiveNotifications',
                    value
                })
            } else {
                this.updateFormField({
                    formType: type,
                    field,
                    value
                })
            }
        }
    },

    mounted() {
        document.addEventListener('click', this.handleBackdropClick)
        this.fetchUser()
    },
    beforeUnmount() {
        document.removeEventListener('click', this.handleBackdropClick)
        document.body.classList.remove('overflow-hidden')
    }
};
</script>

<template>
    <div>
        <!-- Блюр -->
        <transition name="fade">
            <div v-if="currentModal" class="fixed inset-0 bg-black/70 z-40 modal-backdrop"
                @click="closeModal(currentModal)"></div>
        </transition>

        <!-- Шапка -->
        <header class="bg-gray-800 shadow-xl sticky top-0 z-50 border-b border-gray-700">
            <div class="mx-auto flex h-16 max-w-screen-xl items-center gap-8 px-4 sm:px-6 lg:px-8">
                <router-link to="/" class="block text-teal-400 duration-500 hover:scale-105 transition-transform">
                    <span class="sr-only">Home</span>
                    <svg class="h-10" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="2" y="2" width="20" height="20" rx="6" stroke="currentColor" stroke-width="2" />
                        <text x="50%" y="55%" text-anchor="middle" font-size="14" fill="currentColor"
                            font-family="Arial, sans-serif">∞</text>
                        <path d="M8 16 Q12 20, 16 16" stroke="currentColor" stroke-width="2" fill="none" />
                    </svg>
                </router-link>

                <div class="flex flex-1 items-center justify-end md:justify-between">
                    <button @click="toggleMenu"
                        class="block md:hidden p-2 text-gray-400 hover:text-teal-400 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                            stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>

                    <nav aria-label="Global" class="hidden md:block">
                        <ul class="flex items-center gap-6 text-sm">
                            <li>
                                <router-link to="/"
                                    class="transition-all duration-300 text-gray-300 hover:text-teal-400 px-3 py-2 rounded-lg hover:bg-gray-700/50"
                                    active-class="text-teal-400 bg-gray-700/50">
                                    Главная
                                </router-link>
                            </li>
                            <li>
                                <router-link to="/page2"
                                    class="transition-all duration-300 text-gray-300 hover:text-teal-400 px-3 py-2 rounded-lg hover:bg-gray-700/50"
                                    active-class="text-teal-400 bg-gray-700/50">
                                    Каталог фильмов
                                </router-link>
                            </li>
                        </ul>
                    </nav>

                    <div class="hidden md:flex items-center gap-4">
                        <div class="sm:flex sm:gap-4">
                            <template v-if="isLoading">
                                <div class="flex items-center gap-3">
                                    <div class="h-9 w-9 rounded-full bg-gray-700 animate-pulse"></div>
                                    <div class="h-4 w-12 bg-gray-700 rounded animate-pulse"></div>
                                </div>
                            </template>
                            <template v-else>
                                <template v-if="!isAuthenticated">
                                    <button @click="openModal('login')"
                                        class="rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white transition-all hover:bg-teal-700 shadow-md hover:shadow-teal-500/20">
                                        Войти
                                    </button>
                                    <button @click="openModal('register')"
                                        class="rounded-lg bg-gray-700/50 px-5 py-2 text-sm font-medium text-white transition-all hover:bg-gray-700 border border-gray-600 hover:border-gray-500">
                                        Регистрация
                                    </button>
                                </template>

                                <template v-else>
                                    <div class="relative flex items-center gap-3">
                                        <router-link to="/profile"
                                            class="flex items-center gap-2 p-1 rounded-full transition-all hover:ring-2 hover:ring-teal-400/30">
                                            <img :src="userAvatar" alt="User Avatar"
                                                class="h-9 w-9 rounded-full border-2 border-teal-400 object-cover"
                                                loading="lazy" />
                                        </router-link>
                                        <button @click="logout"
                                            class="text-sm text-gray-400 hover:text-teal-400 transition-colors flex items-center gap-1">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none"
                                                viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                            </svg>
                                            Выйти
                                        </button>
                                    </div>
                                </template>
                            </template>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Меню для телефона -->
            <transition enter-active-class="transition-opacity duration-150 ease-out"
                leave-active-class="transition-opacity duration-100 ease-in" enter-from-class="opacity-0"
                enter-to-class="opacity-100" leave-from-class="opacity-100" leave-to-class="opacity-0">
                <div v-show="isMenuOpen" class="md:hidden bg-gray-800 shadow-xl border-t border-gray-700">
                    <div class="px-2 pt-2 pb-4 space-y-2 sm:px-3">
                        <template v-if="isLoading">
                            <div class="px-4 py-3 space-y-3">
                                <div class="h-6 w-3/4 bg-gray-700 rounded animate-pulse"></div>
                                <div class="h-6 w-1/2 bg-gray-700 rounded animate-pulse"></div>
                            </div>
                            <div class="pt-3 border-t border-gray-700 space-y-3">
                                <div class="h-10 w-full bg-gray-700 rounded-lg animate-pulse"></div>
                                <div class="h-10 w-full bg-gray-700 rounded-lg animate-pulse"></div>
                            </div>
                        </template>

                        <template v-else>
                            <router-link to="/"
                                class="block px-4 py-3 rounded-lg text-base font-medium text-gray-300 hover:text-teal-400 hover:bg-gray-700/50 transition-colors"
                                active-class="text-teal-400 bg-gray-700/50" @click="toggleMenu(false)">
                                Главная
                            </router-link>
                            <router-link to="/page2"
                                class="block px-4 py-3 rounded-lg text-base font-medium text-gray-300 hover:text-teal-400 hover:bg-gray-700/50 transition-colors"
                                active-class="text-teal-400 bg-gray-700/50" @click="toggleMenu(false)">
                                Каталог фильмов
                            </router-link>

                            <div v-if="!isAuthenticated" class="pt-3 border-t border-gray-700">
                                <button @click="openModal('login')"
                                    class="w-full text-left block px-4 py-3 rounded-lg text-base font-medium text-gray-300 hover:text-teal-400 hover:bg-gray-700/50 transition-colors flex items-center gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                                        viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                                    </svg>
                                    Войти
                                </button>
                                <button @click="openModal('register')"
                                    class="w-full text-left block px-4 py-3 rounded-lg text-base font-medium text-gray-300 hover:text-teal-400 hover:bg-gray-700/50 transition-colors flex items-center gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                                        viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                                    </svg>
                                    Регистрация
                                </button>
                            </div>

                            <div v-else class="border-t border-gray-700 pt-3 space-y-2">
                                <router-link to="/profile"
                                    class="flex items-center px-4 py-3 text-gray-300 hover:text-teal-400 rounded-lg hover:bg-gray-700/50 transition-colors"
                                    @click="toggleMenu(false)">
                                    <img :src="userAvatar" alt="User Avatar"
                                        class="h-8 w-8 rounded-full mr-3 border-2 border-teal-400" loading="lazy">
                                    <span>Профиль</span>
                                </router-link>
                                <button @click="logout"
                                    class="block px-4 py-3 text-gray-300 hover:text-red-400 rounded-lg transition-colors flex items-center gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                                        viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                    </svg>
                                    Выйти
                                </button>
                            </div>
                        </template>
                    </div>
                </div>
            </transition>
        </header>

        <!-- Модальное окно для комп -->
        <transition name="modal-fade">
            <div v-if="modalOpen && currentModal === 'login'"
                class="fixed inset-0 flex items-center justify-center z-50 p-4 pointer-events-none">
                <div class="bg-gray-800 rounded-xl shadow-2xl border border-gray-700 max-w-md w-full relative pointer-events-auto"
                    style="transform: translateZ(0);">
                    <button @click="closeModal('login')"
                        class="absolute top-4 right-4 text-gray-400 hover:text-white p-1 rounded-full hover:bg-gray-700/50 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                            stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>

                    <div class="p-6">
                        <h2 class="text-2xl font-bold mb-6 text-center text-teal-400">
                            Вход в аккаунт
                        </h2>

                        <form @submit.prevent="userLogin" class="space-y-4">
                            <div>
                                <label class="block text-gray-400 mb-2">Email</label>
                                <input type="email"
                                    class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                                    placeholder="Ваш email" required v-model="form('login').email"
                                    @input="handleInput('login', 'email', $event.target.value)"
                                    @blur="handleBlur('login', 'email')" pattern="[^\s@]+@[^\s@]+\.[^\s@]+"
                                    title="Пожалуйста, введите корректный email (например, user@example.com)" />
                                <p v-if="showEmailError('login')" class="text-red-400 text-xs mt-1">
                                    Пожалуйста, введите корректный email
                                </p>
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-2">Пароль</label>
                                <input type="password"
                                    class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                                    placeholder="••••••••" required :value="form('login').password" minlength="8"
                                    @input="updateFormField({ formType: 'login', field: 'password', value: $event.target.value })" />
                            </div>

                            <button type="submit"
                                class="w-full mt-4 bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 px-4 rounded-lg transition-colors">
                                Войти
                            </button>

                            <div class="text-center mt-4 text-gray-400">
                                Нет аккаунта?
                                <button type="button" @click="switchModal('register')"
                                    class="text-teal-400 hover:text-teal-300 ml-1 underline">
                                    Регистрация
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </transition>

        <transition name="modal-fade">
            <div v-if="modalOpen && currentModal === 'register'"
                class="fixed inset-0 flex items-center justify-center z-50 p-4 pointer-events-none">
                <div class="bg-gray-800 rounded-xl shadow-2xl border border-gray-700 max-w-md w-full relative pointer-events-auto"
                    style="transform: translateZ(0);">
                    <button @click="closeModal('register')"
                        class="absolute top-4 right-4 text-gray-400 hover:text-white p-1 rounded-full hover:bg-gray-700/50 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                            stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>

                    <div class="p-6">
                        <h2 class="text-2xl font-bold mb-6 text-center text-teal-400">
                            Регистрация
                        </h2>

                        <form @submit.prevent="userRegister" class="space-y-4">
                            <div>
                                <label class="block text-gray-400 mb-2">Имя</label>
                                <input type="text"
                                    class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                                    placeholder="Ваше имя" required :value="form('register').username"
                                    @input="updateFormField({ formType: 'register', field: 'username', value: $event.target.value })" />
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-2">Email</label>
                                <input type="email"
                                    class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                                    placeholder="Ваш email" required v-model="form('register').email"
                                    @input="handleInput('register', 'email', $event.target.value)"
                                    @blur="handleBlur('register', 'email')" pattern="[^\s@]+@[^\s@]+\.[^\s@]+"
                                    title="Пожалуйста, введите корректный email (например, user@example.com)" />
                                <p v-if="showEmailError('register')" class="text-red-400 text-xs mt-1">
                                    Пожалуйста, введите корректный email
                                </p>
                            </div>

                            <div>
                                <label class="block text-gray-400 mb-2">Пароль</label>
                                <input type="password"
                                    class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                                    placeholder="••••••••" required minlength="8" v-model="form('register').password"
                                    @input="updateFormField({ formType: 'register', field: 'password', value: $event.target.value })"
                                    @blur="handleBlur('register', 'password')" />
                                <p v-if="showPasswordError('register')" class="text-red-400 text-xs mt-1">
                                    Пароль должен содержать минимум 8 символов
                                </p>
                            </div>

                            <div>
                                <label class="block text-gray-400 mb-2">Подтвердите пароль</label>
                                <input type="password"
                                    class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                                    placeholder="••••••••" required minlength="8"
                                    v-model="form('register').confirmPassword"
                                    @input="updateFormField({ formType: 'register', field: 'confirmPassword', value: $event.target.value })"
                                    @blur="handleBlur('register', 'confirmPassword')" />
                                <p v-if="showConfirmPasswordError()" class="text-red-400 text-xs mt-1">
                                    Пароли не совпадают
                                </p>
                            </div>

                            <div class="flex items-center mt-4">
                                <input type="checkbox" id="notifications"
                                    :checked="form('register').receiveNotifications" @change="updateField({
                                        type: 'register',
                                        field: 'receiveNotifications',
                                        value: $event.target.checked
                                    })"
                                    class="h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-600 rounded bg-gray-700">
                                <label for="notifications" class="ml-2 block text-gray-400">
                                    Получать уведомления на почту
                                </label>
                            </div>

                            <button type="submit"
                                class="w-full mt-4 bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 px-4 rounded-lg transition-colors">
                                Зарегистрироваться
                            </button>

                            <div class="text-center mt-4 text-gray-400">
                                Уже есть аккаунт?
                                <button type="button" @click="switchModal('login')"
                                    class="text-teal-400 hover:text-teal-300 ml-1 underline">
                                    Войти
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
    transition: opacity 0.25s ease, transform 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
    opacity: 0;
    transform: scale(0.95);
}

a,
button {
    cursor: pointer;
    outline: none;
    -webkit-tap-highlight-color: transparent;
}

img {
    transition: transform 0.15s ease, border-color 0.15s ease;
}

@media (prefers-reduced-motion: reduce) {

    .fade-enter-active,
    .fade-leave-active,
    .modal-fade-enter-active,
    .modal-fade-leave-active {
        transition: none !important;
    }

    .modal-fade-enter-from,
    .modal-fade-leave-to {
        transform: none;
    }
}

.modal-backdrop {
    will-change: opacity;
    -webkit-backface-visibility: hidden;
}

.optimize-transform {
    transform: translateZ(0);
}

.animate-pulse {
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {

    0%,
    100% {
        opacity: 0.5;
    }

    50% {
        opacity: 0.3;
    }

}

input:invalid {
    border-color: #f87171;
    /* red-400 */
}

input:focus:invalid {
    border-color: #f87171;
    box-shadow: 0 0 0 2px rgba(248, 113, 113, 0.2);
}
</style>