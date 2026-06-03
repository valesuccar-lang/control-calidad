/**
 * IndexedDB setup using idb library — offline inspection queue
 */
import { openDB, DBSchema, IDBPDatabase } from "idb";

interface OfflineInspection {
  id: string;
  data: Record<string, unknown>;
  createdAt: number;
  syncAttempts: number;
}

interface CCSchema extends DBSchema {
  pending_inspections: {
    key: string;
    value: OfflineInspection;
    indexes: { by_created: number };
  };
}

let _db: IDBPDatabase<CCSchema> | null = null;

export async function getDB(): Promise<IDBPDatabase<CCSchema>> {
  if (_db) return _db;
  _db = await openDB<CCSchema>("control-calidad", 1, {
    upgrade(db) {
      const store = db.createObjectStore("pending_inspections", { keyPath: "id" });
      store.createIndex("by_created", "createdAt");
    },
  });
  return _db;
}

export async function queueInspection(data: Record<string, unknown>): Promise<string> {
  const db = await getDB();
  const id = crypto.randomUUID();
  await db.put("pending_inspections", { id, data, createdAt: Date.now(), syncAttempts: 0 });
  return id;
}

export async function getPendingInspections(): Promise<OfflineInspection[]> {
  const db = await getDB();
  return db.getAllFromIndex("pending_inspections", "by_created");
}

export async function removePendingInspection(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("pending_inspections", id);
}
