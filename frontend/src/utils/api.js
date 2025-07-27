// API client for RescueTime backend
const API_BASE = '/api'

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Time Entries
  async getTimeEntries(date) {
    return this.request(`/time_entries?date=${date}`)
  }

  async getProcessedTimeEntries(date) {
    return this.request(`/processed_time_entries?date=${date}`)
  }

  async createProcessedTimeEntry(entryData) {
    return this.request('/processed_time_entries', {
      method: 'POST',
      body: JSON.stringify(entryData),
    })
  }

  async ignoreTimeEntry(entryId) {
    return this.request(`/time_entries/${entryId}/ignore`, {
      method: 'PUT',
    })
  }

  // Jobs
  async fetchData(days = 1) {
    return this.request('/jobs/fetch', {
      method: 'POST',
      body: JSON.stringify({ days }),
    })
  }

  async processData(date) {
    return this.request('/jobs/process', {
      method: 'POST',
      body: JSON.stringify({ date }),
    })
  }

  // ALP Integration (future)
  async getAlpMatters() {
    return this.request('/alp/matters')
  }

  async submitToAlp(processedEntries) {
    return this.request('/time_entries', {
      method: 'POST',
      body: JSON.stringify(processedEntries),
    })
  }
}

export const apiClient = new ApiClient()
export default apiClient 