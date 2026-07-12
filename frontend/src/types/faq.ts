export interface FaqItem {
  id: number;
  question: string;
  answer: string;
  category: string | null;
  keywords: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface FaqUploadResult {
  success: boolean;
  message: string;
  created?: number;
  skipped?: number;
  errors?: Array<{
    row: number;
    error: string;
  }>;
}

