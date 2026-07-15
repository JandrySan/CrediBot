const TOKEN_KEY = "credibot.dashboard.token";
const ROLE_KEY = "credibot.dashboard.role";

export const AuthStorage = {
  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  },

  save(token: string, role: string) {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(ROLE_KEY, role);
  },

  clear() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(ROLE_KEY);
  },
};
