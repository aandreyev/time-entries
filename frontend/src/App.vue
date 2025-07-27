<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <h1 class="text-2xl font-bold text-gray-900">
            RescueTime Time Entry Assistant
          </h1>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">
              Connected to API
            </span>
            <div class="w-2 h-2 bg-success-500 rounded-full"></div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <TimeEntries />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <p class="text-center text-sm text-gray-500">
          RescueTime Time Entry Assistant - Built with Vue.js
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import TimeEntries from './views/TimeEntries.vue'
</script> 