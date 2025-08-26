import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { digestService } from '@/shared/api/services';

// React Query keys for digest data
export const digestQueryKeys = {
  morning: (date?: string) => ['digest', 'morning', date],
  metrics: () => ['digest', 'metrics'],
};

/**
 * Hook for fetching morning digest
 */
export const useMorningDigest = (date?: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: digestQueryKeys.morning(date),
    queryFn: () => digestService.getMorningDigest(date),
    enabled,
    staleTime: 30 * 60 * 1000, // 30 minutes
    retry: 2,
  });
};

/**
 * Hook for regenerating morning digest
 */
export const useRegenerateMorningDigest = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ force = true, date }: { force?: boolean; date?: string } = {}) =>
      digestService.regenerateMorningDigest(force, date),
    onSuccess: (data, variables) => {
      // Invalidate and update the digest cache
      queryClient.invalidateQueries({ queryKey: ['digest', 'morning'] });
      
      // Update the specific digest cache
      if (variables?.date) {
        queryClient.setQueryData(
          digestQueryKeys.morning(variables.date),
          data
        );
      }
    },
  });
};

/**
 * Hook for fetching digest metrics (for debugging)
 */
export const useDigestMetrics = (enabled: boolean = false) => {
  return useQuery({
    queryKey: digestQueryKeys.metrics(),
    queryFn: () => digestService.getMetrics(),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook that combines digest fetching with automatic regeneration logic
 */
export const useSmartDigest = (date?: string) => {
  const {
    data: digest,
    isLoading,
    error,
    refetch
  } = useMorningDigest(date);
  
  const regenerateMutation = useRegenerateMorningDigest();
  
  const regenerate = (force: boolean = true) => {
    return regenerateMutation.mutateAsync({ force, date });
  };
  
  // Check if digest is stale (older than 4 hours for today's digest)
  const isStale = digest && !date && digest.cache_meta.generated_at ? 
    (new Date().getTime() - new Date(digest.cache_meta.generated_at).getTime()) > (4 * 60 * 60 * 1000) : 
    false;
  
  return {
    digest,
    isLoading: isLoading || regenerateMutation.isPending,
    error: error || regenerateMutation.error,
    isStale,
    regenerate,
    refetch,
    isRegenerating: regenerateMutation.isPending,
  };
};