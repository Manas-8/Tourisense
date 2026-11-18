import api from './api.js'
export const getDestinations=(params)=>api.get('/destinations',{params})
export const getDestinationById=(id)=>api.get(`/destinations/${id}`)
