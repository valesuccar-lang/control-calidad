/**
 * Approval Store — Zustand
 * Manages pending approvals, approval history, and stats
 */

import { create } from 'zustand'
import { Approval, ApprovalStatus, PendingApproval, ApprovalStats } from '../types'

export interface ApprovalState {
  // State
  pending_approvals: PendingApproval[]
  approval_history: Approval[]
  stats: ApprovalStats | null
  loading: boolean
  error: string | null
  selected_approval_id: string | null

  // Actions
  fetchPendingApprovals: () => Promise<void>
  fetchApprovalStats: () => Promise<void>
  fetchApprovalHistory: () => Promise<void>
  approveInspection: (inspection_id: string, comment?: string) => Promise<void>
  rejectInspection: (inspection_id: string, reason: string) => Promise<void>
  setSelectedApproval: (approval_id: string | null) => void
  loadPendingApprovals: (approvals: PendingApproval[]) => void
  removePendingApproval: (inspection_id: string) => void
  clearError: () => void
}

export const useApprovalStore = create<ApprovalState>((set, get) => ({
  pending_approvals: [],
  approval_history: [],
  stats: null,
  loading: false,
  error: null,
  selected_approval_id: null,

  fetchPendingApprovals: async () => {
    set({ loading: true, error: null })
    try {
      const response = await fetch(
        'https://api.company.local/api/inspections/pending-approval?limit=20&offset=0',
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access-token')}`,
          },
        },
      )

      if (!response.ok) throw new Error('Failed to fetch pending approvals')

      const data = await response.json()
      set({
        pending_approvals: data,
        loading: false,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Fetch failed'
      set({ error: message, loading: false })
    }
  },

  fetchApprovalStats: async () => {
    try {
      const response = await fetch(
        'https://api.company.local/api/approvals/stats',
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access-token')}`,
          },
        },
      )

      if (!response.ok) throw new Error('Failed to fetch stats')

      const stats: ApprovalStats = await response.json()
      set({ stats })
    } catch (err) {
      console.error('Stats fetch error:', err)
    }
  },

  fetchApprovalHistory: async () => {
    try {
      const response = await fetch(
        'https://api.company.local/api/approvals/my-approvals?limit=10&offset=0',
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access-token')}`,
          },
        },
      )

      if (!response.ok) throw new Error('Failed to fetch history')

      const data = await response.json()
      set({
        approval_history: data,
      })
    } catch (err) {
      console.error('History fetch error:', err)
    }
  },

  approveInspection: async (inspection_id: string, comment?: string) => {
    set({ loading: true, error: null })
    try {
      const response = await fetch('https://api.company.local/api/approvals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access-token')}`,
        },
        body: JSON.stringify({
          inspection_id,
          status: ApprovalStatus.APPROVED,
          comment,
        }),
      })

      if (!response.ok) throw new Error('Failed to approve')

      const approval = await response.json()

      // Remove from pending
      set((state) => ({
        pending_approvals: state.pending_approvals.filter((a) => a.id !== inspection_id),
        approval_history: [approval, ...state.approval_history],
        loading: false,
        selected_approval_id: null,
      }))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Approval failed'
      set({ error: message, loading: false })
      throw err
    }
  },

  rejectInspection: async (inspection_id: string, reason: string) => {
    if (!reason || reason.length < 10) {
      set({ error: 'Rejection reason must be at least 10 characters' })
      throw new Error('Invalid reason')
    }

    set({ loading: true, error: null })
    try {
      const response = await fetch('https://api.company.local/api/approvals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access-token')}`,
        },
        body: JSON.stringify({
          inspection_id,
          status: ApprovalStatus.REJECTED,
          comment: reason,
        }),
      })

      if (!response.ok) throw new Error('Failed to reject')

      const approval = await response.json()

      set((state) => ({
        pending_approvals: state.pending_approvals.filter((a) => a.id !== inspection_id),
        approval_history: [approval, ...state.approval_history],
        loading: false,
        selected_approval_id: null,
      }))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Rejection failed'
      set({ error: message, loading: false })
      throw err
    }
  },

  setSelectedApproval: (approval_id: string | null) => {
    set({ selected_approval_id: approval_id })
  },

  loadPendingApprovals: (approvals: PendingApproval[]) => {
    set({
      pending_approvals: approvals,
      error: null,
    })
  },

  removePendingApproval: (inspection_id: string) => {
    set((state) => ({
      pending_approvals: state.pending_approvals.filter((a) => a.id !== inspection_id),
    }))
  },

  clearError: () => {
    set({ error: null })
  },
}))

// Hook for component usage
export const useApproval = () => {
  const store = useApprovalStore()
  return {
    pending_approvals: store.pending_approvals,
    approval_history: store.approval_history,
    stats: store.stats,
    is_loading: store.loading,
    error: store.error,
    selected_approval_id: store.selected_approval_id,
    fetchPendingApprovals: store.fetchPendingApprovals,
    fetchApprovalStats: store.fetchApprovalStats,
    approveInspection: store.approveInspection,
    rejectInspection: store.rejectInspection,
    setSelectedApproval: store.setSelectedApproval,
  }
}
