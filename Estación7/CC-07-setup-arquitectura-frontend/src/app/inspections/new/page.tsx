"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import api from "@/lib/api";

const schema = z.object({
  lote_id: z.string().min(1),
  defect_id: z.string().min(1),
  comment_text: z.string().min(10, "Comentario debe tener al menos 10 caracteres"),
  photo_path: z.string().min(1),
  photo_checksum: z.string().length(64),
  photo_size_kb: z.number().int().min(1).max(500),
  machine_id: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

export default function NewInspectionPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    await api.post("/api/inspections", data);
    alert("Inspección registrada");
  };

  return (
    <main className="max-w-lg mx-auto p-6 space-y-4">
      <h1 className="text-xl font-bold">Nueva Inspección</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        <input {...register("lote_id")} placeholder="ID Lote" className="w-full border rounded px-3 py-2" />
        {errors.lote_id && <p className="text-red-500 text-sm">Requerido</p>}

        <select {...register("defect_id")} className="w-full border rounded px-3 py-2">
          <option value="">Selecciona tipo de defecto</option>
          <option value="TEAR">Rasgadura</option>
          <option value="STAIN">Mancha</option>
          <option value="COLOR_VARIATION">Variación de color</option>
          <option value="WEAVING_ERROR">Error de tejido</option>
          <option value="SHRINKAGE">Encogimiento</option>
        </select>

        <textarea {...register("comment_text")} placeholder="Comentario (mín. 10 caracteres)"
          className="w-full border rounded px-3 py-2" rows={3} />
        {errors.comment_text && <p className="text-red-500 text-sm">{errors.comment_text.message}</p>}

        <input {...register("machine_id")} placeholder="ID Máquina" className="w-full border rounded px-3 py-2" />

        <button type="submit" disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-2 rounded disabled:opacity-50">
          {isSubmitting ? "Guardando..." : "Registrar Inspección"}
        </button>
      </form>
    </main>
  );
}
