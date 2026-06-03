/**
 * Hook that routes inspection submission through offline queue when no network
 */
import { useState } from "react";
import api from "@/lib/api";
import { queueInspection } from "@/lib/db";

export function useOfflineInspection() {
  const [status, setStatus] = useState<"idle" | "submitting" | "queued" | "success" | "error">("idle");

  const submit = async (data: Record<string, unknown>) => {
    setStatus("submitting");
    if (!navigator.onLine) {
      await queueInspection(data);
      setStatus("queued");
      return { queued: true };
    }
    try {
      const resp = await api.post("/api/inspections", data);
      setStatus("success");
      return { queued: false, data: resp.data };
    } catch {
      // Fall back to offline queue on network error
      await queueInspection(data);
      setStatus("queued");
      return { queued: true };
    }
  };

  return { submit, status };
}
