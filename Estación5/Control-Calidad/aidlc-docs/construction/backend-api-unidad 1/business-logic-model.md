# Business Logic Model — Backend API Unit (Unit 1)
**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Purpose**: Document business processes, workflows, and logic flows  
**Status**: FUNCTIONAL DESIGN PHASE

---

## 📊 BUSINESS LOGIC MODEL OVERVIEW

This document describes HOW the system processes business transactions across the 3 Bounded Contexts:

1. **Inspection Flow**: Analista captures defects (offline-first)
2. **Approval Flow**: Jefe QA validates findings
3. **Masters Flow**: Admin manages reference data
4. **Sync Flow**: Offline inspections sync to server

---

## 🔄 WORKFLOW 1: INSPECTION CAPTURE (Analista)

### Preconditions
- Analista is logged in with ANALISTA role
- WiFi available (online) OR offline capability ready
- Lote HDR-XXXXX exists in database

### Process Flow: Create Inspection

```
┌─────────────────────────────────────────────────────────────────────┐
│ UC1: Register Inspection (Defect Finding)                           │
└─────────────────────────────────────────────────────────────────────┘

1. ANALISTA ACTION: Open Inspection Page
   │
   ├─ Render inspection form
   │  ├─ LoteSearchBar (search/scan HDR code)
   │  ├─ CameraCapture (take photo)
   │  ├─ DefectTypeSelector (dropdown: 25+ defects from Masters)
   │  ├─ CommentInput (text area, min 10 chars)
   │  ├─ MachineSelector (auto-filled from defect.typicalMachine)
   │  └─ SaveButton
   │
   └─ ONLINE or OFFLINE both possible

2. ANALISTA ACTION: Search Lote
   │
   ├─ Input: Scan "HDR-12847"
   ├─ API Call: GET /api/lotes/HDR-12847
   │
   └─ If ONLINE:
       └─ Server returns Lote from DB
   
   └─ If OFFLINE:
       └─ Browser returns Lote from IndexedDB (cached from earlier)

3. ANALISTA ACTION: Capture Photo
   │
   ├─ Camera opens, takes photo
   ├─ Client: Compress to JPEG 80% quality
   ├─ Client: Calculate SHA256 checksum
   ├─ Client: Store photo bytes in memory (temp)
   │
   └─ Validation:
       └─ Photo size ≤ 500KB ✓
       └─ Format = image/jpeg ✓
       └─ Checksum calculated ✓

4. ANALISTA ACTION: Select Defect Type
   │
   ├─ Dropdown shows ACTIVE defects from Masters
   ├─ Selection: "TONODIFFERENTE" (DEF-TON)
   │
   └─ Side Effect:
       └─ MachineSelector auto-fills with defect.typicalMachine
           (e.g., "AGOTAMIENTO 80")

5. ANALISTA ACTION: Enter Comment
   │
   ├─ TextArea: "Tono diferente en esquina inferior derecha, aproximadamente 20% del área"
   │
   └─ Validation:
       └─ Length: 89 chars (10 <= 89 <= 500) ✓

6. ANALISTA ACTION: Verify Machine (Optional Edit)
   │
   ├─ Pre-filled: AGOTAMIENTO 80 (from defect)
   ├─ Can edit if wrong machine identified
   │
   └─ Validation:
       └─ Machine must exist in Masters ✓

7. ANALISTA ACTION: Submit (Click "Guardar")
   │
   ├─ Client Validation:
   │  ├─ defect_id: not empty ✓
   │  ├─ comment: 10-500 chars ✓
   │  ├─ photo: not null, ≤500KB ✓
   │  ├─ machine_id: not empty ✓
   │  └─ lote_id: not empty ✓
   │
   └─ Prepare Request DTO:
       {
         lote_id: "HDR-12847",
         defect_id: "DEF-TON",
         comment: "Tono diferente en esquina...",
         photo_base64: "[compressed photo bytes]",
         photo_checksum: "a1b2c3d4...",
         machine_id: "MAQ-AGO-80"
       }

8. ONLINE PATH: POST /api/inspections
   │
   ├─ Request arrives at FastAPI server
   ├─ Route Handler: create_inspection(req: InspectionCreateDTO)
   │
   ├─ Step 8a: Validate DTO
   │  └─ Pydantic validates types, lengths, formats ✓
   │
   ├─ Step 8b: Load Lote Aggregate
   │  ├─ Query DB: SELECT * FROM lotes WHERE lote_id = "HDR-12847"
   │  ├─ Result: Lote aggregate with status, fabric_id, quantity
   │  └─ Validate: Lote exists ✓
   │
   ├─ Step 8c: Call InspectionService.register_inspection()
   │  │
   │  ├─ Domain Logic: Validate cross-domain references
   │  │  ├─ Defect exists? Query DefectRepository.find_by_id("DEF-TON")
   │  │  │  └─ SELECT * FROM defects WHERE defect_id = "DEF-TON" AND status = 'ACTIVE'
   │  │  │  └─ Result: Defect aggregate ✓
   │  │  │
   │  │  └─ Machine exists? Query MachineRepository.find_by_id("MAQ-AGO-80")
   │  │     └─ SELECT * FROM machines WHERE machine_id = "MAQ-AGO-80" AND status = 'ACTIVE'
   │  │     └─ Result: Machine aggregate ✓
   │  │
   │  ├─ Domain Logic: Detect duplicates
   │  │  └─ find_by_lote_defect_photo(lote_id, defect_id, photo_checksum)
   │  │     └─ Result: No duplicate found ✓
   │  │
   │  ├─ Create Value Objects:
   │  │  ├─ defect_vo = DefectType(defect_id="DEF-TON", defect_name="TONODIFFERENTE", ...)
   │  │  ├─ comment_vo = Comment(text="Tono diferente...", created_at=now())
   │  │  ├─ photograph_vo = Photograph(checksum="a1b2c3d4...", size_bytes=450000, ...)
   │  │  ├─ machine_vo = MachineId(machine_id="MAQ-AGO-80", machine_name="AGOTAMIENTO 80")
   │  │  └─ inspection_time_vo = InspectionTime(check_in=2026-05-28T14:35:22Z, check_out=None)
   │  │
   │  ├─ Create Inspection Aggregate:
   │  │  └─ inspection = Inspection(
   │  │      inspection_id=uuid4(),
   │  │      lote_id="HDR-12847",
   │  │      analista_id=current_user.id,
   │  │      defect=defect_vo,
   │  │      comment=comment_vo,
   │  │      photograph=photograph_vo,
   │  │      machine_identified=machine_vo,
   │  │      inspection_time=inspection_time_vo,
   │  │      sync_status=SyncStatus.SYNCED,  ← Already on server
   │  │      created_at=now()
   │  │    )
   │  │
   │  ├─ Persist: inspection_repo.save(inspection)
   │  │  └─ INSERT INTO inspections (
   │  │      inspection_id, lote_id, analista_id, defect_id, comment_text,
   │  │      photo_id, photo_checksum, machine_id, check_in, check_out,
   │  │      sync_status, created_at
   │  │    ) VALUES (...)
   │  │
   │  └─ Return: inspection_id, status, created_at
   │
   ├─ Step 8d: Response Handler
   │  ├─ InspectionCreateResponseDTO {
   │  │    inspection_id: "550e8400-e29b-41d4-a716-446655440000",
   │  │    status: "CREATED",
   │  │    lote_id: "HDR-12847",
   │  │    sync_status: "SYNCED",
   │  │    created_at: "2026-05-28T14:35:22Z"
   │  │  }
   │  └─ HTTP 201 Created
   │
   └─ Client: Render confirmation
       ├─ Toast: "Inspección guardada exitosamente"
       ├─ Clear form
       ├─ Add to InspectionHistory (local store)
       └─ Ready for next defect

9. OFFLINE PATH: POST /api/inspections (no connection)
   │
   ├─ Request queued in Service Worker
   ├─ Optimistic response: HTTP 201 (fake)
   │
   ├─ Photo stored in IndexedDB:
   │  └─ DB.photos.add({
   │      lote_id: "HDR-12847",
   │      photo_blob: [binary],
   │      checksum: "a1b2c3d4...",
   │      timestamp: now()
   │    })
   │
   ├─ Inspection stored in IndexedDB:
   │  └─ DB.inspections.add({
   │      inspection_id: "550e8400-...",
   │      lote_id: "HDR-12847",
   │      defect_id: "DEF-TON",
   │      comment: "Tono diferente...",
   │      machine_id: "MAQ-AGO-80",
   │      check_in: now(),
   │      check_out: null,
   │      sync_status: "PENDING",
   │      created_at: now()
   │    })
   │
   ├─ Update offline store:
   │  └─ offlineStore.pendingInspections += 1
   │  └─ UI shows: "📡 OFFLINE (1 inspection pending)"
   │
   └─ Client: Show toast + pending indicator
       └─ "Inspección guardada localmente (pendiente sincronización)"

10. SYNC TRIGGERED: Online connection detected
    │
    ├─ Service Worker: addEventListener('online')
    ├─ Query: SELECT * FROM inspections WHERE sync_status = 'PENDING'
    │  └─ Result: 1 pending inspection
    │
    ├─ For each pending inspection:
    │  ├─ POST /api/inspections/sync
    │  │  ├─ Headers: Authorization: Bearer {token}
    │  │  ├─ Body: {
    │  │  │    inspection_id,
    │  │  │    lote_id,
    │  │  │    defect_id,
    │  │  │    comment,
    │  │  │    photo_base64,
    │  │  │    machine_id
    │  │  │  }
    │  │  │
    │  │  ├─ Server: Same validation as step 8
    │  │  ├─ Server: Check idempotency
    │  │  │  └─ SELECT * FROM inspections WHERE inspection_id = ?
    │  │  │  └─ If exists and sync_status = SYNCED: return success (idempotent)
    │  │  │  └─ Else: INSERT or UPDATE
    │  │  │
    │  │  └─ Response: { status: "SYNCED", inspection_id }
    │  │
    │  └─ Client: Update IndexedDB
    │     └─ inspections.update(inspection_id, {sync_status: "SYNCED"})
    │
    ├─ Update UI:
    │  ├─ offlineStore.pendingInspections = 0
    │  ├─ UI: "📡 ONLINE (All synced)"
    │  └─ Toast: "Inspecciones sincronizadas"
    │
    └─ Clear sync queue

Postconditions:
├─ Inspection created (stored in DB)
├─ Photo persisted (file system or S3)
├─ sync_status = SYNCED or PENDING (depending on online/offline)
├─ Analista can proceed to next defect
└─ Inspection ready for approval flow
```

### Error Paths

#### Error EP1: Defect Not Found
```
If step 8c validation fails (defect_id not found):

├─ InspectionService.register_inspection() raises ValueError
├─ FastAPI error handler catches exception
├─ Response: HTTP 400 Bad Request
│  └─ { error: "Defect DEF-INVALID not found in Masters" }
│
└─ Client: Render error modal
   └─ "El tipo de defecto seleccionado no existe. Recargue la página."
```

#### Error EP2: Photo Checksum Mismatch
```
If photo corrupted during upload:

├─ Step 8c: Server computes SHA256(photo_bytes)
├─ Verify: computed_checksum == req.photo_checksum
├─ If NOT equal:
│  ├─ Raise ValueError("Photo checksum mismatch")
│  ├─ HTTP 400 Bad Request
│  └─ Client: Retry upload (network issue)
│
└─ Max retries: 5 attempts, then mark as SYNC_FAILED
```

#### Error EP3: Machine Not Found
```
(Same as Defect Not Found)
```

#### Error EP4: Duplicate Inspection
```
If analista clicks "Save" twice by accident:

├─ Second POST /api/inspections same data
├─ Step 8c: find_by_lote_defect_photo() returns existing inspection
├─ Service raises ValueError("Inspection already exists")
│  OR returns existing inspection (idempotent)
│
└─ Client: Toast "Ya existe esta inspección" OR success (idempotent)
```

---

---

## 🔄 WORKFLOW 2: INSPECTION APPROVAL (Jefe QA)

### Preconditions
- Jefe QA is logged in with JEFE_QA role
- Online (approval is synchronous, no offline support for now)
- Inspections exist in database (pending approval)

### Process Flow: Approve Inspection

```
┌──────────────────────────────────────────────────────────────┐
│ UC2: Approve or Reject Inspection                            │
└──────────────────────────────────────────────────────────────┘

1. JEFE QA ACTION: Open Approval Page
   │
   └─ Render approval interface:
      ├─ PendingLotsTable (list all lotes with pending inspections)
      │  Columns: LoteID, Fabric, DefectCount, Status
      │
      └─ Example data:
         ├─ HDR-12847 | NOVAKREPEL | 2 defects | PENDING
         ├─ HDR-12848 | POLYESTER  | 1 defect  | PENDING
         └─ ...

2. JEFE QA ACTION: Select Lote
   │
   ├─ Click row: HDR-12847
   ├─ API Call: GET /api/lotes/HDR-12847/inspections/pending
   │
   └─ Server:
      ├─ SELECT * FROM inspections
      │  WHERE lote_id = "HDR-12847"
      │  AND approval_id IS NULL (no approval yet)
      │
      └─ Response:
         [
           {
             inspection_id: "550e...",
             defect: { defect_id: "DEF-TON", name: "TONODIFFERENTE" },
             comment: "Tono diferente...",
             photo_url: "/api/photos/550e...",
             machine: "AGOTAMIENTO 80",
             check_in: "2026-05-28T14:35:22Z"
           },
           ...
         ]

3. JEFE QA ACTION: Review First Inspection
   │
   ├─ Click inspection row
   ├─ Modal opens showing:
   │  ├─ Large photo (defect)
   │  ├─ Defect type: TONODIFFERENTE
   │  ├─ Comment: "Tono diferente..."
   │  ├─ Machine: AGOTAMIENTO 80
   │  ├─ Analyst: Juan Pérez
   │  ├─ Check-in time: 14:35:22
   │  └─ Two buttons: [APROBAR] [RECHAZAR]
   │
   └─ Jefe QA examines photo and comment

4. JEFE QA DECISION: APPROVE
   │
   ├─ Click [APROBAR] button
   │
   └─ Client: POST /api/approvals
      ├─ Body:
      │  {
      │    inspection_id: "550e...",
      │    decision: "APPROVED"
      │  }
      │
      └─ Server Handler: approve_inspection()
         │
         ├─ Step 4a: Load Inspection
         │  └─ inspection_repo.find_by_id("550e...")
         │
         ├─ Step 4b: Call ApprovalService.approve_inspection()
         │  │
         │  ├─ Verify inspection exists ✓
         │  ├─ Create Approval Aggregate:
         │  │  └─ approval = Approval(
         │  │      approval_id=uuid4(),
         │  │      inspection_id="550e...",
         │  │      jefe_qa_id=current_user.id,
         │  │      decision=ApprovalDecision.APPROVED,
         │  │      rejection_reason=None,
         │  │      timestamp=now()
         │  │    )
         │  │
         │  ├─ Persist: approval_repo.save(approval)
         │  │  └─ INSERT INTO approvals (...)
         │  │
         │  ├─ Publish Event:
         │  │  └─ event_bus.publish(InspectionApproved(
         │  │      approval_id,
         │  │      inspection_id,
         │  │      jefe_qa_id,
         │  │      timestamp
         │  │    ))
         │  │
         │  └─ Return: approval_id, status
         │
         ├─ Step 4c: Application Layer Handler (Event Subscriber)
         │  ├─ NotificationService.handle_inspection_approved(event)
         │  ├─ Send notification to Gerente:
         │  │  └─ "Inspección HDR-12847/DEF-TON aprobada por Jefe QA"
         │  │
         │  └─ Update dashboard metrics (Gerente sees real-time)
         │
         └─ Response: HTTP 201 Created
            ├─ {
            │    approval_id: "...",
            │    status: "APPROVED",
            │    timestamp: "2026-05-28T15:02:15Z"
            │  }
            │
            └─ Client: Modal closes
               ├─ Toast: "Inspección aprobada"
               ├─ Remove from pending list
               └─ Show next pending inspection (if any)

Postconditions (APPROVED):
├─ Approval record created in DB
├─ InspectionApproved event published
├─ Gerente notified (real-time)
├─ Lote can now proceed to reproceso
└─ Inspection marked as APPROVED in history
```

### Alternative: REJECT

```
4 (Alternative). JEFE QA DECISION: REJECT
   │
   ├─ Click [RECHAZAR] button
   │
   └─ Modal: Rejection Reason Form
      ├─ Dropdown: "Razón de rechazo"
      │  Options: PHOTO_BLURRY, FALSE_ALARM, NOT_CONFIRMED, OTHER
      │
      ├─ Text: "Detalle adicional (min 10 chars)"
      │  Value: "Foto borrosa, no se ve claramente el tonodifferente"
      │
      └─ [CONFIRMAR RECHAZO] button

5. JEFE QA CONFIRMS REJECTION
   │
   ├─ POST /api/approvals
   │  ├─ Body:
   │  │  {
   │  │    inspection_id: "550e...",
   │  │    decision: "REJECTED",
   │  │    rejection_reason: {
   │  │      reason: "Foto borrosa, no se ve...",
   │  │      reason_code: "PHOTO_BLURRY"
   │  │    }
   │  │  }
   │  │
   │  └─ Server: Same flow as APPROVE
   │     ├─ Create Approval(decision=REJECTED, rejection_reason={...})
   │     ├─ Publish InspectionRejected event
   │     └─ Application Layer handler notifies Analista
   │
   └─ Analista receives notification:
      └─ "Tu inspección HDR-12847 fue rechazada: Foto borrosa"
```

---

## 🔄 WORKFLOW 3: MASTERS MANAGEMENT (Admin)

### Preconditions
- Admin is logged in with ADMIN role
- Online (Masters CRUD requires server)

### Process Flow: Import Masters CSV

```
┌──────────────────────────────────────────────────────────────┐
│ UC3: Bulk Import Masters (Defects, Machines, Fabrics)        │
└──────────────────────────────────────────────────────────────┘

1. ADMIN ACTION: Open Config Page
   │
   └─ Render config tabs:
      ├─ Masters (defects, machines, fabrics)
      ├─ Users (CRUD users + roles)
      └─ Settings (company, ACATEX integration)

2. ADMIN ACTION: Masters Tab
   │
   ├─ Click "Defectos" sub-tab
   ├─ Render:
   │  ├─ Table: Current defects (ACTIVE + INACTIVE)
   │  ├─ Columns: DefectID, Name, Process, Machine, Status
   │  ├─ Action buttons: [CREAR] [EDITAR] [INACTIVAR]
   │  └─ Import button: [IMPORTAR CSV]
   │
   └─ Click [IMPORTAR CSV]
      ├─ File picker opens
      ├─ Admin selects "defects.csv"
      │
      └─ CSV format:
         type,id,name,description,process,typical_machine
         DEFECT,DEF-TON,TONODIFFERENTE,Tono...,TINTORERIA,MAQ-AGO-80
         DEFECT,DEF-MAN,MANCHAS,Manchas...,LAVADO,MAQ-LAV-01
         ...

3. ADMIN ACTION: Upload CSV
   │
   ├─ POST /api/masters/bulk-import
   │  ├─ Content-Type: multipart/form-data
   │  ├─ File: defects.csv
   │  │
   │  └─ Server Handler:
   │     ├─ Read CSV file
   │     ├─ For each row:
   │     │  ├─ Parse: type, id, name, ...
   │     │  │
   │     │  ├─ If type = DEFECT:
   │     │  │  ├─ Check if defect_id exists
   │     │  │  ├─ If exists: counts['skipped'] += 1, continue
   │     │  │  ├─ If not:
   │     │  │  │  ├─ Create Defect(
   │     │  │  │  │    defect_id=row['id'],
   │     │  │  │  │    defect_name=row['name'],
   │     │  │  │  │    description=row['description'],
   │     │  │  │  │    typical_process=row['process'],
   │     │  │  │  │    status=ACTIVE
   │     │  │  │  │  )
   │     │  │  │  ├─ defect_repo.save(defect)
   │     │  │  │  └─ counts['imported'] += 1
   │     │  │  │
   │     │  │  └─ (Same for MACHINE and FABRIC types)
   │     │  │
   │     │  └─ On error:
   │     │     └─ counts['errors'] += 1 (log, continue)
   │     │
   │     └─ Return:
   │        {
   │          imported: 15,
   │          skipped: 8,
   │          errors: 0
   │        }
   │
   └─ Client: Display results
      ├─ Toast: "15 defectos importados, 8 saltados"
      ├─ Refresh table
      └─ Show new defects in dropdown
```

### Alternative: Manual Create Defect

```
ADMIN ACTION: Click [CREAR]
   │
   ├─ Modal: Defect Form
   │  ├─ defect_id: [input] (e.g., "DEF-NEW")
   │  ├─ defect_name: [input] (e.g., "NUEVO DEFECTO")
   │  ├─ description: [textarea]
   │  ├─ typical_process: [dropdown] (TINTORERIA, LAVADO, ...)
   │  ├─ typical_machine: [dropdown] (auto-populated from Masters)
   │  └─ [CREAR] button
   │
   └─ POST /api/masters/defects
      ├─ Body: { defect_id, defect_name, ... }
      │
      └─ Server:
         ├─ MastersService.create_defect(...)
         │  ├─ Check uniqueness: defect_id not exists ✓
         │  ├─ Validate machine exists (if provided)
         │  ├─ Create Defect aggregate
         │  ├─ defect_repo.save(defect)
         │  └─ Publish DefectCreated event
         │
         └─ Response: HTTP 201, defect_id
```

---

## 🔄 WORKFLOW 4: OFFLINE SYNC (Background)

### Preconditions
- Browser tab is open (even if user is not actively using)
- Service Worker is registered
- One or more PENDING inspections in IndexedDB

### Process Flow: Automatic Sync with Retry

```
┌──────────────────────────────────────────────────────────────┐
│ UC4: Offline Inspection Sync (Background)                    │
└──────────────────────────────────────────────────────────────┘

1. BROWSER EVENT: Online Status Change
   │
   └─ navigator.onLine changes from false → true
      ├─ Service Worker: addEventListener('online')
      │  └─ trigger_sync_queue()
      │
      └─ Zustand offlineStore: setOnline(true)
         └─ Trigger sync in React

2. QUERY PENDING INSPECTIONS
   │
   ├─ IndexedDB: SELECT * FROM inspections WHERE sync_status = 'PENDING'
   ├─ Result: [ { inspection_id: "550e...", ... }, ... ]
   │
   └─ For each pending inspection:
      └─ START SYNC RETRY LOOP

3. SYNC ATTEMPT 1 (Immediate)
   │
   ├─ POST /api/inspections/sync
   │  ├─ Body: inspection object (including photo_base64)
   │  │
   │  └─ Network call (0ms delay)
   │
   └─ Possible outcomes:
      ├─ A: Success (HTTP 200-201)
      │  └─ UPDATE inspections SET sync_status = 'SYNCED'
      │  └─ Remove from sync queue
      │
      ├─ B: Network error (timeout, ECONNREFUSED, etc.)
      │  └─ MARK_RETRY: sync_status = 'RETRY'
      │  └─ Schedule next attempt in 1 second
      │
      └─ C: HTTP error (400, 500, etc.)
         └─ Different handling per status code

4. SYNC ATTEMPT 2 (1 second later)
   │
   ├─ setTimeout(() => sync(), 1000)
   │
   └─ POST /api/inspections/sync (same as attempt 1)
      ├─ Success: SYNCED ✓
      ├─ Fail: retry again → next attempt in 2 seconds

5. SYNC ATTEMPT 3 (2 seconds later)
   ├─ setTimeout(() => sync(), 2000)

6. SYNC ATTEMPT 4 (4 seconds later)
   ├─ setTimeout(() => sync(), 4000)

7. SYNC ATTEMPT 5 (8 seconds later)
   ├─ setTimeout(() => sync(), 8000)

8. FINAL: After attempt 5 fails
   │
   ├─ If still failing:
   │  ├─ Mark: sync_status = 'SYNC_FAILED'
   │  ├─ Publish event: SyncFailed(inspection_id, error)
   │  │
   │  └─ Notify user:
   │     └─ Toast: "No se pudo sincronizar. Reintente manualmente."
   │     └─ Show [SINCRONIZAR] button in UI
   │
   └─ User can click [SINCRONIZAR] anytime
      └─ Restart sync loop

Total retry time: 0 + 1 + 2 + 4 + 8 = 15 seconds
If offline again during retry: Pause, resume on online

Idempotency Safety:
├─ POST /api/inspections/sync always includes inspection_id
├─ Server checks: SELECT * FROM inspections WHERE inspection_id = ?
├─ If exists AND sync_status = SYNCED: return success (idempotent)
├─ If not exists: create new
└─ No duplicates possible, safe to retry indefinitely
```

---

## 📊 ERROR HANDLING MATRIX

| Flow | Error Type | Handling | Outcome |
|------|-----------|----------|---------|
| Inspection | Defect not found | Raise ValueError (400) | User fix + retry |
| Inspection | Photo checksum fails | Raise ValueError (400) | User retake + retry |
| Inspection | Duplicate found | Return success (idempotent) | OK, move on |
| Inspection | DB constraint fails | Catch exception → 500 | Log + alert admin |
| Approval | Inspection not found | Raise ValueError (400) | Refresh + retry |
| Approval | No rejection reason | Raise ValueError (400) | User provides + retry |
| Masters | ID already exists | Raise ValueError (400) | User edit + retry |
| Masters | Machine not found | Skip row (CSV import) | Log, continue |
| Sync | Network timeout | Retry with backoff | Eventual consistency |
| Sync | Invalid token | Raise 401 Unauthorized | User re-login |
| Sync | Server validation fails | Raise 400 Bad Request | Log + alert admin |

---

## 🎯 DATA FLOW DIAGRAMS

### Online Inspection Creation
```
Analista Form
    ↓
Pydantic Validation
    ↓
POST /api/inspections
    ↓
InspectionService.register_inspection()
    ├─ validate defect exists
    ├─ validate machine exists
    ├─ create aggregates + value objects
    └─ persist to DB
    ↓
Response: inspection_id
    ↓
Client: Toast + Clear form
    ↓
Ready for next
```

### Offline Inspection Creation → Sync
```
Analista Form (No Network)
    ↓
Service Worker intercepts
    ↓
Store in IndexedDB + Queue
    ↓
Optimistic response (201)
    ↓
UI: "📡 OFFLINE"
    ↓
[Network Detected]
    ↓
Background Sync Loop
    ├─ Attempt 1: POST /api/inspections/sync
    ├─ Attempt 2: (1s delay)
    ├─ Attempt 3: (2s delay)
    ├─ Attempt 4: (4s delay)
    └─ Attempt 5: (8s delay)
    ↓
Success: Update IndexedDB (sync_status = SYNCED)
    ↓
UI: "📡 ONLINE (All synced)"
```

### Approval Flow with Events
```
Jefe QA Decision
    ↓
POST /api/approvals
    ↓
ApprovalService.approve_inspection()
    ├─ Create Approval aggregate
    ├─ Persist to DB
    └─ Publish InspectionApproved event
    ↓
Event Bus
    ↓
NotificationService (subscriber)
    ├─ Send notification to Gerente
    └─ Update dashboard metrics
    ↓
Gerente sees real-time update
```

---

## ✅ BUSINESS LOGIC VALIDATION

- [ ] All value objects are immutable
- [ ] Domain services encapsulate business logic
- [ ] Cross-domain validation happens in services (not controllers)
- [ ] Events enable loose coupling
- [ ] Error handling is explicit (ValueError, custom exceptions)
- [ ] Offline-first sync is idempotent
- [ ] Soft deletes preserve history
- [ ] RBAC enforced at route level
- [ ] Timestamps from server
- [ ] Photo checksums verify integrity

---

**Status**: ✅ BUSINESS LOGIC MODEL DOCUMENTED  
**Ready for**: NFR Requirements & Infrastructure Design
