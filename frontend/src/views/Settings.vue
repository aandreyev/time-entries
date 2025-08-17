<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-4xl mx-auto px-4">
      <div class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-gray-200">
          <h1 class="text-2xl font-bold text-gray-900">Settings</h1>
          <p class="text-gray-600 mt-1">Configure your RescueTime Time-Entry Assistant</p>
        </div>

        <div class="p-6">
          <!-- Loading indicator -->
          <div v-if="loading" class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="mt-2 text-gray-600">Loading configuration...</p>
          </div>

          <!-- Content when loaded -->
          <div v-else class="space-y-8">
            <!-- Debug info -->
            <div class="bg-gray-100 p-4 rounded-lg">
              <h3 class="font-medium mb-2">Debug Info:</h3>
              <pre class="text-xs text-gray-700">{{ JSON.stringify(settings, null, 2) }}</pre>
            </div>

            <!-- API Key Section -->
            <div class="space-y-4">
              <div class="flex items-center space-x-2">
                <h2 class="text-lg font-semibold text-gray-900">RescueTime API Key</h2>
                <span v-if="settings.has_api_key" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✓ Configured
                </span>
                <span v-else class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  ⚠ Required
                </span>
              </div>
              
              <div v-if="settings.has_api_key" class="p-3 bg-gray-50 rounded-md">
                <p class="text-sm text-gray-700">
                  Current API key: <code class="bg-gray-200 px-2 py-1 rounded text-sm">{{ settings.api_key_preview }}</code>
                </p>
              </div>

              <div class="flex space-x-3">
                <input
                  v-model="newApiKey"
                  type="password"
                  placeholder="Enter your RescueTime API key"
                  class="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  @click="updateApiKey"
                  :disabled="!newApiKey.trim() || updating"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {{ updating ? 'Updating...' : 'Update' }}
                </button>
              </div>
            </div>

            <!-- Database Section -->
            <div class="space-y-4">
              <h2 class="text-lg font-semibold text-gray-900">Database Path</h2>
              <div class="p-3 bg-gray-50 rounded-md">
                <p class="text-sm text-gray-700 mb-2">Current database path:</p>
                <code class="bg-gray-200 px-2 py-1 rounded text-sm break-all">{{ settings.database_path }}</code>
              </div>

              <div class="flex space-x-3">
                <input
                  v-model="newDatabasePath"
                  type="text"
                  placeholder="Enter full path to database file"
                  class="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  @click="updateDatabasePath"
                  :disabled="!newDatabasePath.trim() || updatingDbPath"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {{ updatingDbPath ? 'Updating...' : 'Update' }}
                </button>
              </div>
            </div>

            <!-- Messages -->
            <div v-if="apiKeyMessage" :class="[
              'p-3 rounded-md text-sm',
              apiKeyMessage.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
            ]">
              {{ apiKeyMessage.text }}
            </div>

            <div v-if="databaseMessage" :class="[
              'p-3 rounded-md text-sm',
              databaseMessage.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
            ]">
              {{ databaseMessage.text }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../utils/api.js'

export default {
  name: 'Settings',
  data() {
    return {
      settings: {
        has_api_key: false,
        api_key_preview: '',
        database_path: '',
        database_info: {
          path: '',
          exists: false,
          readable: false,
          writable: false,
          size_mb: 0,
          connection_test: false,
          tables_exist: false,
          record_counts: {},
          error: null
        },
        first_run: true,
  backend_port: 8765
      },
      newApiKey: '',
      newDatabasePath: '',
      loading: true,
      updating: false,
      updatingDbPath: false,
      testing: false,
      initializing: false,
      apiKeyMessage: null,
      databaseMessage: null,
      testMessage: null
    }
  },
  async mounted() {
    console.log('Settings component mounted, loading settings...')
    await this.loadSettings()
  },
  methods: {
    async loadSettings() {
      try {
        console.log('Loading settings from API...')
        this.loading = true
        this.settings = await apiClient.getSettings()
        console.log('Settings loaded:', this.settings)
      } catch (error) {
        console.error('Failed to load settings:', error)
        // Keep default values if loading fails
      } finally {
        this.loading = false
      }
    },
    async updateApiKey() {
      if (!this.newApiKey.trim()) return
      
      this.updating = true
      this.apiKeyMessage = null
      
      try {
        await apiClient.updateApiKey(this.newApiKey.trim())
        this.apiKeyMessage = {
          type: 'success',
          text: 'API key updated successfully!'
        }
        this.newApiKey = ''
        await this.loadSettings()
      } catch (error) {
        this.apiKeyMessage = {
          type: 'error',
          text: `Failed to update API key: ${error.message}`
        }
      } finally {
        this.updating = false
      }
    },
    async updateDatabasePath() {
      if (!this.newDatabasePath.trim()) return
      
      this.updatingDbPath = true
      this.databaseMessage = null
      
      try {
        await apiClient.updateDatabasePath(this.newDatabasePath.trim())
        this.databaseMessage = {
          type: 'success',
          text: 'Database path updated successfully! The changes are now active.'
        }
        this.newDatabasePath = ''
        // Reload settings to show the updated path and test the new database
        await this.loadSettings()
      } catch (error) {
        this.databaseMessage = {
          type: 'error',
          text: `Failed to update database path: ${error.message}`
        }
      } finally {
        this.updatingDbPath = false
      }
    },
    async testDatabase() {
      this.testing = true
      this.testMessage = null
      
      try {
        const result = await apiClient.testDatabase()
        if (result.status === 'success') {
          this.testMessage = {
            type: 'success',
            text: 'Database test completed successfully! Check the status details above.'
          }
        } else {
          this.testMessage = {
            type: 'error',
            text: 'Database test found issues. Check the status details above for more information.'
          }
        }
        // Refresh settings to get updated database info
        await this.loadSettings()
      } catch (error) {
        this.testMessage = {
          type: 'error',
          text: `Database test failed: ${error.message}`
        }
      } finally {
        this.testing = false
      }
    },
    async initializeDatabase() {
      this.initializing = true
      this.testMessage = null
      
      try {
        await apiClient.initializeDatabase()
        this.testMessage = {
          type: 'success',
          text: 'Database initialized successfully!'
        }
        // Refresh settings to get updated database info
        await this.loadSettings()
      } catch (error) {
        this.testMessage = {
          type: 'error',
          text: `Failed to initialize database: ${error.message}`
        }
      } finally {
        this.initializing = false
      }
    },
    async testConnection() {
      // TODO: Implement API connection test
      alert('API connection test - to be implemented')
    },
    async initDatabase() {
      // Redirect to the new initialize function
      await this.initializeDatabase()
    }
  }
}
</script>
