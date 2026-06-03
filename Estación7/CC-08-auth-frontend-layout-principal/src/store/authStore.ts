import { create } from "zustand";
import api from "@/lib/api";

interface AuthState {
  userId: string | null;
  roles: string[];
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  userId: null,
  roles: [],
  accessToken: null,

  login: async (email, password) => {
    const resp = await api.post("/auth/login", { email, password });
    const { access_token, refresh_token, user_id, roles } = resp.data;
    sessionStorage.setItem("access_token", access_token);
    sessionStorage.setItem("refresh_token", refresh_token);
    set({ userId: user_id, roles, accessToken: access_token });
  },

  logout: () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
    set({ userId: null, roles: [], accessToken: null });
  },

  hasRole: (role) => get().roles.includes(role),
}));
