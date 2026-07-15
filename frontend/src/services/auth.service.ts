import api from "../api/axios";
import { AuthStorage } from "./auth.storage";

type AuthConfig = { enabled: boolean };
type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  role: "admin" | "advisor";
};

export const AuthService = {
  async getConfig(): Promise<AuthConfig> {
    const response = await api.get<AuthConfig>("/api/auth/config");
    return response.data;
  },

  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>("/api/auth/token", {
      username,
      password,
    });
    AuthStorage.save(response.data.access_token, response.data.role);
    return response.data;
  },

  logout() {
    AuthStorage.clear();
  },
};
