import React, { createContext, useContext, useEffect, useState } from 'react'
import { api } from './http'

type User = {
  email: string
  name: string
  role: 'merchant' | 'admin' | 'user'
  access: string
  api_key?: string | null
}

type AuthContextType = {
  user: User | null
  login: (email: string, password: string) =>  Promise<any>
  register: (name: string, email: string, password: string, webhook_url?: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('paygate_user')
    if (!stored) return null
    try {
      const parsed: User = JSON.parse(stored)
      return parsed
    } catch {
      return null
    }
  })

  // Ensure API client has token after hydration
  useEffect(() => {
    if (user?.access) api.setAccessToken(user.access)
  }, [])

  // Sync user to localStorage
  useEffect(() => {
    if (user) localStorage.setItem('paygate_user', JSON.stringify(user))
    else localStorage.removeItem('paygate_user')
  }, [user])

async function login(email: string, password: string) {
  try {
    const res = await api.post('/paygate/api/v1/auth/token/', { email, password }, { withCredentials: true })
    // Handle success case based on your JSON structure
    if (res.data?.success === true && res.data?.data) {
      const u: User = {
        email: res.data.data.email,
        name: res.data.data.name,
        role: res.data.data.role,
        access: res.data.data.access,
        api_key: res.data.data.api_key ?? null,
      }

      // Set token & user
      api.setAccessToken(u.access)
      setUser(u)

      // Optional: store in localStorage
      localStorage.setItem('user', JSON.stringify(u))
      localStorage.setItem('access_token', u.access)

      return {
        success: true,
        message: res.data.message || 'Login successful',
        data: res.data.data,
      }
    } else {
      // API returned success=false
      return {
        success: false,
        message: res.data?.exception?.message || 'Login failed',
        description: res.data?.exception?.description || null,
        code: res.data?.exception?.code || null,
      }
    }
  } catch (err: any) {
    // Handle thrown errors (network/server errors)
    const message =
      err?.response?.data?.message ||
      err?.response?.data?.exception?.message ||
      err?.message ||
      'Login failed. Please try again.'

    const description =
      err?.response?.data?.exception?.description ||
      err?.response?.data?.detail ||
      null

    return {
      success: false,
      message,
      description,
    }
  }
}


  async function register(name: string, email: string, password: string, webhook_url?: string) {
    const res = await api.post(
      '/paygate/api/v1/auth/register/',
      {
        user: { name, email, password },
        webhook_url: webhook_url ?? '',
      },
      { withCredentials: true }
    )
    const u: User = {
      email: res.data.email,
      name: res.data.name,
      role: 'merchant',
      access: res.data.access,
      api_key: res.data.api_key ?? null,
    }
    api.setAccessToken(u.access)
    setUser(u)
    return res.data
  }

  async function logout() {
    try {
      await api.post('/paygate/api/v1/auth/logout/', {}, { withCredentials: true })
    } catch {}
    setUser(null)
    api.setAccessToken(null)
    localStorage.removeItem('paygate_user')
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
