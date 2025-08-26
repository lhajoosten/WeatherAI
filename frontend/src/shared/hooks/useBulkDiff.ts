/**
 * Hook for computing bulk add/remove differences between old and new ID arrays.
 * Useful for bulk membership operations.
 */
export function useBulkDiff(oldIds: number[], newIds: number[]): { add: number[]; remove: number[] } {
  const oldSet = new Set(oldIds);
  const newSet = new Set(newIds);
  
  const add = newIds.filter(id => !oldSet.has(id));
  const remove = oldIds.filter(id => !newSet.has(id));
  
  return { add, remove };
}

export default useBulkDiff;