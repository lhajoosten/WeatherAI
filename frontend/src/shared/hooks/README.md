# Shared Hooks

This directory will contain reusable React hooks that provide common functionality across features.

## Structure (to be implemented in PR2/PR3)

```
hooks/
  api/                # API-related hooks (useQuery wrappers, mutations)
  auth/               # Authentication hooks
  storage/            # LocalStorage, SessionStorage hooks
  ui/                 # UI-related hooks (useDisclosure, useToast wrappers)
  utils/              # Utility hooks (useDebounce, useLocalStorage, etc.)
```

## Guidelines

- Hooks should follow React best practices
- Use TypeScript for all hook parameters and return types
- Include JSDoc documentation
- Consider error handling and loading states
- Use React Query for data fetching hooks
- Export from index.ts files for clean imports

## Examples (to be migrated)

Current hooks in the hooks/ directory will be evaluated and either moved to feature-specific modules or kept as shared hooks during the migration.