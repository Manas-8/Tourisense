import { createContext, useContext, useEffect, useState } from 'react'
import * as authService from '../services/authService.js'
const AuthContext=createContext(null)
export function AuthProvider({children}){const [user,setUser]=useState(null);const [loading,setLoading]=useState(true);useEffect(()=>{const stored=authService.getCurrentUser();if(!stored){setLoading(false);return}authService.refreshCurrentUser().then(setUser).catch(()=>authService.logout()).finally(()=>setLoading(false))},[]);const login=async(data)=>{const next=await authService.login(data);setUser(next);return next};const register=async(data)=>{const next=await authService.register(data);setUser(next);return next};const logout=()=>{authService.logout();setUser(null)};return <AuthContext.Provider value={{user,loading,login,register,logout}}>{children}</AuthContext.Provider>}
export const useAuth=()=>useContext(AuthContext)
