"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

interface Approval {
  inspection_id: string;
  lote_id: string;
  defect_id: string;
  comment_text: string;
  photo_path: string;
  analista_id: string;
  check_in: string;
}

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);
  const [selected, setSelected] = useState<Approval | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const { hasRole } = useAuthStore();

  useEffect(() => {
    api.get("/api/approvals/pending").then((r) => setItems(r.data.items ?? []));
  }, []);

  const approve = async (id: string) => {
    await api.post("/api/approvals/approve", { inspection_id: id });
    setItems((prev) => prev.filter((i) => i.inspection_id !== id));
    setSelected(null);
  };

  const reject = async (id: string) => {
    if (rejectReason.length < 10) return alert("Razón debe tener al menos 10 caracteres");
    await api.post("/api/approvals/reject", { inspection_id: id, rejection_reason: rejectReason });
    setItems((prev) => prev.filter((i) => i.inspection_id !== id));
    setSelected(null);
  };

  if (!hasRole("JEFE_QA") && !hasRole("GERENTE")) {
    return <p className="p-6 text-red-500">Sin permisos</p>;
  }

  return (
    <main className="max-w-3xl mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Inspecciones Pendientes ({items.length})</h1>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.inspection_id} className="border rounded p-3 cursor-pointer hover:bg-gray-50"
            onClick={() => setSelected(item)}>
            <p><strong>Lote:</strong> {item.lote_id} — <strong>Defecto:</strong> {item.defect_id}</p>
            <p className="text-sm text-gray-500">{item.comment_text}</p>
          </li>
        ))}
      </ul>

      {selected && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 w-96 space-y-3">
            <h2 className="font-bold">Lote: {selected.lote_id}</h2>
            <img src={selected.photo_path} alt="foto" className="w-full max-h-64 object-contain" />
            <p>{selected.comment_text}</p>
            <textarea value={rejectReason} onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Razón de rechazo (si aplica, mín. 10 chars)"
              className="w-full border rounded px-3 py-2" rows={2} />
            <div className="flex gap-2">
              <button onClick={() => approve(selected.inspection_id)}
                className="flex-1 bg-green-600 text-white py-2 rounded">Aprobar</button>
              <button onClick={() => reject(selected.inspection_id)}
                className="flex-1 bg-red-600 text-white py-2 rounded">Rechazar</button>
              <button onClick={() => setSelected(null)}
                className="flex-1 bg-gray-300 py-2 rounded">Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
