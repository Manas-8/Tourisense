import api from './api.js'; export const getRestaurants=(params)=>api.get('/restaurants',{params})
