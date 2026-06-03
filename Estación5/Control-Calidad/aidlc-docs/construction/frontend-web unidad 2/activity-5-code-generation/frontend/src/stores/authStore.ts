/**
 * Auth Store — Zustand
 * Manages user state, authentication, tokens, and role-based access
 */

import { create } from 'zustand'
import { User, AuthResponse, Role, LoginRequest } from '../types'

export interface AuthState {
  // State
  user: User | null
  access_token: string | null
  refresh_token: string | null
  is_authenticated: boolean
  is_loading: boolean
  error: string | null

  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  setUser: (user: User) => void
  setAccessToken: (token: string) => void
  clearError: () => void
  resetAuth: () => void

  // Selectors
  canCreateInspection: () => boolean
  canApproveInspection: () => boolean
  canManageMasters: () => boolean
  canViewDashboard: () => boolean
  hasRole: (role: Role | Role[]) => boolean
  hasPermission: (action: string) => boolean
}

const INITIAL_STATE = {
  user: null,
  access_token: null,
  refresh_token: null,
  is_authenticated: false,
  is_loading: false,
  error: null,
}

export const useAuthStore = create<AuthState>((set, get) => ({
  ...INITIAL_STATE,

  login: async (email: string, password: string) => {
    set({ is_loading: true, error: null })
    try {
      const response = await fetch('https://api.company.local/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        throw new Error('Invalid email or password')
      }

      const data: AuthResponse = await response.json()

      set({
        user: data.user,
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        is_authenticated: true,
        is_loading: false,
      })

      // Store tokens in httpOnly cookies (set by backend)
      // accessToken also stored in memory for immediate access
      localStorage.setItem('user-email', data.user.email)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Authentication failed'
      set({
        error: message,
        is_loading: false,
      })
      throw err
    }
  },

  logout: async () => {
    set({ is_loading: true })
    try {
      const token = get().access_token
      if (token) {
        await fetch('https://api.company.local/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      }

      set(INITIAL_STATE)
      localStorage.removeItem('user-email')
    } catch (err) {
      console.error('Logout error:', err)
      set(INITIAL_STATE)
    }
  },

  refreshToken: async () => {
    try {
      const refresh_token = get().refresh_token
      if (!refresh_token) {
        throw new Error('No refresh token available')
      }

      const response = await fetch('https://api.company.local/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token }),
      })

      if (!response.ok) {
        // Refresh failed, logout
        set(INITIAL_STATE)
        throw new Error('Token refresh failed')
      }

      const data = await response.json()
      set({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      })
    } catch (err) {
      console.error('Token refresh error:', err)
      set(INITIAL_STATE)
      throw err
    }
  },

  setUser: (user: User) => {
    set({ user })
  },

  setAccessToken: (access_token: string) => {
    set({ access_token })
  },

  clearError: () => {
    set({ error: null })
  },

  resetAuth: () => {
    set(INITIAL_STATE)
  },

  // Selectors (RBAC)
  canCreateInspection: () => {
    const { user } = get()
    if (!user) return false
    return [Role.OPERARIO, Role.SUPERVISOR, Role.ADMIN].includes(user.role)
  },

  canApproveInspection: () => {
    const { user } = get()
    if (!user) return false
    return [Role.SUPERVISOR, Role.JEFE_QA, Role.ADMIN].includes(user.role)
  },

  canManageMasters: () => {
    const { user } = get()
    if (!user) return false
    return [Role.ADMIN, Role.JEFE_QA].includes(user.role)
  },

  canViewDashboard: () => {
    const { user } = get()
    if (!user) return false
    return [Role.GERENTE, Role.ADMIN, Role.JEFE_QA].includes(user.role)
  },

  hasRole: (roles: Role | Role[]) => {
    const { user } = get()
    if (!user) return false
    const roleList = Array.isArray(roles) ? roles : [roles]
    return roleList.includes(user.role)
  },

  hasPermission: (action: string) => {
    const { user } = get()
    if (!user) return false

    const permissions: Record<Role, string[]> = {
      [Role.OPERARIO]: [
        'create_inspection',
        'view_own_inspections',
      ],
      [Role.SUPERVISOR]: [
        'create_inspection',
        'view_all_inspections',
        'approve_inspection',
        'reject_inspection',
      ],
      [Role.JEFE_QA]: [
        'create_inspection',
        'view_all_inspections',
        'approve_inspection',
        'reject_inspection',
        'create_masters',
        'update_masters',
      ],
      [Role.GERENTE]: [
        'view_dashboard',
        'view_analytics',
      ],
      [Role.ADMIN]: ['*'],
    }

    const userPermissions = permissions[user.role] || []
    return userPermissions.includes(action) || userPermissions.includes('*')
  },
}))

// Hook for component usage
export const useAuth = () => {
  const store = useAuthStore()
  return {
    user: store.user,
    is_authenticated: store.is_authenticated,
    is_loading: store.is_loading,
    error: store.error,
    login: store.login,
    logout: store.logout,
    canCreateInspection: store.canCreateInspection(),
    canApproveInspection: store.canApproveInspection(),
    canManageMasters: store.canManageMasters(),
    canViewDashboard: store.canViewDashboard(),
  }
}
