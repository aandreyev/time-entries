// Form validation utilities

export function validateTimeUnits(value) {
  const num = parseFloat(value)
  
  if (isNaN(num)) {
    return { valid: false, message: 'Must be a valid number' }
  }
  
  if (num < 0.1) {
    return { valid: false, message: 'Minimum value is 0.1 units (6 minutes)' }
  }
  
  if (num > 24) {
    return { valid: false, message: 'Maximum value is 24 units (24 hours)' }
  }
  
  // Round to nearest 0.1
  const rounded = Math.round(num * 10) / 10
  if (rounded !== num) {
    return { 
      valid: true, 
      corrected: rounded,
      message: `Rounded to ${rounded} units`
    }
  }
  
  return { valid: true }
}

export function validateMatterCode(value) {
  if (!value || value.trim() === '') {
    return { valid: true } // Optional field
  }
  
  const code = value.trim()
  const regex = /^\d{5}$/
  
  if (!regex.test(code)) {
    return { 
      valid: false, 
      message: 'Matter code must be exactly 5 digits' 
    }
  }
  
  return { valid: true }
}

export function validateTaskDescription(value) {
  if (!value || value.trim() === '') {
    return { 
      valid: false, 
      message: 'Task description is required' 
    }
  }
  
  const trimmed = value.trim()
  
  if (trimmed.length < 3) {
    return { 
      valid: false, 
      message: 'Task description must be at least 3 characters' 
    }
  }
  
  if (trimmed.length > 200) {
    return { 
      valid: false, 
      message: 'Task description must be less than 200 characters' 
    }
  }
  
  return { valid: true }
}

export function validateNotes(value) {
  if (!value) {
    return { valid: true } // Optional field
  }
  
  if (value.length > 500) {
    return { 
      valid: false, 
      message: 'Notes must be less than 500 characters' 
    }
  }
  
  return { valid: true }
}

// Validate entire time entry
export function validateTimeEntry(entry) {
  const errors = {}
  
  const taskResult = validateTaskDescription(entry.task_description)
  if (!taskResult.valid) {
    errors.task_description = taskResult.message
  }
  
  const timeResult = validateTimeUnits(entry.time_units)
  if (!timeResult.valid) {
    errors.time_units = timeResult.message
  }
  
  const matterResult = validateMatterCode(entry.matter_code)
  if (!matterResult.valid) {
    errors.matter_code = matterResult.message
  }
  
  const notesResult = validateNotes(entry.notes)
  if (!notesResult.valid) {
    errors.notes = notesResult.message
  }
  
  return {
    valid: Object.keys(errors).length === 0,
    errors
  }
} 