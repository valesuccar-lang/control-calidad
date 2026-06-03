"use client";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import api from "@/lib/api";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"];

export default function AnalyticsPage() {
  const [defectData, setDefectData] = useState<{ name: string; count: number }[]>([]);
  const [machineData, setMachineData] = useState<{ name: string; count: number }[]>([]);

  useEffect(() => {
    // In production these would be dedicated analytics endpoints
    api.get("/api/inspections?limit=1000").then((r) => {
      const items = r.data.items ?? [];
      const byDefect = items.reduce((acc: Record<string, number>, i: any) => {
        acc[i.defect_id] = (acc[i.defect_id] ?? 0) + 1;
        return acc;
      }, {});
      setDefectData(Object.entries(byDefect).map(([name, count]) => ({ name, count: count as number })));

      const byMachine = items.reduce((acc: Record<string, number>, i: any) => {
        acc[i.machine_id] = (acc[i.machine_id] ?? 0) + 1;
        return acc;
      }, {});
      setMachineData(Object.entries(byMachine).map(([name, count]) => ({ name, count: count as number })));
    });
  }, []);

  return (
    <main className="max-w-5xl mx-auto p-6 space-y-8">
      <h1 className="text-xl font-bold">Análisis de Defectos</h1>

      <section>
        <h2 className="text-lg font-semibold mb-2">Defectos por tipo</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={defectData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Defectos por máquina</h2>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={machineData} dataKey="count" nameKey="name" outerRadius={100} label>
              {machineData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </section>
    </main>
  );
}
