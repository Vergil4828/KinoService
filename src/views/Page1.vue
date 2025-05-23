<script>
import { mapState, mapGetters, mapActions } from 'vuex'
export default {
    mounted() {
        this.initSmoothScroll();
        this.loadSubscriptions();
    },
    computed: {

        ...mapGetters(['plans']),
        isAuthenticated() {
            return this.$store.getters.isAuthenticated;
        },
        activePlanId() {
            return this.$store.getters.activeSubscriptionPlanId;
        }
    },
    methods: {
        initSmoothScroll() {
            const links = document.querySelectorAll('a[href^="#"]');

            links.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetId = link.getAttribute('href');
                    if (targetId === '#') return;

                    const targetElement = document.querySelector(targetId);
                    if (targetElement) {
                        targetElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        },
        async loadSubscriptions() {

            try {


                await this.$store.dispatch('fetchPlans');

                if (this.isAuthenticated) {
                    await this.$store.dispatch('fetchCurrentSubscription');
                }
            } catch (error) {
                console.error('Ошибка загрузки подписок:', error);
                this.$notify({
                    title: "Ошибка",
                    text: "Не удалось загрузить информацию о подписке",
                    type: "error"
                });

            }
        },
        async selectPlan(planId) {
            if (!this.isAuthenticated) {
                this.$router.push('/login');
                return;
            }

            try {
                this.$notify({ clean: true });
                const result = await this.$store.dispatch('purchasePlan', { planId });

                if (result?.paymentRequired) {
                    this.$router.push(`/payment/${planId}?amount=${result.requiredAmount}`);
                } else if (result?.success) {
                    this.$notify({
                        title: "Успех",
                        text: "Подписка успешно оформлена",
                        type: "success",
                        duration: 5000
                    });


                    await this.loadSubscriptions();
                }
            } catch (error) {
                this.$notify({
                    title: "Ошибка",
                    text: error.message,
                    type: "error",
                    duration: 10000
                });
            }
        },
        isActivePlan(planId) {
            if (!this.isAuthenticated) return false;
            return this.activePlanId === planId;
        },
        getPlanBadge(planId, defaultName) {
            return this.isActivePlan(planId) ? 'Ваш тариф' : defaultName;
        }
    }
}
</script>

<template>
    <main class="bg-gray-900 text-white overflow-hidden">
        <!-- Блок с параллакс-эффектом -->
        <section
            class="relative flex items-center justify-center min-h-screen bg-cover bg-center bg-fixed overflow-hidden"
            style="background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url('/hero-bg.jpg');">
            <div class="text-center px-4 max-w-4xl transform transition-all duration-500 hover:scale-105">
                <h1
                    class="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent">
                    Фильмы и сериалы в 4K качестве
                </h1>
                <p class="mt-4 text-xl md:text-2xl text-gray-300">
                    Тысячи фильмов без рекламы на всех ваших устройствах
                </p>
                <div class="mt-8 flex flex-col sm:flex-row justify-center gap-4">
                    <a href="#subscribe"
                        class="px-8 py-4 bg-gradient-to-r from-teal-600 to-blue-600 text-lg rounded-lg hover:from-teal-700 hover:to-blue-700 transition-all duration-300 shadow-lg hover:shadow-teal-500/30 transform hover:-translate-y-1">
                        Оформить подписку
                    </a>
                    <a href="#popular_films"
                        class="px-8 py-4 border-2 border-teal-400 text-lg rounded-lg hover:bg-teal-400 hover:text-gray-900 transition-all duration-300 transform hover:-translate-y-1">
                        Популярные фильмы
                    </a>
                </div>
            </div>

            <div class="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
                <svg class="h-8 w-8 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
            </div>
        </section>

        <!-- Преимущества с анимацией появления -->
        <section class="py-20 px-4 text-center">
            <div class="max-w-6xl mx-auto">
                <h2 class="text-4xl font-bold mb-16 relative inline-block">
                    <span class="relative z-10">Почему выбирают нас?</span>
                    <span
                        class="absolute -bottom-2 left-0 w-full h-1 bg-gradient-to-r from-teal-400 to-blue-500 rounded-full"></span>
                </h2>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-12">
                    <div
                        class="p-8 bg-gray-800 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-teal-500/10">
                        <div
                            class="mx-auto h-20 w-20 bg-teal-500/20 rounded-full flex items-center justify-center mb-6">
                            <svg class="h-12 w-12 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                            </svg>
                        </div>
                        <h3 class="text-xl font-semibold mb-3">4K HDR качество</h3>
                        <p class="text-gray-400">Наслаждайтесь кристально чистым изображением с поддержкой HDR10+</p>
                    </div>

                    <div
                        class="p-8 bg-gray-800 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-teal-500/10">
                        <div
                            class="mx-auto h-20 w-20 bg-teal-500/20 rounded-full flex items-center justify-center mb-6">
                            <svg class="h-12 w-12 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                            </svg>
                        </div>
                        <h3 class="text-xl font-semibold mb-3">Мультиплатформенность</h3>
                        <p class="text-gray-400">Смотрите на телевизоре, смартфоне, планшете или компьютере</p>
                    </div>

                    <div
                        class="p-8 bg-gray-800 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-teal-500/10">
                        <div
                            class="mx-auto h-20 w-20 bg-teal-500/20 rounded-full flex items-center justify-center mb-6">
                            <svg class="h-12 w-12 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                        </div>
                        <h3 class="text-xl font-semibold mb-3">Без рекламы</h3>
                        <p class="text-gray-400">Полное погружение в кино без навязчивой рекламы</p>
                    </div>
                </div>
            </div>
        </section>


        <!-- Тарифные планы с акцентом на премиум -->
        <section id="subscribe" class="py-20 px-4 bg-gradient-to-b from-gray-800 to-gray-900">
            <div class="max-w-6xl mx-auto">
                <h2 class="text-4xl font-bold mb-4 text-center">Выберите свой тариф</h2>
                <!--<p class="text-xl text-gray-400 mb-16 text-center">Попробуйте 7 дней бесплатно, без обязательств</p>-->

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <!-- Динамический вывод планов -->
                    <div v-for="plan in plans" :key="plan._id"
                        class="relative border-2 border-teal-400 bg-gray-800 rounded-xl p-8 transform hover:-translate-y-2 transition-all duration-300 shadow-xl shadow-teal-500/10 flex flex-col h-full"
                        :class="{
                            'border-blue-400 hover:shadow-blue-500/10': plan._id === '67f437687b06d9a11720a6ce',
                            'border-purple-400 hover:shadow-purple-500/10': plan._id === '67f437687b06d9a11720a6d4',
                            'border-red-400 hover:shadow-red-500/10': !['67f437687b06d9a11720a6ce', '67f437687b06d9a11720a6d1', '67f437687b06d9a11720a6d4'].includes(plan._id)
                        }">

                        <!-- Бейдж с названием тарифа -->
                        <div class="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 px-4 py-2 rounded-full text-sm font-semibold text-gray-900"
                            :class="{
                                'bg-blue-500': plan._id === '67f437687b06d9a11720a6ce',
                                'bg-teal-500': plan._id === '67f437687b06d9a11720a6d1',
                                'bg-purple-500': plan._id === '67f437687b06d9a11720a6d4',
                                'bg-red-500': !['67f437687b06d9a11720a6ce', '67f437687b06d9a11720a6d1', '67f437687b06d9a11720a6d4'].includes(plan._id)
                            }">
                            {{ isActivePlan(plan._id) ? 'Ваш тариф' : plan.name }}
                        </div>

                        <div class="text-center mt-6 flex-grow">
                            <p class="text-5xl font-bold mb-4">
                                {{ plan.price }} ₽<span class="text-lg text-gray-400">/мес</span>
                            </p>
                            <ul class="space-y-3 mb-8">
                                <li v-for="feature in plan.features" :key="feature" class="flex items-center">
                                    <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                        :class="{
                                            'text-blue-400': plan._id === '67f437687b06d9a11720a6ce',
                                            'text-teal-400': plan._id === '67f437687b06d9a11720a6d1',
                                            'text-purple-400': plan._id === '67f437687b06d9a11720a6d4',
                                            'text-red-400': !['67f437687b06d9a11720a6ce', '67f437687b06d9a11720a6d1', '67f437687b06d9a11720a6d4'].includes(plan._id)
                                        }">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M5 13l4 4L19 7" />
                                    </svg>
                                    {{ feature }}
                                </li>
                            </ul>
                        </div>

                        <button v-if="isActivePlan(plan._id)"
                            class="w-full py-3 rounded-lg transition-colors duration-300 mt-auto" :class="{
                                'bg-blue-500 hover:bg-blue-600': plan._id === '67f437687b06d9a11720a6ce',
                                'bg-teal-500 hover:bg-teal-600': plan._id === '67f437687b06d9a11720a6d1',
                                'bg-purple-500 hover:bg-purple-600': plan._id === '67f437687b06d9a11720a6d4',
                                'bg-red-500 hover:bg-red-600': !['67f437687b06d9a11720a6ce', '67f437687b06d9a11720a6d1', '67f437687b06d9a11720a6d4'].includes(plan._id)
                            }">
                            Активен
                        </button>
                        <button v-else @click="selectPlan(plan._id)" :disabled="!isAuthenticated" :class="{
                            'opacity-50 cursor-not-allowed': !isAuthenticated,
                            'bg-blue-500 hover:bg-blue-600': plan._id === '67f437687b06d9a11720a6ce',
                            'bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600': plan._id === '67f437687b06d9a11720a6d1',
                            'bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600': plan._id === '67f437687b06d9a11720a6d4',
                            'bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600': !['67f437687b06d9a11720a6ce', '67f437687b06d9a11720a6d1', '67f437687b06d9a11720a6d4'].includes(plan._id)
                        }"
                            class="w-full py-3 rounded-lg transition-all duration-300 shadow-md hover:shadow-teal-500/30 mt-auto">
                            {{ isAuthenticated ? 'Выбрать' : 'Войдите для выбора' }}
                        </button>
                    </div>
                </div>
            </div>
        </section>
        <!-- Популярные фильмы с каруселью -->
        <section id="popular_films" class="py-20 px-4">
            <div class="max-w-6xl mx-auto">
                <div class="flex justify-center">
                    <h2 class="text-4xl font-bold mb-16 relative inline-block">
                        <span class="relative z-10">Популярные фильмы</span>
                        <span
                            class="absolute -bottom-2 left-0 w-full h-1 bg-gradient-to-r from-teal-400 to-blue-500 rounded-full"></span>
                    </h2>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    <div
                        class="group relative overflow-hidden rounded-xl shadow-lg transition-all duration-500 transform hover:-translate-y-2 hover:hover:shadow-teal-500/20">
                        <div class="aspect-w-2 aspect-h-3 bg-gray-800 rounded-xl overflow-hidden">
                            <img src="https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDktN2IxOS00OGEyLWFmMjktY2FiMmZkNWIyODZiXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_FMjpg_UX1000_.jpg"
                                alt="Интерстеллар"
                                class="object-cover w-full h-full group-hover:opacity-75 transition-opacity duration-300">
                        </div>
                        <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4"
                            style="z-index: 10; color: white;">
                            <h3 class="text-xl font-bold">Интерстеллар</h3>
                            <p class="text-teal-400">Фантастика, 2014</p>
                            <div class="flex items-center mt-2">
                                <svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path
                                        d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                                <span class="ml-1">8.6</span>
                            </div>
                        </div>
                    </div>

                    <div
                        class="group relative overflow-hidden rounded-xl shadow-lg transition-all duration-500 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-teal-500/20">
                        <div class="aspect-w-2 aspect-h-3 bg-gray-800 rounded-xl overflow-hidden">
                            <img src="https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_.jpg"
                                alt="Начало"
                                class="object-cover w-full h-full group-hover:opacity-75 transition-opacity duration-300">
                        </div>
                        <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4"
                            style="z-index: 10; color: white;">
                            <h3 class="text-xl font-bold">Начало</h3>
                            <p class="text-teal-400">Фантастика, 2010</p>
                            <div class="flex items-center mt-2">
                                <svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path
                                        d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                                <span class="ml-1">8.8</span>
                            </div>
                        </div>
                    </div>

                    <div
                        class="group relative overflow-hidden rounded-xl shadow-lg transition-all duration-500 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-teal-500/20">
                        <div class="aspect-w-2 aspect-h-3 bg-gray-800 rounded-xl overflow-hidden">
                            <img src="https://cdn.ananasposter.ru/image/cache/catalog/poster/film/87/6240-1000x830.jpg"
                                alt="Бойцовский клуб"
                                class="object-cover w-full h-full group-hover:opacity-75 transition-opacity duration-300">
                        </div>
                        <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4"
                            style="z-index: 10; color: white;">
                            <h3 class="text-xl font-bold">Бойцовский клуб</h3>
                            <p class="text-teal-400">Драма, 1999</p>
                            <div class="flex items-center mt-2">
                                <svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path
                                        d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                                <span class="ml-1">8.8</span>
                            </div>
                        </div>
                    </div>

                    <div
                        class="group relative overflow-hidden rounded-xl shadow-lg transition-all duration-500 transform hover:-translate-y-2 hover:shadow-xl hover:shadow-teal-500/20">
                        <div class="aspect-w-2 aspect-h-3 bg-gray-800 rounded-xl overflow-hidden">
                            <img src="https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_.jpg"
                                alt="Темный рыцарь"
                                class="object-cover w-full h-full group-hover:opacity-75 transition-opacity duration-300">
                        </div>
                        <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4"
                            style="z-index: 10; color: white;">
                            <h3 class="text-xl font-bold">Темный рыцарь</h3>
                            <p class="text-teal-400">Боевик, 2008</p>
                            <div class="flex items-center mt-2">
                                <svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path
                                        d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                                <span class="ml-1">9.0</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-12 text-center">
                    <button
                        class="px-8 py-3 border-2 border-teal-400 text-lg rounded-lg hover:bg-teal-400 hover:text-gray-900 transition-all duration-300">
                        Показать больше
                    </button>
                </div>
            </div>
        </section>

        <!-- CTA с параллакс-эффектом -->
        <section class="relative py-32 bg-cover bg-center bg-fixed overflow-hidden"
            style="background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url('/cta-bg.jpg');">
            <div class="max-w-4xl mx-auto text-center px-4">
                <h2 class="text-4xl md:text-5xl font-bold mb-6">Готовы начать смотреть?</h2>
                <!-- <p class="text-xl text-gray-300 mb-8">Подключите подписку прямо сейчас и получите 7 дней бесплатного 
                    доступа</p> -->
                <a href="#subscribe"
                    class="inline-block px-8 py-4 bg-gradient-to-r from-teal-500 to-blue-500 text-lg font-semibold rounded-lg hover:from-teal-600 hover:to-blue-600 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-teal-500/30">
                    Начать бесплатный период
                </a>
            </div>
        </section>
    </main>
</template>

<style>
/* Плавная прокрутка для всего документа */
html {
    scroll-behavior: smooth;
}

/* Анимация появления секций */
section {
    view-timeline-name: --section;
    view-timeline-axis: block;

    animation-timeline: --section;
    animation-name: fadeIn;

    animation-range: entry 25% cover 30%;
    animation-fill-mode: both;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Оптимизация анимаций */
@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
        scroll-behavior: auto !important;
    }
}

/* Градиентный текст */
.gradient-text {
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
}



.disabled-plan {
    opacity: 0.7;
    filter: grayscale(30%);
    pointer-events: none;
}
</style>