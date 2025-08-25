// User domain hooks

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { queryKeys } from '@/state';

/**
 * Hook for getting current user profile
 */
export function useUserProfile() {
  return useQuery({
    queryKey: queryKeys.user.profile(),
    queryFn: () => apiClient.getCurrentUser(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook for updating user preferences  
 */
export function useUpdateUserPreferences() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.updateUserPreferences,
    onSuccess: (data) => {
      // Update the user profile cache
      queryClient.setQueryData(queryKeys.user.profile(), data);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.user.all() });
    },
  });
}