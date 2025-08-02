<template>
  <div class="space-y-6">
    <!-- Header with Date Navigation -->
    <div class="bg-white rounded-lg shadow p-4">
      <!-- Single-row compact header -->
      <div class="flex flex-nowrap items-center gap-2 text-sm">
        <!-- Date navigation -->
        <button @click="previousDay" class="btn-secondary px-2 py-1" :disabled="loading">«</button>

        <input
          type="text"
          v-model="displayDate"
          placeholder="dd/mm/yyyy"
          class="input-field text-center w-28"
          :disabled="loading"
          @keyup.enter="onDisplayDateEnter"
          @blur="onDisplayDateEnter"
        />

        <button @click="nextDay" class="btn-secondary px-2 py-1" :disabled="loading">»</button>

        <button @click="goToToday" class="btn-secondary px-2 py-1" :disabled="loading">Today</button>

        <!-- View toggle -->
        <button
          :class="viewMode==='pending' ? 'btn-primary px-2 py-1' : 'btn-secondary px-2 py-1'"
          @click="setView('pending')"
          :disabled="loading"
        >Pending</button>
        <button
          :class="viewMode==='processed' ? 'btn-primary px-2 py-1' : 'btn-secondary px-2 py-1'"
          @click="setView('processed')"
          :disabled="loading"
        >Processed</button>

        <!-- Update: fetch then process -->
        <button @click="updateData" class="btn-secondary px-3 py-1" :disabled="loading">
          {{ loading ? 'Updating…' : 'Update Day' }}
        </button>
      </div>
      
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-blue-50 p-4 rounded-lg">
          <div class="text-sm font-medium text-blue-600">Pending</div>
          <div class="text-2xl font-bold text-blue-900">
            {{ pendingEntries.length }}
          </div>
          <div class="text-sm text-blue-700">
            {{ formatTimeWithMinutes(totalPendingTime) }} units
          </div>
        </div>
        
        <div class="bg-green-50 p-4 rounded-lg">
          <div class="text-sm font-medium text-green-600">Submitted</div>
          <div class="text-2xl font-bold text-green-900">
            {{ submittedEntries.length }}
          </div>
          <div class="text-sm text-green-700">
            {{ formatTimeWithMinutes(totalSubmittedTime) }} units
          </div>
        </div>
        
        <div class="bg-gray-50 p-4 rounded-lg">
          <div class="text-sm font-medium text-gray-600">Ignored</div>
          <div class="text-2xl font-bold text-gray-900">
            {{ ignoredEntries.length }}
          </div>
        </div>
        
        <div class="bg-purple-50 p-4 rounded-lg">
          <div class="text-sm font-medium text-purple-600">Total Time</div>
          <div class="text-2xl font-bold text-purple-900">
            {{ formatTimeWithMinutes(totalPendingTime + totalSubmittedTime) }}
          </div>
          <div class="text-sm text-purple-700">units tracked</div>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex">
        <div class="text-red-400">⚠️</div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error</h3>
          <div class="mt-2 text-sm text-red-700">{{ error }}</div>
          <div class="mt-4">
            <button @click="clearError" class="btn-danger text-sm">
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !displayedEntries.length" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
      <p class="mt-4 text-gray-500">Loading time entries...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!displayedEntries.length && !loading" class="text-center py-12">
      <div class="text-gray-400 text-6xl mb-4">📅</div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No time entries found</h3>
      <p class="text-gray-500 mb-6">
        No time entries exist for {{ displayDate }}. Use the "Update Day" button above to fetch and process data.
      </p>
    </div>

    <!-- Time Entries Table -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">Time Entries</h3>
      </div>
      
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Application
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Task Description
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Matter Code
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="entry in displayedEntries" :key="entry.entry_id" class="table-row">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ entry.application }}
              </td>
              <td class="px-6 py-4 text-sm text-gray-900">
                <div v-if="!entry.isEditing" class="max-w-xs truncate">{{ entry.task_description }}</div>
                <input v-else v-model="entry.edit_task_description" type="text" class="input-field w-full" />
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <span v-if="!entry.isEditing">{{ formatTimeWithMinutes(entry.time_units) }}</span>
                <input v-else v-model.number="entry.edit_time_units" type="number" step="0.1" min="0.1" class="input-field w-20" />
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <span v-if="!entry.isEditing">{{ entry.matter_code || '-' }}</span>
                <input v-else v-model="entry.edit_matter_code" type="text" class="input-field w-24" />
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getStatusClass(entry.status)">
                  {{ entry.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                <template v-if="entry.status === 'pending' && viewMode==='pending'">
                  <button v-if="!entry.isEditing" @click="startEdit(entry)" class="text-blue-600 hover:text-blue-900">Edit</button>
                  <button v-if="entry.isEditing" @click="cancelEdit(entry)" class="text-gray-500 hover:text-gray-700">Cancel</button>

                  <button 
                    v-if="!entry.isEditing"
                    @click="confirmEntry(entry)"
                    class="text-green-600 hover:text-green-900"
                  >
                    Confirm
                  </button>
                  <button v-if="entry.isEditing" @click="saveAndConfirm(entry)" class="text-green-600 hover:text-green-900">Save & Confirm</button>

                  <button 
                    v-if="!entry.isEditing"
                    @click="ignoreEntry(entry)"
                    class="text-red-600 hover:text-red-900"
                  >
                    Ignore
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useTimeEntriesStore } from '../stores/timeEntries.js'
import { formatDateAU, parseAUDate, formatTimeWithMinutes, getToday, addDays, subtractDays } from '../utils/dateUtils.js'
import { storeToRefs } from 'pinia'

const store = useTimeEntriesStore()

const {
  timeEntries,
  processedEntries,
  currentDate,
  loading,
  error,
  pendingEntries,
  submittedEntries,
  ignoredEntries,
  totalPendingTime,
  totalSubmittedTime
} = storeToRefs(store)

const viewMode = ref('pending') // 'pending' | 'processed'

const displayedEntries = computed(() => {
  return viewMode.value === 'pending' ? pendingEntries.value : submittedEntries.value
})

const displayDate = ref(formatDateAU(currentDate.value))

watch(currentDate, (newVal)=>{
  displayDate.value = formatDateAU(newVal)
})

function setView(mode) {
  if (viewMode.value === mode) return
  viewMode.value = mode
  fetchData()
}

// Methods
function startEdit(entry) {
  // Ensure editable copies are populated each time edit starts
  entry.edit_task_description = entry.task_description
  entry.edit_time_units = entry.time_units
  entry.edit_matter_code = entry.matter_code
  entry.isEditing = true
}

function previousDay() {
  const newDate = subtractDays(currentDate.value, 1)
  store.setCurrentDate(newDate)
}

function nextDay() {
  const newDate = addDays(currentDate.value, 1)
  store.setCurrentDate(newDate)
}

function goToToday() {
  store.setCurrentDate(getToday())
}

function onDisplayDateEnter(){
  const iso=parseAUDate(displayDate.value)
  if(!iso){
    alert('Please enter date as DD/MM/YYYY')
    displayDate.value=formatDateAU(currentDate.value)
    return
  }
  store.setCurrentDate(iso)
}

async function fetchData() {
  if (viewMode.value === 'pending') {
    await store.fetchTimeEntries(currentDate.value)
  } else {
    await store.fetchProcessedTimeEntries(currentDate.value)
  }
}

async function updateData() {
  await store.fetchRescueTimeData(4, currentDate.value)
  await store.processRescueTimeData(currentDate.value)
  await fetchData()
}

async function saveAndConfirm(entry) {
  const editedData = {
    task_description: entry.edit_task_description,
    time_units: entry.edit_time_units,
    matter_code: entry.edit_matter_code,
    notes: entry.notes || ''
  }
  await confirmEntry(entry, editedData)
  entry.isEditing = false
}

function cancelEdit(entry) {
  entry.isEditing = false
}

async function confirmEntry(entry, editedDataOverride = null) {
  try {
    const dataToSend = editedDataOverride || {
      task_description: entry.task_description,
      time_units: entry.time_units,
      matter_code: entry.matter_code,
      notes: ''
    }
    await store.confirmTimeEntry(entry.entry_id, dataToSend)
  } catch (err) {
    // Error handled by store
  }
}

async function ignoreEntry(entry) {
  try {
    await store.ignoreTimeEntry(entry.entry_id)
  } catch (err) {
    // Error handled by store
  }
}

function getStatusClass(status) {
  switch (status) {
    case 'pending': return 'status-pending'
    case 'submitted': return 'status-submitted'
    case 'ignored': return 'status-ignored'
    default: return 'status-pending'
  }
}

function clearError() {
  store.clearError()
}

// Watchers
watch(currentDate, () => {
  fetchData()
})

// Add initialisation when entries are loaded
watch(() => store.timeEntries.value, (newEntries) => {
  newEntries.forEach((e) => {
    if (e.isEditing === undefined) {
      e.isEditing = false
      e.edit_task_description = e.task_description
      e.edit_time_units = e.time_units
      e.edit_matter_code = e.matter_code
    }
  })
})

// Lifecycle
onMounted(() => {
  fetchData()
})
</script> 