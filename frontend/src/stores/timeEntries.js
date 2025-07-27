import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '../utils/api.js'
import { getToday } from '../utils/dateUtils.js'

export const useTimeEntriesStore = defineStore('timeEntries', () => {
  // State
  const timeEntries = ref([])
  const processedEntries = ref([])
  const currentDate = ref(getToday())
  const loading = ref(false)
  const error = ref(null)
  const lastFetch = ref(null)

  // Getters
  const pendingEntries = computed(() => 
    timeEntries.value.filter(entry => entry.status === 'pending')
  )

  const submittedEntries = computed(() => 
    processedEntries.value.filter(entry => entry.status === 'submitted')
  )

  const ignoredEntries = computed(() => 
    timeEntries.value.filter(entry => entry.status === 'ignored')
  )

  const totalPendingTime = computed(() => 
    pendingEntries.value.reduce((total, entry) => total + (entry.time_units || 0), 0)
  )

  const totalSubmittedTime = computed(() => 
    submittedEntries.value.reduce((total, entry) => total + (entry.time_units || 0), 0)
  )

  // Actions
  async function fetchTimeEntries(date = currentDate.value) {
    loading.value = true
    error.value = null
    
    try {
      const [draftEntries, confirmedEntries] = await Promise.all([
        apiClient.getTimeEntries(date),
        apiClient.getProcessedTimeEntries(date)
      ])
      
      timeEntries.value = draftEntries || []
      processedEntries.value = confirmedEntries || []
      lastFetch.value = new Date()
      
    } catch (err) {
      error.value = `Failed to fetch time entries: ${err.message}`
      console.error('Fetch error:', err)
    } finally {
      loading.value = false
    }
  }

  async function confirmTimeEntry(entryId, editedData) {
    loading.value = true
    error.value = null
    
    try {
      const originalEntry = timeEntries.value.find(e => e.entry_id === entryId)
      if (!originalEntry) {
        throw new Error('Original entry not found')
      }

      const processedEntry = {
        original_entry_id: entryId,
        entry_date: currentDate.value,
        application: originalEntry.application,
        task_description: editedData.task_description || originalEntry.task_description,
        time_units: editedData.time_units || originalEntry.time_units,
        matter_code: editedData.matter_code || originalEntry.matter_code,
        notes: editedData.notes || '',
        status: 'submitted',
        source_hash: originalEntry.source_hash
      }

      const result = await apiClient.createProcessedTimeEntry(processedEntry)
      
      // Add to processed entries
      processedEntries.value.push(result)
      
      // Remove from pending entries or mark as processed
      const entryIndex = timeEntries.value.findIndex(e => e.entry_id === entryId)
      if (entryIndex >= 0) {
        timeEntries.value[entryIndex].status = 'submitted'
      }
      
    } catch (err) {
      error.value = `Failed to confirm entry: ${err.message}`
      console.error('Confirm error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function ignoreTimeEntry(entryId) {
    loading.value = true
    error.value = null
    
    try {
      await apiClient.ignoreTimeEntry(entryId)
      
      // Update local state
      const entryIndex = timeEntries.value.findIndex(e => e.entry_id === entryId)
      if (entryIndex >= 0) {
        timeEntries.value[entryIndex].status = 'ignored'
      }
      
    } catch (err) {
      error.value = `Failed to ignore entry: ${err.message}`
      console.error('Ignore error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchRescueTimeData(days = 1) {
    loading.value = true
    error.value = null
    
    try {
      await apiClient.fetchData(days)
      // Refresh current data after fetch
      await fetchTimeEntries(currentDate.value)
      
    } catch (err) {
      error.value = `Failed to fetch RescueTime data: ${err.message}`
      console.error('Fetch RescueTime error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function processRescueTimeData(date = currentDate.value) {
    loading.value = true
    error.value = null
    
    try {
      await apiClient.processData(date)
      // Refresh current data after processing
      await fetchTimeEntries(date)
      
    } catch (err) {
      error.value = `Failed to process data: ${err.message}`
      console.error('Process error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function setCurrentDate(date) {
    currentDate.value = date
  }

  function clearError() {
    error.value = null
  }

  // Return store interface
  return {
    // State
    timeEntries,
    processedEntries,
    currentDate,
    loading,
    error,
    lastFetch,
    
    // Getters
    pendingEntries,
    submittedEntries,
    ignoredEntries,
    totalPendingTime,
    totalSubmittedTime,
    
    // Actions
    fetchTimeEntries,
    confirmTimeEntry,
    ignoreTimeEntry,
    fetchRescueTimeData,
    processRescueTimeData,
    setCurrentDate,
    clearError
  }
}) 