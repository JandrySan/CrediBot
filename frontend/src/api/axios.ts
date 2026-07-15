import axios from "axios";
import { API_BASE_URL } from "../config/api";
import { AuthStorage } from "../services/auth.storage";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use((config) => {
    const token = AuthStorage.getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && window.location.pathname !== "/login") {
            AuthStorage.clear();
            window.location.assign("/login");
        }
        return Promise.reject(error);
    },
);

export default api;
