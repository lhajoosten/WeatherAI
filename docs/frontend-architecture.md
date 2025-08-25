# Frontend Architecture (Draft)

This document outlines the new feature-first, modular architecture for the WeatherAI frontend application.

## Overview

The frontend has been refactored from a monolithic structure to a feature-first, Angular-inspired modular architecture that promotes:

- **Separation of concerns** - Clear boundaries between features, core services, and shared utilities
- **Scalability** - Easy to add new features without impacting existing code
- **Maintainability** - Consistent patterns and organized code structure
- **Testability** - Isolated modules that are easy to test
- **Reusability** - Shared components and utilities across features

## Directory Structure

```
src/
├── main.tsx                    # Application entry point
├── App.tsx                     # Main app component (refactored)
├── app/                        # Application-level configuration
│   ├── providers/              # Provider composition
│   │   └── AppProviders.tsx    # All app providers in one place
│   └── routing/                # Application routing
│       └── routes.tsx          # Central route definitions
├── core/                       # Core application services
│   ├── auth/                   # Authentication context and utilities
│   │   └── AuthContext.tsx     # Auth provider and hooks
│   ├── config/                 # Environment configuration
│   │   └── index.ts            # Typed config loader with Zod validation
│   ├── error/                  # Error handling
│   │   └── ErrorBoundary.tsx   # Global error boundary
│   └── http/                   # HTTP client and API utilities
│       └── apiClient.ts        # Typed API client with interceptors
├── shared/                     # Shared utilities and components
│   ├── components/             # Reusable UI components
│   ├── hooks/                  # Reusable React hooks
│   └── utils/                  # Utility functions
│       └── index.ts            # Common utilities (date, debounce, etc.)
├── features/                   # Feature modules (domain-driven)
│   ├── auth/                   # Authentication features
│   │   └── pages/              # Auth-specific pages
│   │       └── LoginPage.tsx   # Login page component
│   ├── locations/              # Location management features
│   │   └── pages/              # Location-specific pages
│   │       └── LocationsPage.tsx
│   ├── digest/                 # Weather digest features
│   │   └── pages/              # Digest-specific pages
│   │       └── DigestPage.tsx
│   ├── analytics/              # Analytics dashboard features
│   │   └── pages/              # Analytics-specific pages
│   │       └── AnalyticsPage.tsx
│   └── rag/                    # RAG knowledge base features
│       └── pages/              # RAG-specific pages
│           └── RagPage.tsx
├── theme/                      # Design system and theming
│   ├── index.ts                # Main theme configuration
│   └── tokens.ts               # Design tokens (colors, fonts, etc.)
├── types/                      # TypeScript type definitions
│   └── api/                    # API-related types
│       └── placeholder.ts      # Placeholder API types
└── tests/                      # Test utilities and setup
    ├── setupTests.ts           # Global test configuration
    └── App.test.tsx            # Basic app smoke tests
```

## Key Principles

### 1. Feature-First Organization

Each feature domain (auth, locations, digest, analytics, rag) has its own directory with:
- **Pages** - React components that represent full pages/routes
- **Components** - Feature-specific UI components (to be added in PR2/PR3)
- **Services** - Feature-specific API calls and business logic (to be added in PR2/PR3)
- **Types** - Feature-specific TypeScript interfaces (to be added in PR2/PR3)
- **Hooks** - Feature-specific React hooks (to be added in PR2/PR3)

### 2. Layered Architecture

- **App Layer** - Application configuration, providers, routing
- **Core Layer** - Cross-cutting concerns (auth, config, error handling, HTTP)
- **Shared Layer** - Reusable components, hooks, and utilities
- **Feature Layer** - Domain-specific functionality
- **Theme Layer** - Design system and visual tokens

### 3. Path Aliases

Clean imports using TypeScript path aliases:
```typescript
import { getConfig } from '@/core/config';
import { ErrorBoundary } from '@/core/error/ErrorBoundary';
import LoginPage from '@/features/auth/pages/LoginPage';
import { formatDate } from '@/shared/utils';
import theme from '@/theme';
```

## Technology Stack

- **React 19** - UI library with modern features
- **TypeScript** - Type safety with strict configuration
- **Chakra UI** - Component library and design system
- **React Router 7** - Client-side routing
- **React Query** - Server state management
- **Vite** - Build tool and dev server
- **Vitest** - Testing framework
- **ESLint + Prettier** - Code linting and formatting
- **Zod** - Runtime type validation for configuration

## Configuration Management

Environment configuration is handled through:
- **Typed schemas** using Zod for validation
- **Centralized config** in `@/core/config`
- **Environment variables** with VITE_ prefix
- **Fallback defaults** for development

Example:
```typescript
import { getConfig } from '@/core/config';

const config = getConfig();
console.log(config.apiUrl); // Typed and validated
```

## API Client

Centralized HTTP client with:
- **Typed methods** for all HTTP verbs
- **Automatic authentication** via interceptors
- **Error handling** with consistent error types
- **Request/response transformation**

Example:
```typescript
import { getApiClient } from '@/core/http/apiClient';

const api = getApiClient();
const user = await api.get<User>('/users/me');
```

## Routing Strategy

- **Centralized route definitions** in `@/app/routing/routes.tsx`
- **Lazy loading ready** structure (to be implemented in PR3)
- **Type-safe route constants** for consistent navigation
- **Feature-based route organization**

## Testing Strategy

- **Unit tests** with Vitest and React Testing Library
- **Global test setup** in `setupTests.ts`
- **Feature-specific tests** co-located with components
- **Smoke tests** for critical application flows

## Migration Status (PR1)

### ✅ Completed in PR1
- [x] New directory structure
- [x] TypeScript configuration with path aliases
- [x] ESLint and Prettier setup
- [x] Core services (config, API client, error boundary)
- [x] Theme configuration
- [x] Routing infrastructure
- [x] Provider composition
- [x] Placeholder pages for all features
- [x] Test setup and basic smoke tests
- [x] Documentation skeleton

### ⏳ Planned for PR2/PR3
- [ ] Migrate existing business logic to feature modules
- [ ] Implement real API integrations
- [ ] Add comprehensive component library
- [ ] Implement lazy loading and code splitting
- [ ] Add advanced error handling and loading states
- [ ] Migrate existing components and contexts
- [ ] Add comprehensive test coverage
- [ ] Finalize design system tokens
- [ ] Add Storybook documentation

## Development Guidelines

### Code Organization
- Keep feature modules independent and focused
- Use barrel exports (index.ts) for clean imports
- Follow consistent naming conventions
- Separate concerns between components, services, and types

### Type Safety
- Use TypeScript strictly - avoid `any` types
- Define interfaces for all component props
- Use Zod for runtime validation where needed
- Leverage path aliases for clean imports

### Performance
- Prepare for lazy loading in route structure
- Use React Query for efficient data caching
- Optimize bundle size with proper tree shaking
- Consider component-level code splitting

### Testing
- Write tests for all new features
- Use Testing Library best practices
- Mock external dependencies appropriately
- Maintain good test coverage

## Next Steps

1. **PR2**: Migrate existing business logic and components to feature modules
2. **PR3**: Implement advanced features, optimization, and comprehensive testing
3. **Future**: Add micro-frontend capabilities if needed for scaling