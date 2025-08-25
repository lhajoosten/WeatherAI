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
│   ├── api/                    # HTTP client and API layer
│   │   ├── client.ts           # Main API client instance
│   │   ├── errors.ts           # Error mapping utilities
│   │   ├── httpClient.ts       # Base HTTP client
│   │   └── queryKeys.ts        # React Query key factories
│   ├── components/             # Reusable UI components
│   ├── config/                 # Runtime configuration
│   ├── hooks/                  # Reusable React hooks
│   ├── i18n/                   # Internationalization
│   ├── lib/                    # Core utility libraries (NEW)
│   │   ├── logger.ts           # Client-side structured logging
│   │   ├── utils.ts            # Common utilities (delay, debounce, etc.)
│   │   ├── http.ts             # HTTP client with abort/retry support
│   │   ├── fetchStream.ts      # Fetch-based streaming for text/event-stream
│   │   ├── hashing.ts          # SHA-256 hashing for client logs
│   │   └── index.ts            # Re-exports all lib modules
│   ├── observability/          # Logging, metrics, tracing
│   ├── theme/                  # Enhanced Chakra theme
│   ├── types/                  # Shared TypeScript definitions
│   ├── ui/                     # Reusable UI primitives
│   └── utils/                  # Legacy utilities (being migrated to lib/)
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
│       ├── components/         # RAG-specific components
│       ├── hooks/              # RAG hooks (useRagStream, useRagAsk)
│       │   ├── useRagAsk.ts    # Traditional RAG queries
│       │   └── useRagStream.ts # Streaming RAG with fetch (NEW)
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

## Streaming Architecture (Wave 1)

### Fetch-Based Streaming

The application implements fetch-based streaming (not EventSource) for text/event-stream responses:

- **createFetchStream** - Core fetch streaming utility with ReadableStream parsing
- **parseFetchSSEMessage** - Server-Sent Events message parser
- **createRagStream** - RAG-specific streaming with typed events (token/done/error)

### HTTP Client with Streaming

Enhanced HTTP client in `shared/lib/http.ts`:
- **Abort controller support** - Cancel requests and streams
- **Retry logic** - Exponential backoff for failed requests
- **Error mapping** - Consistent error handling across the app
- **Streaming method** - Dedicated stream() method for SSE endpoints

### RAG Streaming Hook

```typescript
import { useRagStream } from '@/features/rag/hooks/useRagStream';

function RagComponent() {
  const { startStream, content, isStreaming, stopStream } = useRagStream();
  
  const handleAsk = async () => {
    await startStream({ 
      query: 'What is the weather like?',
      locationId: 'current' 
    });
  };
  
  return (
    <div>
      <button onClick={handleAsk} disabled={isStreaming}>
        Ask RAG
      </button>
      {isStreaming && <div>Streaming: {content}</div>}
    </div>
  );
}
```

### Feature Flags for Streaming

Streaming capabilities are controlled by feature flags:
- `VITE_FEATURE_RAG=1` - Enable RAG features
- `VITE_FEATURE_STREAMING=1` - Enable streaming functionality

### Client-Side Logging & Privacy

Hash-based logging utilities for privacy-safe client logs:
- **sha256()** - Cryptographic hashing for sensitive data
- **hashForLogging()** - Privacy-safe logging of user content
- **createLogCacheKey()** - Consistent cache keys for log correlation

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

## Wave 1 Implementation Status (Current)

### ✅ Completed in Wave 1
- [x] Core shared/lib infrastructure (logger, utils, http, fetchStream, hashing)
- [x] Fetch-based streaming implementation (text/event-stream parsing)
- [x] useRagStream hook with abort controller support
- [x] Typed HTTP client with retry and error mapping
- [x] Client-side hashing utilities for privacy-safe logging
- [x] Feature flag integration for streaming capabilities
- [x] Build system working with TypeScript strict mode
- [x] ESLint configuration updated for browser APIs

### ⏳ Planned for Wave 2/Wave 3
- [ ] Migrate existing business logic to feature modules
- [ ] Complete API integrations using new HTTP client
- [ ] Add comprehensive component library
- [ ] Implement lazy loading and code splitting
- [ ] Add advanced error handling and loading states
- [ ] Migrate remaining legacy components and contexts
- [ ] Add comprehensive test coverage for streaming
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