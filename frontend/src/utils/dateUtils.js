// Date utility functions
function parseDate(dateStr) {
  // dateStr in YYYY-MM-DD
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d) // local time, midnight
}

export function formatDate(date) {
  // Always return YYYY-MM-DD
  if (typeof date === 'string') {
    date = parseDate(date)
  }
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function formatDisplayDate(dateString) {
  const date = parseDate(dateString)
  // Australian long format: e.g., Monday, 27 July 2025
  return date.toLocaleDateString('en-AU', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

export function formatTimeWithMinutes(timeUnits) {
  if (!timeUnits || timeUnits === 0) return '0.0 units (0 min)'
  const minutes = Math.round(timeUnits * 6)
  return `${parseFloat(timeUnits).toFixed(1)} units (${minutes} min)`
}

export function getToday() {
  return formatDate(new Date())
}

export function addDays(dateString, days) {
  const date = parseDate(dateString)
  date.setDate(date.getDate() + days)
  return formatDate(date)
}

export function subtractDays(dateString, days) {
  return addDays(dateString, -days)
}

export function isValidDate(dateString) {
  return /^\d{4}-\d{2}-\d{2}$/.test(dateString)
}

export function formatDateAU(dateString){
  const [y,m,d]=dateString.split('-');
  return `${d}/${m}/${y}`
}

export function parseAUDate(input){
  // expects DD/MM/YYYY returns YYYY-MM-DD or null
  const parts=input.split('/')
  if(parts.length!==3) return null
  const [d,m,y]=parts
  if(d.length!==2||m.length!==2||y.length!==4) return null
  return `${y}-${m}-${d}`
} 