/**
 * Inspection Store — Zustand
 * Manages inspection data, drafts, photos, and sync status
 */

import { create } from 'zustand'
import { v4 as uuid } from 'uuid'
import {
  Inspection,
  InspectionDraft,
  InspectionCreate,
  Photo,
  SyncStatus,
  InspectionStatus,
} from '../types'

export interface InspectionState {
  // State
  inspections: Record<string, Inspection>
  current_inspection_id: string | null
  loading: boolean
  error: string | null

  // Actions
  createInspection: (lote_id: string) => void
  addPhoto: (inspection_id: string, photo: Photo) => void
  removePhoto: (inspection_id: string, photo_id: string) => void
  updateComment: (inspection_id: string, comment: string) => void
  updateDefectType: (inspection_id: string, defect_type_id: string, machine_id?: string) => void
  updateMachine: (inspection_id: string, machine_id: string) => void
  submitInspection: (inspection_id: string) => Promise<void>
  saveDraft: (inspection_id: string) => Promise<void>
  setCurrentInspection: (inspection_id: string | null) => void
  loadInspections: (inspections: Inspection[]) => void
  updateSyncStatus: (inspection_id: string, status: SyncStatus, error?: string) => void
  clearError: () => void

  // Selectors
  getCurrentInspection: () => Inspection | null
  getPendingPhotos: () => number
  canSubmit: () => boolean
  getInspectionsBySync: (status: SyncStatus) => Inspection[]
}

export const useInspectionStore = create<InspectionState>((set, get) => ({
  inspections: {},
  current_inspection_id: null,
  loading: false,
  error: null,

  createInspection: (lote_id: string) => {
    const newId = uuid()
    const now = new Date().toISOString()

    set((state) => ({
      inspections: {
        ...state.inspections,
        [newId]: {
          id: newId,
          lote_id,
          defect_type_id: '',
          machine_culpable_id: undefined,
          comment: '',
          photos: [],
          status: InspectionStatus.DRAFT,
          sync_status: SyncStatus.PENDING,
          check_in: now,
          created_at: now,
          updated_at: now,
          synced: false,
        },
      },
      current_inspection_id: newId,
      error: null,
    }))
  },

  addPhoto: (inspection_id: string, photo: Photo) => {
    set((state) => {
      const inspection = state.inspections[inspection_id]
      if (!inspection) return state

      const newPhoto: Photo = {
        ...photo,
        id: photo.id || uuid(),
        inspection_id,
      }

      return {
        inspections: {
          ...state.inspections,
          [inspection_id]: {
            ...inspection,
            photos: [...inspection.photos, newPhoto],
            updated_at: new Date().toISOString(),
          },
        },
        error: null,
      }
    })
  },

  removePhoto: (inspection_id: string, photo_id: string) => {
    set((state) => {
      const inspection = state.inspections[inspection_id]
      if (!inspection) return state

      return {
        inspections: {
          ...state.inspections,
          [inspection_id]: {
            ...inspection,
            photos: inspection.photos.filter((p) => p.id !== photo_id),
            updated_at: new Date().toISOString(),
          },
        },
      }
    })
  },

  updateComment: (inspection_id: string, comment: string) => {
    set((state) => {
      const inspection = state.inspections[inspection_id]
      if (!inspection) return state

      return {
        inspections: {
          ...state.inspections,
          [inspection_id]: {
            ...inspection,
            comment,
            updated_at: new Date().toISOString(),
          },
        },
        error: null,
      }
    })
  },

  updateDefectType: (inspection_id: string, defect_type_id: string, machine_id?: string) => {
    set((state) => {
      const inspection = state.inspections[inspection_id]
      if (!inspection) return state

      return {
        inspections: {
          ...state.inspections,
          [inspection_id]: {
            ...inspection,
            defect_type_id,
            machine_culpable_id: machine_id || inspection.machine_culpable_id,
            updated_at: new Date().toISOString(),
          },
        },
        error: null,
      }
    })
  },

  updateMachine: (inspection_id: string, machine_id: string) => {
    set((state) => {
      const inspection = state.inspections[inspection_id]
      if (!inspection) return state

      return {
        inspections: {
          ...state.inspections,
          [inspection_id]: {
            ...inspection,
            machine_culpable_id: machine_id,
            updated_at: new Date().toISOString(),
          },
        },
      }
    })
  },

  submitInspection: async (inspection_id: string) => {
    const state = get()
    const inspection = state.inspections[inspection_id]
    if (!inspection) throw new Error('Inspection not found')

    set({ loading: true, error: null })

    try {
      // Validate
      if (!inspection.comment || inspection.comment.length < 10) {
        throw new Error('Comment must be at least 10 characters')
      }
      if (inspection.photos.length === 0) {
        throw new Error('At least one photo is required')
      }
      if (!inspection.defect_type_id) {
        throw new Error('Defect type is required')
      }

      // Save locally (IndexedDB - offline guarantee)
      // This would call inspectionService.saveDraftOffline(inspection)
      // For now, just update state
      set((state) => ({
        inspections: {
          ...state.inspections,
          [inspection_id]: {
            ...state.inspections[inspection_id],
            status: InspectionStatus.REGISTERED,
            sync_status: SyncStatus.PENDING,
            check_out: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        },
        loading: false,
      }))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Submission failed'
      set({
        error: message,
        loading: false,
      })
      throw err
    }
  },

  saveDraft: async (inspection_id: string) => {
    const inspection = get().inspections[inspection_id]
    if (!inspection) throw new Error('Inspection not found')

    // This would call inspectionService.saveDraftOffline(inspection)
    // For now, just log
    console.log('Saving draft:', inspection)
  },

  setCurrentInspection: (inspection_id: string | null) => {
    set({ current_inspection_id: inspection_id })
  },

  loadInspections: (inspections: Inspection[]) => {
    const inspectionsMap = inspections.reduce(
      (acc, insp) => {
        acc[insp.id] = insp
        return acc
      },
      {} as Record<string, Inspection>,
    )

    set({
      inspections: inspectionsMap,
      error: null,
    })
  },

  updateSyncStatus: (inspection_id: string, status: SyncStatus, error?: string) => {
    set((state) => {
      const inspection = state.inspections[inspection_id]
      if (!inspection) return state

      return {
        inspections: {
          ...state.inspections,
          [inspection_id]: {
            ...inspection,
            sync_status: status,
            synced: status === SyncStatus.SYNCED,
            last_error: error,
            updated_at: new Date().toISOString(),
          },
        },
      }
    })
  },

  clearError: () => {
    set({ error: null })
  },

  // Selectors
  getCurrentInspection: () => {
    const { current_inspection_id, inspections } = get()
    if (!current_inspection_id) return null
    return inspections[current_inspection_id] || null
  },

  getPendingPhotos: () => {
    const current = get().getCurrentInspection()
    return current?.photos.length || 0
  },

  canSubmit: () => {
    const current = get().getCurrentInspection()
    if (!current) return false
    return !!(
      current.comment &&
      current.comment.length >= 10 &&
      current.photos.length > 0 &&
      current.defect_type_id
    )
  },

  getInspectionsBySync: (status: SyncStatus) => {
    const { inspections } = get()
    return Object.values(inspections).filter((insp) => insp.sync_status === status)
  },
}))

// Hook for component usage
export const useInspection = () => {
  const store = useInspectionStore()
  const current = store.getCurrentInspection()

  return {
    current_inspection: current,
    can_submit: store.canSubmit(),
    pending_photos: store.getPendingPhotos(),
    is_loading: store.loading,
    error: store.error,
    createInspection: store.createInspection,
    addPhoto: store.addPhoto,
    removePhoto: store.removePhoto,
    updateComment: store.updateComment,
    updateDefectType: store.updateDefectType,
    updateMachine: store.updateMachine,
    submitInspection: store.submitInspection,
    setCurrentInspection: store.setCurrentInspection,
  }
}
