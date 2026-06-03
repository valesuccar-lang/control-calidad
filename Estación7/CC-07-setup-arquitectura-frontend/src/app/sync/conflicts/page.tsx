"use client";
import { useEffect, useState } from "react";
import { getPendingInspections, removePendingInspection } from "@/lib/db";
import { detectConflicts, SyncItem } from "@/lib/conflictDetector";

export default function ConflictsPage() {
  const [conflicts, setConflicts] = useState<SyncItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPendingInspections().then(async (pending) => {
      const items = pending.map((p) => ({ id: p.id, data: p.data }));
      const report = await detectConflicts(items);
      setConflicts(report.conflicts);
      setLoading(false);
    });
  }, []);

  const discard = async (id: string) => {
    await removePendingInspection(id);
    setConflicts((prev) => prev.filter((c) => c.id !== id));
  };

  if (loading) return <p className="p-6">Verificando conflictos...</p>;
  if (!conflicts.length) return <p className="p-6 text-green-600">Sin conflictos pendientes.</p>;

  return (
    <main className="max-w-2xl mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Conflictos de Sincronización ({conflicts.length})</h1>
      <ul className="space-y-3">
        {conflicts.map((c) => (
          <li key={c.id} className="border rounded p-4">
            <p className="text-sm font-mono text-gray-600">{c.id}</p>
            <p className="text-sm mt-1">Ya existe en el servidor. ¿Descartar versión local?</p>
            <button onClick={() => discard(c.id)}
              className="mt-2 px-4 py-1 bg-red-600 text-white rounded text-sm">
              Descartar local
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
