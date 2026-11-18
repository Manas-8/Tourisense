import api from './api.js'

const TOKEN_KEY = 'tourisense-token'
const USER_KEY = 'tourisense-user'
const LEGACY_TOKEN_KEY = 'wanderly-token'
const LEGACY_USER_KEY = 'wanderly-user'

function getApiErrorMessage(error, fallback){
  return error?.response?.data?.error || error?.response?.data?.message || error?.message || fallback
}

function persistSession({token,user}){
  if(token) localStorage.setItem(TOKEN_KEY,token)
  localStorage.setItem(USER_KEY,JSON.stringify(user))
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  localStorage.removeItem(LEGACY_USER_KEY)
}

function readStoredUser(){
  const raw = localStorage.getItem(USER_KEY) || localStorage.getItem(LEGACY_USER_KEY)
  if(!raw) return null
  try {
    const user = JSON.parse(raw)
    if(localStorage.getItem(LEGACY_USER_KEY) && !localStorage.getItem(USER_KEY)) {
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      localStorage.removeItem(LEGACY_USER_KEY)
    }
    return user
  } catch {
    return null
  }
}

export async function login(credentials){
  const payload = { email: credentials.email, password: credentials.password }
  const {data}=await api.post('/auth/login',payload)
  persistSession({token:data.token,user:data.user})
  return data.user
}

export async function register(data){
  const payload = { name: data.name, email: data.email, password: data.password }
  const {data:response}=await api.post('/auth/register',payload)
  persistSession({token:response.token,user:response.user})
  return response.user
}

export async function refreshCurrentUser(){
  const {data:user}=await api.get('/users/me')
  localStorage.setItem(USER_KEY,JSON.stringify(user))
  return user
}

export function logout(){
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  localStorage.removeItem(LEGACY_USER_KEY)
}

export function getCurrentUser(){return readStoredUser()}
export function getAccessToken(){return localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY)}
export function buildGovernmentHandoffUrl(baseUrl, token){
  if(!token) throw new Error('An authenticated session token is required.')
  const target=new URL(baseUrl)
  target.pathname=`${target.pathname.replace(/\/$/,'')}/government/dashboard`
  target.hash=new URLSearchParams({session:token}).toString()
  return target.toString()
}
export function getAuthErrorMessage(error, fallback){return getApiErrorMessage(error, fallback)}
