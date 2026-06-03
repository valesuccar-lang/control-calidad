/**
 * Master Store — Zustand
 * Manages Defects, Machines, Fabrics (master data)
 */

import { create } from 'zustand'
import {
  Defect,
  Machine,
  Fabric,
  MastersCache,
  DefectCreate,
  MachineCreate,
  FabricCreate,
} from '../types'

export interface MasterState {
  // State
  defects: Defect[]
  machines: Machine[]
  fabrics: Fabric[]
  loading: boolean
  error: string | null
  last_updated: string | null
  cache_ttl_ms: number

  // Actions
  fetchAllMasters: () => Promise<void>
  fetchDefects: () => Promise<void>
  fetchMachines: () => Promise<void>
  fetchFabrics: () => Promise<void>

  // Defects
  createDefect: (data: DefectCreate) => Promise<Defect>
  updateDefect: (id: string, data: Partial<DefectCreate>) => Promise<Defect>
  inactivateDefect: (id: string) => Promise<void>

  // Machines
  createMachine: (data: MachineCreate) => Promise<Machine>
  updateMachine: (id: string, data: Partial<MachineCreate>) => Promise<Machine>
  inactivateMachine: (id: string) => Promise<void>

  // Fabrics
  createFabric: (data: FabricCreate) => Promise<Fabric>
  updateFabric: (id: string, data: Partial<FabricCreate>) => Promise<Fabric>
  inactivateFabric: (id: string) => Promise<void>

  // Cache management
  refreshCache: () => Promise<void>
  getCacheStatus: () => { is_expired: boolean; age_ms: number }
  clearError: () => void
}

const CACHE_TTL_MS = 60 * 60 * 1000 // 1 hour

export const useMasterStore = create<MasterState>((set, get) => ({
  defects: [],
  machines: [],
  fabrics: [],
  loading: false,
  error: null,
  last_updated: null,
  cache_ttl_ms: CACHE_TTL_MS,

  fetchAllMasters: async () => {
    const status = get().getCacheStatus()
    if (!status.is_expired) {
      // Cache is still valid
      return
    }

    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('access-token')
      const headers = {
        'Authorization': `Bearer ${token}`,
      }

      const [defectsRes, machinesRes, fabricsRes] = await Promise.all([
        fetch('https://api.company.local/api/masters/defects', { headers }),
        fetch('https://api.company.local/api/masters/machines', { headers }),
        fetch('https://api.company.local/api/masters/fabrics', { headers }),
      ])

      if (!defectsRes.ok || !machinesRes.ok || !fabricsRes.ok) {
        throw new Error('Failed to fetch masters')
      }

      const defects = await defectsRes.json()
      const machines = await machinesRes.json()
      const fabrics = await fabricsRes.json()

      set({
        defects,
        machines,
        fabrics,
        last_updated: new Date().toISOString(),
        loading: false,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Fetch failed'
      set({ error: message, loading: false })
    }
  },

  fetchDefects: async () => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch('https://api.company.local/api/masters/defects', {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (!response.ok) throw new Error('Failed to fetch defects')

      const defects = await response.json()
      set({ defects })
    } catch (err) {
      console.error('Defects fetch error:', err)
    }
  },

  fetchMachines: async () => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch('https://api.company.local/api/masters/machines', {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (!response.ok) throw new Error('Failed to fetch machines')

      const machines = await response.json()
      set({ machines })
    } catch (err) {
      console.error('Machines fetch error:', err)
    }
  },

  fetchFabrics: async () => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch('https://api.company.local/api/masters/fabrics', {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (!response.ok) throw new Error('Failed to fetch fabrics')

      const fabrics = await response.json()
      set({ fabrics })
    } catch (err) {
      console.error('Fabrics fetch error:', err)
    }
  },

  // Defects
  createDefect: async (data: DefectCreate) => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch('https://api.company.local/api/masters/defects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) throw new Error('Failed to create defect')

      const defect = await response.json()
      set((state) => ({
        defects: [...state.defects, defect],
      }))

      return defect
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Creation failed'
      set({ error: message })
      throw err
    }
  },

  updateDefect: async (id: string, data: Partial<DefectCreate>) => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch(`https://api.company.local/api/masters/defects/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) throw new Error('Failed to update defect')

      const updated = await response.json()
      set((state) => ({
        defects: state.defects.map((d) => (d.id === id ? updated : d)),
      }))

      return updated
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Update failed'
      set({ error: message })
      throw err
    }
  },

  inactivateDefect: async (id: string) => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch(`https://api.company.local/api/masters/defects/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) throw new Error('Failed to inactivate')

      set((state) => ({
        defects: state.defects.filter((d) => d.id !== id),
      }))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Inactivation failed'
      set({ error: message })
      throw err
    }
  },

  // Machines (similar implementation)
  createMachine: async (data: MachineCreate) => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch('https://api.company.local/api/masters/machines', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) throw new Error('Failed to create machine')

      const machine = await response.json()
      set((state) => ({
        machines: [...state.machines, machine],
      }))

      return machine
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Creation failed'
      set({ error: message })
      throw err
    }
  },

  updateMachine: async (id: string, data: Partial<MachineCreate>) => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch(`https://api.company.local/api/masters/machines/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) throw new Error('Failed to update')

      const updated = await response.json()
      set((state) => ({
        machines: state.machines.map((m) => (m.id === id ? updated : m)),
      }))

      return updated
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Update failed'
      set({ error: message })
      throw err
    }
  },

  inactivateMachine: async (id: string) => {
    try {
      const token = localStorage.getItem('access-token')
      await fetch(`https://api.company.local/api/masters/machines/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      set((state) => ({
        machines: state.machines.filter((m) => m.id !== id),
      }))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Inactivation failed'
      set({ error: message })
      throw err
    }
  },

  // Fabrics (similar implementation)
  createFabric: async (data: FabricCreate) => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch('https://api.company.local/api/masters/fabrics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) throw new Error('Failed to create')

      const fabric = await response.json()
      set((state) => ({
        fabrics: [...state.fabrics, fabric],
      }))

      return fabric
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Creation failed'
      set({ error: message })
      throw err
    }
  },

  updateFabric: async (id: string, data: Partial<FabricCreate>) => {
    try {
      const token = localStorage.getItem('access-token')
      const response = await fetch(`https://api.company.local/api/masters/fabrics/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) throw new Error('Failed to update')

      const updated = await response.json()
      set((state) => ({
        fabrics: state.fabrics.map((f) => (f.id === id ? updated : f)),
      }))

      return updated
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Update failed'
      set({ error: message })
      throw err
    }
  },

  inactivateFabric: async (id: string) => {
    try {
      const token = localStorage.getItem('access-token')
      await fetch(`https://api.company.local/api/masters/fabrics/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      set((state) => ({
        fabrics: state.fabrics.filter((f) => f.id !== id),
      }))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Inactivation failed'
      set({ error: message })
      throw err
    }
  },

  refreshCache: async () => {
    await get().fetchAllMasters()
  },

  getCacheStatus: () => {
    const { last_updated, cache_ttl_ms } = get()
    if (!last_updated) {
      return { is_expired: true, age_ms: 0 }
    }

    const age_ms = Date.now() - new Date(last_updated).getTime()
    return {
      is_expired: age_ms > cache_ttl_ms,
      age_ms,
    }
  },

  clearError: () => {
    set({ error: null })
  },
}))

// Hook for component usage
export const useMaster = () => {
  const store = useMasterStore()
  return {
    defects: store.defects,
    machines: store.machines,
    fabrics: store.fabrics,
    is_loading: store.loading,
    error: store.error,
    fetchAllMasters: store.fetchAllMasters,
    createDefect: store.createDefect,
    updateDefect: store.updateDefect,
    inactivateDefect: store.inactivateDefect,
    createMachine: store.createMachine,
    updateMachine: store.updateMachine,
    inactivateMachine: store.inactivateMachine,
    createFabric: store.createFabric,
    updateFabric: store.updateFabric,
    inactivateFabric: store.inactivateFabric,
  }
}
