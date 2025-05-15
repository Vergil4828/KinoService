<script>

// Компоненты
import AppHeader from './components/AppHeader.vue';
import { RouterView } from 'vue-router'
import AppFooter from './components/AppFooter.vue';


export default {
	components: {
		AppHeader,
		RouterView,
		AppFooter
	}
};


</script>

<template>
	<div class="app">
		<!-- Шапка -->
		<app-header v-if="!$route.meta.hideHeaderFooter"></app-header>

		<!-- Меняющаяся часть -->
		<notifications position="top right"/>
		<router-view></router-view>
		<app-footer v-if="!$route.meta.hideHeaderFooter"></app-footer>
	</div>
</template>

<style>
html {
  scroll-behavior: smooth;
}


:root {
  scrollbar-color: #4fd1c5 #1a202c;
  scrollbar-width: thin;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #1a202c;
}

::-webkit-scrollbar-thumb {
  background: #4fd1c5;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #38b2ac;
}
</style>
