import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        setLoading(false)
        return
      }
      try {
        const response = await api.get('/me')
        setUser(response.data)
        localStorage.setItem('user', JSON.stringify(response.data))
      } catch (err) {
        // Only clear on actual auth failure, not network errors
        if (err.response?.status === 401) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          setUser(null)
        }
      } finally {
        setLoading(false)
      }
    }

    // Handle GitHub OAuth redirect
    const params = new URLSearchParams(window.location.search)
    const githubToken = params.get('access_token')
    if (githubToken) {
      localStorage.setItem('access_token', githubToken)
      window.history.replaceState({}, '', '/')
      // credentials: 'include' so the refresh cookie gets stored
      fetch(`${import.meta.env.VITE_API_URL}/me`, {
        headers: { Authorization: `Bearer ${githubToken}` },
        credentials: 'include',
      })
        .then(r => r.json())
        .then(userData => {
          setUser(userData)
          localStorage.setItem('user', JSON.stringify(userData))
          setLoading(false)
        })
        .catch(() => setLoading(false))
    } else {
      initAuth()
    }
  }, [])

  const login = (userData, accessToken) => {
    // No refresh token param — cookie is handled by the browser
    setUser(userData)
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const logout = async () => {
    try {
      // Cookie is sent automatically, backend clears it
      await api.post('/auth/logout')
    } catch (err) {
      console.error('Logout error', err)
    }
    setUser(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)