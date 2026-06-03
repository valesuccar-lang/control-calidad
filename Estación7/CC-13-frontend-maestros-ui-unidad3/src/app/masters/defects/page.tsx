"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";

interface Defect {
  defect_id: string;
  name: string;
  category: string;
  severity: string;
  status: string;
}

export default function DefectsPage() {
  const [defects, setDefects] = useState<Defect[]>([]);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.get("/api/masters/defects").then((r) => setDefects(r.data.items ?? []));
  }, []);

  const filtered = defects.filter(
    (d) => d.name.toLowerCase().includes(filter.toLowerCase()) || d.category.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Catálogo de Defectos</h1>
      <input value={filter} onChange={(e) => setFilter(e.target.value)}
        placeholder="Filtrar por nombre o categoría..."
        className="w-full border rounded px-3 py-2 mb-4" />
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-100">
            <th className="text-left p-2 border">ID</th>
            <th className="text-left p-2 border">Nombre</th>
            <th className="text-left p-2 border">Categoría</th>
            <th className="text-left p-2 border">Severidad</th>
            <th className="text-left p-2 border">Estado</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((d) => (
            <tr key={d.defect_id} className="hover:bg-gray-50">
              <td className="p-2 border">{d.defect_id}</td>
              <td className="p-2 border">{d.name}</td>
              <td className="p-2 border">{d.category}</td>
              <td className="p-2 border">{d.severity}</td>
              <td className="p-2 border">{d.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-sm text-gray-500 mt-2">{filtered.length} de {defects.length} defectos</p>
    </main>
  );
}
