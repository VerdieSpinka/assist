import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import {
  AuthStatus,
  getAuthStatus,
  loginUser,
  registerUser,
  saveAuthData,
  logoutUser,
  UserInfo,
  RegisterPayload,
  ApiError,
} from '../api/auth'
import { useRefreshModels } from './configs'
import { updateJaazApiKey, clearJaazApiKey } from '../api/config'

interface AuthContextType {
  authStatus: AuthStatus
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation()
  const [authStatus, setAuthStatus] = useState<AuthStatus>({ status: 'logged_out' })
  const [isLoading, setIsLoading] = useState(true)
  const refreshModels = useRefreshModels()

  const refreshAuth = useCallback(async () => {
    setIsLoading(true)
    try {
      const status = await getAuthStatus()
      if (status.tokenExpired) {
        toast.error(t('common:auth.authExpiredMessage'))
      }
      setAuthStatus(status)
    } catch (error) {
      console.error('Gagal menyegarkan status autentikasi:', error)
      setAuthStatus({ status: 'logged_out' })
    } finally {
      setIsLoading(false)
    }
  }, [t])

  useEffect(() => {
    refreshAuth()
  }, [refreshAuth])

  const handleLoginSuccess = async (token: string, userInfo: UserInfo) => {
    saveAuthData(token, userInfo)
    setAuthStatus({ status: 'logged_in', user_info: userInfo })
    await updateJaazApiKey(token)
    refreshModels()
    toast.success(t('common:auth.loginSuccessMessage'))
  }

  const login = async (username: string, password: string) => {
    const { access_token, user_info } = await loginUser(username, password)
    await handleLoginSuccess(access_token, user_info)
  }

  const register = async (payload: RegisterPayload) => {
    await registerUser(payload)
    // Otomatis login setelah registrasi berhasil
    const { access_token, user_info } = await loginUser(
      payload.username,
      payload.password
    )
    await handleLoginSuccess(access_token, user_info)
  }

  const logout = async () => {
    logoutUser()
    setAuthStatus({ status: 'logged_out' })
    await clearJaazApiKey()
    refreshModels()
    toast.success(t('common:auth.logoutSuccessMessage'))
  }

  return (
    <AuthContext.Provider
      value={{ authStatus, isLoading, login, register, logout, refreshAuth }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}