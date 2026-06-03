/**
 * TypeScript Types & Interfaces
 * Frontend Web Unit - Control de Calidad Textil
 */

// ============================================================================
// AUTH TYPES
// ============================================================================

export enum Role {
  OPERARIO = "OPERARIO",
  SUPERVISOR = "SUPERVISOR",
  JEFE_QA = "JEFE_QA",
  GERENTE = "GERENTE",
  ADMIN = "ADMIN",
}

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  user: User
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenPayload {
  sub: string
  user_id: string
  email: string
  role: Role
  exp: number
  iat: number
}

// ============================================================================
// LOTE TYPES (HDR)
// ============================================================================

export enum LoteStatus {
  PENDING = "PENDING",
  IN_PROCESS = "IN_PROCESS",
  REPROCESSED = "REPROCESSED",
  APPROVED = "APPROVED",
}

export interface Lote {
  id: string // HDR-12847
  fabric_id: string
  fabric_name?: string
  quantity_meters: number
  status: LoteStatus
  created_at: string
  updated_at: string
}

export interface LoteSearchRequest {
  lote_id: string
}

export interface LoteResponse {
  id: string
  fabric_id: string
  fabric_name: string
  quantity_meters: number
  status: LoteStatus
  created_at: string
}

// ============================================================================
// INSPECTION TYPES
// ============================================================================

export enum InspectionStatus {
  DRAFT = "DRAFT",
  REGISTERED = "REGISTERED",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

export enum SyncStatus {
  PENDING = "PENDING",
  SYNCING = "SYNCING",
  SYNCED = "SYNCED",
  FAILED = "FAILED",
}

export interface Photo {
  id: string
  inspection_id?: string
  blob?: Blob
  base64?: string
  metadata: PhotoMetadata
  quality: "PASS" | "WARN" | "FAIL"
  created_at?: string
}

export interface PhotoMetadata {
  laplacian: number
  brightness: number
  contrast: number
  file_size: number
  width: number
  height: number
}

export interface Inspection {
  id: string
  lote_id: string
  analista_id?: string
  analista_name?: string
  defect_type_id: string
  defect_type_name?: string
  machine_culpable_id?: string
  machine_name?: string
  comment: string
  photos: Photo[]
  status: InspectionStatus
  sync_status: SyncStatus
  check_in: string
  check_out?: string
  created_at: string
  updated_at: string
  synced: boolean
  last_error?: string
}

export interface InspectionDraft extends Inspection {
  draft_id: string
  local_only: boolean
}

export interface InspectionCreate {
  lote_id: string
  defect_type_id: string
  machine_culpable_id?: string
  comment: string
  photos: Photo[] // with base64
}

export interface InspectionResponse {
  id: string
  lote_id: string
  status: InspectionStatus
  check_in: string
  synced: boolean
}

export interface InspectionListResponse {
  id: string
  lote_id: string
  fabric_name: string
  analista_name: string
  defect_type: string
  comment: string
  photo_url?: string
  status: InspectionStatus
  created_at: string
}

export interface InspectionDetailResponse extends Inspection {
  fabric_name: string
}

export interface InspectionSyncRequest {
  inspection: Inspection
  photos: Photo[]
}

export interface InspectionSyncResponse {
  inspection_id: string
  synced: boolean
  errors?: string[]
}

// ============================================================================
// APPROVAL TYPES
// ============================================================================

export enum ApprovalStatus {
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

export interface Approval {
  id: string
  inspection_id: string
  jefe_qa_id?: string
  jefe_qa_name?: string
  status: ApprovalStatus
  comment?: string
  created_at: string
  updated_at: string
}

export interface ApprovalCreate {
  inspection_id: string
  status: ApprovalStatus
  comment?: string
}

export interface ApprovalResponse {
  id: string
  inspection_id: string
  status: ApprovalStatus
  created_at: string
}

export interface ApprovalDetail extends Inspection {
  approval?: Approval
}

export interface PendingApproval {
  id: string
  lote_id: string
  fabric_name: string
  analista_name: string
  defect_type: string
  machine_name?: string
  comment: string
  photo_url?: string
  created_at: string
}

export interface ApprovalStats {
  pending_count: number
  approved_today: number
  rejected_today: number
  total_approved: number
  approval_rate: number
}

// ============================================================================
// MASTER TYPES (Defects, Machines, Fabrics)
// ============================================================================

export interface Defect {
  id: string // DEF-TON
  name: string // TONODIFFERENTE
  description: string
  typical_process?: string // TINTORERIA
  typical_machine_id?: string
  created_at?: string
  updated_at?: string
}

export interface DefectCreate {
  id: string
  name: string
  description: string
  typical_process?: string
  typical_machine_id?: string
}

export interface DefectUpdate {
  name?: string
  description?: string
  typical_process?: string
  typical_machine_id?: string
}

export interface Machine {
  id: string // MAQ-AGO-80
  name: string
  process?: string
  created_at?: string
  updated_at?: string
}

export interface MachineCreate {
  id: string
  name: string
  process?: string
}

export interface MachineUpdate {
  name?: string
  process?: string
}

export interface Fabric {
  id: string // NOVAKREPEL
  name: string
  composition?: string
  width_cm?: number
  weight_gsm?: number
  created_at?: string
  updated_at?: string
}

export interface FabricCreate {
  id: string
  name: string
  composition?: string
  width_cm?: number
  weight_gsm?: number
}

export interface FabricUpdate {
  name?: string
  composition?: string
  width_cm?: number
  weight_gsm?: number
}

export interface MastersCache {
  defects: Defect[]
  machines: Machine[]
  fabrics: Fabric[]
  last_updated: string
  ttl_ms: number
}

// ============================================================================
// OFFLINE SYNC TYPES
// ============================================================================

export enum SyncOperationType {
  CREATE_INSPECTION = "CREATE_INSPECTION",
  UPDATE_INSPECTION = "UPDATE_INSPECTION",
  APPROVE_INSPECTION = "APPROVE_INSPECTION",
  REJECT_INSPECTION = "REJECT_INSPECTION",
}

export interface SyncQueueItem {
  id: string
  operation: SyncOperationType
  payload: any
  retry_count: number
  last_error?: string
  status: SyncStatus
  enqueued_at: string
}

export interface SyncResult {
  successful: number
  failed: number
  total: number
  errors: SyncError[]
}

export interface SyncError {
  item_id: string
  operation: SyncOperationType
  error: string
  timestamp: string
}

export interface QueueStatus {
  pending: number
  syncing: number
  synced: number
  failed: number
  last_sync_time?: string
}

// ============================================================================
// NETWORK & STATUS TYPES
// ============================================================================

export enum NetworkStatus {
  ONLINE = "ONLINE",
  OFFLINE = "OFFLINE",
  POOR_CONNECTION = "POOR_CONNECTION",
}

export interface AppStatus {
  network: NetworkStatus
  is_syncing: boolean
  pending_count: number
  failed_count: number
  last_sync_time?: string
}

// ============================================================================
// ERROR TYPES
// ============================================================================

export interface ErrorReport {
  error_id: string
  timestamp: string
  message: string
  stack?: string
  context: ErrorContext
  severity: "ERROR" | "WARNING" | "INFO"
  metadata?: Record<string, any>
}

export interface ErrorContext {
  url: string
  user_role?: Role
  user_id?: string
  user_email?: string
  app_version: string
}

export interface AnalyticsEvent {
  event_name: string
  timestamp: string
  user_id?: string
  user_role?: Role
  properties?: Record<string, any>
}

// ============================================================================
// FORM TYPES
// ============================================================================

export interface FormError {
  field: string
  message: string
}

export interface FormState<T> {
  data: T
  errors: FormError[]
  is_submitting: boolean
  is_valid: boolean
}

// ============================================================================
// API PAGINATION
// ============================================================================

export interface PaginationParams {
  limit: number
  offset: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

// ============================================================================
// API ERROR RESPONSE
// ============================================================================

export interface ApiError {
  detail: string
  status_code: number
  error_id?: string
}

export interface ApiResponse<T> {
  data?: T
  error?: ApiError
  success: boolean
}
