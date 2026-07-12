import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { FaqService } from "../services/faq.service";

export function useFaqs() {
  return useQuery({
    queryKey: ["faqs"],
    queryFn: FaqService.getAll,
  });
}

export function useUploadFaqs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: FaqService.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["faqs"] });
    },
  });
}

export function useDeleteFaq() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: FaqService.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["faqs"] });
    },
  });
}

