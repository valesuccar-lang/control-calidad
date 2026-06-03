/**
 * Conflict detection — compares local queue with server state
 * A conflict occurs when an inspection_id already exists on the server
 * with a different payload than the local queued version.
 */
import api from "@/lib/api";

export interface SyncItem {
  id: string;
  data: Record<string, unknown>;
}

export interface ConflictReport {
  conflicts: SyncItem[];
  safe: SyncItem[];
}

export async function detectConflicts(pending: SyncItem[]): Promise<ConflictReport> {
  const conflicts: SyncItem[] = [];
  const safe: SyncItem[] = [];

  await Promise.all(
    pending.map(async (item) => {
      const remoteId = (item.data as any).inspection_id;
      if (!remoteId) {
        safe.push(item);
        return;
      }
      try {
        await api.get(`/api/inspections/${remoteId}`);
        // Server already has this inspection → conflict
        conflicts.push(item);
      } catch (err: any) {
        if (err?.response?.status === 404) {
          safe.push(item);
        } else {
          // Network error — treat as safe to retry
          safe.push(item);
        }
      }
    })
  );

  return { conflicts, safe };
}
