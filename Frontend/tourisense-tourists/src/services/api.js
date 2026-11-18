import axios from 'axios'

const env = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env : {}
const TOKEN_KEY = 'tourisense-token'
const LEGACY_TOKEN_KEY = 'wanderly-token'

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY)

const api=axios.create({baseURL:env.VITE_API_BASE_URL||'http://127.0.0.1:5000/api',headers:{'Content-Type':'application/json'}})
api.interceptors.request.use(config=>{const token=getStoredToken();if(token) config.headers.Authorization=`Bearer ${token}`;return config})
export default api
