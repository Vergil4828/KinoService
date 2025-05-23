<script>
export default {
  data() {
    return {
      activeTab: 'all',
      selectedGenres: [],
      genres: [
        { id: 'action', name: 'Боевик', color: 'red' },
        { id: 'comedy', name: 'Комедия', color: 'yellow' },
        { id: 'drama', name: 'Драма', color: 'blue' },
        { id: 'fantasy', name: 'Фантастика', color: 'green' },
        { id: 'horror', name: 'Ужасы', color: 'purple' },
        { id: 'romance', name: 'Романтика', color: 'pink' }
      ]
    }
  },
  methods: {
    toggleGenre(genreId) {
      if (genreId === 'all') {
        this.selectedGenres = [];
      } else {
        const index = this.selectedGenres.indexOf(genreId);
        if (index === -1) {
          this.selectedGenres.push(genreId);
        } else {
          this.selectedGenres.splice(index, 1);
        }
      }
    },
    isGenreSelected(genreId) {
      return genreId === 'all' 
        ? this.selectedGenres.length === 0
        : this.selectedGenres.includes(genreId);
    }
  }
}
</script>

<template>
  <section class="py-12 bg-gradient-to-b from-gray-900 to-gray-800 text-white">
    <!-- Упрощенный контейнер без лишних отступов -->
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <h2 class="text-4xl font-bold text-center mb-12">Каталог фильмов</h2>

      <!-- Группа кнопок тарифов -->
      <div class="mb-8 flex justify-center gap-3">
        <button 
          v-for="tab in [
            { id: 'free', name: 'Базовый', color: 'indigo' },
            { id: 'basic', name: 'Популярный', color: 'purple' },
            { id: 'premium', name: 'Премиум+', color: 'pink' }
          ]"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-5 py-2 rounded-full transition whitespace-nowrap"
          :class="activeTab === tab.id 
            ? `bg-${tab.color}-600 hover:bg-${tab.color}-700 text-white` 
            : 'bg-gray-700 hover:bg-gray-600 text-gray-300'"
        >
          {{ tab.name }}
        </button>
      </div>

      <!-- Поле поиска -->
      <div class="mb-8 max-w-2xl mx-auto">
        <input 
          type="text" 
          placeholder="Поиск фильма..."
          class="w-full px-5 py-3 rounded-lg bg-gray-800 text-white border-none focus:outline-none focus:ring-2 focus:ring-teal-500"
        >
      </div>

      <!-- Фильтрация по жанрам -->
      <div class="mb-8 flex flex-wrap justify-center gap-3">
        <button 
          @click="toggleGenre('all')"
          class="px-5 py-2 rounded-full transition"
          :class="isGenreSelected('all') 
            ? 'bg-teal-600 hover:bg-teal-700' 
            : 'bg-gray-700 hover:bg-gray-600'"
        >
          Все
        </button>
        
        <button 
          v-for="genre in genres"
          :key="genre.id"
          @click="toggleGenre(genre.id)"
          class="px-5 py-2 rounded-full transition relative"
          :class="{
            [`bg-${genre.color}-600 hover:bg-${genre.color}-700`]: isGenreSelected(genre.id),
            'bg-gray-700 hover:bg-gray-600': !isGenreSelected(genre.id)
          }"
        >
          {{ genre.name }}
          
        </button>
      </div>

      <!-- Сетка фильмов -->
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div 
          v-for="(movie, index) in 12" 
          :key="index"
          class="rounded-lg overflow-hidden shadow-lg bg-gray-800 hover:bg-gray-700 transition transform hover:-translate-y-1"
        >
          <div class="overflow-hidden">
            <img 
              src="https://via.placeholder.com/300x450" 
              alt="Название фильма"
              class="w-full h-64 object-cover transition-transform duration-300 hover:scale-105"
            >
          </div>
          <div class="p-4">
            <h3 class="text-lg font-semibold">Фильм {{ index + 1 }}</h3>
            <div class="flex justify-between items-center mt-2">
              <p class="text-sm text-gray-400">⭐ {{ (8.5 - index * 0.2).toFixed(1) }}</p>
              <span 
                class="text-xs px-2 py-1 rounded"
                :class="{
                  'bg-indigo-600': index % 3 === 0,
                  'bg-purple-600': index % 3 === 1,
                  'bg-pink-600': index % 3 === 2
                }"
              >
                {{ index % 3 === 0 ? 'Бесплатно' : index % 3 === 1 ? 'Базовый' : 'Премиум' }}
              </span>
            </div>
            <div class="mt-2 flex flex-wrap gap-1">
              <span 
                v-for="(genre, i) in genres.slice(0, 4)" 
                :key="i"
                class="text-xs px-2 py-1 rounded"
                :class="`bg-${genre.color}-500`"
              >
                {{ genre.name }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style>
/* Плавные анимации */
.transition {
  transition: all 0.3s ease;
}



</style>