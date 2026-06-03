/**
 * Background sync queue — flushes pending inspections when back online
 */
import api from "@/lib/api";
import { getPendingInspections, removePendingInspection } from "@/lib/db";

let _running = false;

export async function flushQueue(): Promise<{ synced: number; failed: number }> {
  if (_running) return { synced: 0, failed: 0 };
  _running = true;

  const pending = await getPendingInspections();
  let synced = 0;
  let failed = 0;

  for (const item of pending) {
    try {
      await api.post("/api/inspections", item.data);
      await removePendingInspection(item.id);
      synced++;
    } catch {
      failed++;
    }
  }

  _running = false;
  return { synced, failed };
}

export function registerOnlineListener() {
  if (typeof window === "undefined") return;
  window.addEventListener("online", () => {
    flushQueue().then(({ synced }) => {
      if (synced > 0) console.log(`[sync] ${synced} inspecciones sincronizadas`);
    });
  });
}
