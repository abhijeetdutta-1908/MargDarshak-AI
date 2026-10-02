import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { auth, tokenStore } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!tokenStore.get())

  useEffect(() => {
    if (!tokenStore.get()) return
    auth
      .me()
      .then(setUser)
      .catch((e) => {
        if (e.response?.status === 401) tokenStore.clear()
      })
      .finally(() => setLoading(false))
  }, [])

  const acceptSession = useCallback(({ access_token, user }) => {
    tokenStore.set(access_token)
    setUser(user)
  }, [])

  const login = useCallback(async (body) => acceptSession(await auth.login(body)), [acceptSession])
  const register = useCallback(async (body) => acceptSession(await auth.register(body)), [acceptSession])

  const logout = useCallback(async () => {
    try {
      await auth.logout()
    } finally {
      tokenStore.clear()
      setUser(null)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, register, logout, acceptSession }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
