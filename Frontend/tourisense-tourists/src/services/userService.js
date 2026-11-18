import api from './api.js'; export const getProfile=()=>api.get('/users/me'); export const updateProfile=(data)=>api.patch('/users/me',data)
