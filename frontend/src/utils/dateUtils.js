// Date utility functions
export function formatDate(date) {
  if (typeof date === 'string') {
    date = new Date(date)
  }
  return date.toISOString().split('T')[0] // YYYY-MM-DD format
}

export function formatDisplayDate(dateString) {
  const date = new Date(dateString + 'T00:00:00') // Avoid timezone issues
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

export function formatTime(timeUnits) {
  if (!timeUnits || timeUnits === 0) return '0.0'
  return parseFloat(timeUnits).toFixed(1)
}

export function formatTimeWithMinutes(timeUnits) {
  if (!timeUnits || timeUnits === 0) return '0.0 units (0 min)'
  const minutes = Math.round(timeUnits * 6)
  return `${parseFloat(timeUnits).toFixed(1)} units (${minutes} min)`
}

export function getToday() {
  return formatDate(new Date())
}

export function getYesterday() {
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return formatDate(yesterday)
}

export function addDays(dateString, days) {
  const date = new Date(dateString + 'T00:00:00')
  date.setDate(date.getDate() + days)
  return formatDate(date)
}

export function subtractDays(dateString, days) {
  return addDays(dateString, -days)
}

export function isValidDate(dateString) {
  const regex = /^\d{4}-\d{2}-\d{2}$/
  if (!regex.test(dateString)) return false
  
  const date = new Date(dateString + 'T00:00:00')
  return date instanceof Date && !isNaN(date)
} 