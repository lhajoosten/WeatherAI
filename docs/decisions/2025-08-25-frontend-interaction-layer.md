# ADR-003: Frontend Interaction Layer & Streaming Scaffold (PR3)

## Status
Accepted

## Date
2025-08-25

## Context

Following the Frontend Foundation implementation in PR2, we needed to implement the interaction layer patterns, streaming infrastructure, and clean up legacy code to prepare for advanced features like RAG AI assistance. The main challenges addressed:

- **Interaction Layer**: Need for consistent, typed API client with error mapping aligned to backend Problem+JSON format
- **Streaming Infrastructure**: Required SSE (Server-Sent Events) support for real-time AI responses and live updates
- **Feature Gating**: Need for runtime feature flag system to enable/disable experimental features like RAG
- **Legacy Cleanup**: Multiple API client implementations and inconsistent patterns from earlier iterations
- **Developer Experience**: Required comprehensive testing utilities and demo pages for development workflow

## Decision

We implemented a comprehensive interaction layer with the following key components:

### 1. Enhanced Directory Structure
```
src/
├── api/              # Typed API client + streaming infrastructure
│   ├── client.ts     # Enhanced API client with domain methods
│   ├── endpoints.ts  # Centralized endpoint definitions
│   └── streaming.ts  # SSE infrastructure and EventSource wrapper
├── hooks/            # Cross-cutting React hooks
│   └── index.ts      # useEventStream, useDebounce, localStorage hooks
├── state/            # React Query setup and query key factory
├── config/           # Feature flags and runtime configuration
├── components/       # Global UI components (ErrorBoundary, etc.)
└── test-utils/       # Testing utilities with provider wrappers
```

### 2. Interaction Layer Components

**Enhanced API Client**
- Type-safe methods for all backend endpoints (locations, weather, user, RAG)
- Automatic error transformation from fetch/HTTP errors to AppError discriminated union
- Consistent error handling aligned with RFC 7807 Problem Details format
- Built on existing HttpClient from shared/api for consistency

**React Query Integration**
- Centralized QueryClient configuration with sensible defaults
- Type-safe query key factory with hierarchical structure
- Domain-oriented hooks (useLocations, useUserProfile, useRagAsk)
- Automatic retry logic with smart failure handling

### 3. Streaming Infrastructure

**useEventStream Hook**
- Generic Server-Sent Events management with React state integration
- Automatic reconnection with exponential backoff
- Message parsing with JSON detection and heartbeat filtering
- Cleanup and abort controller support for memory safety

**EventStreamManager Class**
- Lower-level SSE management for complex scenarios
- Configurable retry policies and error handling
- Support for custom message parsing and event filtering

### 4. Feature Flag System

**Runtime Configuration**
- Environment variable driven: `VITE_FEATURE_RAG=1`, `VITE_FEATURE_STREAMING=1`
- TypeScript-safe flag definitions with useFeatureFlags hook
- Component-level gating for experimental features

### 5. RAG UI Skeleton

**ChatShell Component**
- Complete chat interface with message history and input
- Streaming response simulation with realistic typing animation
- Source citation placeholders and message timestamps
- Accessibility features (ARIA live regions, focus management)

**StreamingIndicator Component**
- Visual feedback during streaming responses
- Accessible loading states with screen reader support

### 6. Error Handling & Observability

**Global ErrorBoundary**
- React error boundary with development error details
- User-friendly error messages and recovery actions
- Error logging integration with structured data

**Enhanced Logging**
- Environment-aware log levels (VITE_LOG_LEVEL)
- Structured logging with timestamps and context
- Integration with browser console and future analytics backend

### 7. Testing Infrastructure

**Test Utilities**
- Custom render function with React Query and Chakra UI providers
- Test QueryClient with disabled retries and caching
- Hook testing utilities with proper cleanup

**Component Tests**
- useEventStream hook tests with EventSource mocking
- Demo tests for streaming and error scenarios

### 8. Legacy Cleanup

**Removed Components**
- Old App.old.tsx file (no longer referenced)
- Legacy core/http/apiClient.ts (Axios-based, replaced by fetch-based client)
- Placeholder TypeScript files

**Consolidated Exports**
- Resolved export conflicts between api/ and types/ modules
- Cleaner shared/ module exports with explicit naming

## Alternatives Considered

### API Client Approach
- **Axios vs Fetch**: Chose fetch for smaller bundle size and native browser support
- **Class vs Function API**: Chose class-based ApiClient for better organization and extensibility
- **Direct vs Wrapper**: Chose wrapper approach to maintain consistency with existing HttpClient

### Streaming Implementation  
- **WebSocket vs SSE**: Chose SSE for simpler implementation and better HTTP/browser integration
- **Custom vs Native EventSource**: Chose wrapper around native EventSource for broader browser support
- **Hook vs Context**: Chose hook-based approach for simpler component integration

### State Management
- **Zustand vs React Query**: Chose React Query for server state, keeping client state minimal
- **Context vs Props**: Chose hook-based approach over context providers for better performance

## Consequences

### Positive
- **Type Safety**: Comprehensive TypeScript coverage with strict error handling
- **Developer Experience**: Rich testing utilities, demo pages, and clear patterns
- **Scalability**: Modular architecture ready for multiple feature teams
- **Performance**: Efficient streaming with proper cleanup and memory management
- **Maintainability**: Clear separation of concerns and consistent patterns

### Negative
- **Bundle Size**: Increased from React Query, streaming infrastructure, and comprehensive error handling
- **Complexity**: More abstractions may have learning curve for new team members
- **Feature Flag Management**: Runtime flags need careful coordination with backend feature flags

### Mitigation Strategies
- Bundle analysis and code splitting planned for performance optimization
- Comprehensive documentation and examples provided
- Feature flag system designed for easy coordination with backend flags

## Implementation Notes

### Key Files Added
```
src/api/client.ts           # Enhanced typed API client
src/api/streaming.ts        # SSE infrastructure
src/hooks/index.ts          # Cross-cutting React hooks  
src/state/index.ts          # React Query setup
src/config/flags.ts         # Feature flag system
src/components/error/       # Error boundary components
src/features/rag/           # RAG UI skeleton
src/test-utils/            # Testing infrastructure
```

### Environment Variables
```bash
VITE_FEATURE_RAG=1              # Enable RAG chat interface
VITE_FEATURE_STREAMING=1        # Enable streaming features  
VITE_FEATURE_ANALYTICS_UPLOAD=1 # Enable analytics
VITE_LOG_LEVEL=debug           # Set logging level
```

### Integration Points
- Backend endpoints aligned with API_ENDPOINTS definitions
- Error handling expects RFC 7807 Problem Details from backend
- Streaming endpoints expect SSE format with JSON payloads
- Feature flags should coordinate with backend feature gates

## Future Considerations

### Performance Optimization
- Code splitting for RAG and streaming features
- React Query devtools integration for development
- Bundle size analysis and optimization

### Feature Enhancements  
- Real SSE endpoint integration when backend streaming available
- Advanced error recovery with user actions
- Analytics integration for usage tracking
- A11y enhancements and testing

### Backend Integration
- Alignment with backend Phase 3c error format
- Real RAG endpoint integration
- Streaming response format standardization

---

**Decision makers**: Frontend Team  
**Stakeholders**: Full development team, QA, Backend team  
**Review**: Should be reviewed after RAG backend integration and first production deployment