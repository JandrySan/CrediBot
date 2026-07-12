import api from "../api/axios";
import type { FaqItem, FaqUploadResult } from "../types/faq";

export const FaqService = {
  async getAll(): Promise<FaqItem[]> {
    const response = await api.get("/api/dashboard/faq");
    return response.data;
  },

  async upload(file: File): Promise<FaqUploadResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/api/dashboard/faq/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  },

  async remove(faqId: number) {
    const response = await api.delete(`/api/dashboard/faq/${faqId}`);
    return response.data;
  },
};

