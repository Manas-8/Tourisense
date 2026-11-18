import api from './api.js'

export const createTrip = (payload) => api.post('/trips', payload)
export const getTrips = () => api.get('/trips')
export const getTripById = (id) => api.get(`/trips/${id}`)
export const updateTrip = (id, payload) => api.put(`/trips/${id}`, payload)
export const deleteTrip = (id) => api.delete(`/trips/${id}`)
export const saveTrip = (payload) => api.post('/trips', payload)

// New function for handling real-time photo check-ins
export const checkInActivity = (formData) => api.post('/trips/checkin', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})