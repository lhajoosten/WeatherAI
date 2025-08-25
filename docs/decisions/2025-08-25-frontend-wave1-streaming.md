# ADR-004: Frontend Wave 1 - Fetch Streaming & Core Infrastructure

## Status
Accepted

## Date
2025-08-25

## Context

Frontend Wave 1 refactor aimed to establish foundational infrastructure for streaming capabilities while maintaining minimal changes to existing UI. The backend is implementing RAG streaming pipeline (Phase 4), requiring frontend to support text/event-stream responses from `/api/rag/stream` POST endpoints.

### Requirements
- Implement fetch-based streaming (NOT EventSource) for text/event-stream parsing
- Create typed HTTP client with abort controller and error mapping
- Add client-side hashing utilities for privacy-safe logging
- Establish shared/lib infrastructure for reusable utilities
- Implement useRagStream hook for RAG streaming functionality
- Maintain feature flag integration for progressive rollout

### Constraints
- Minimal UI changes (structure realignment only)
- Must work with existing AppProviders and feature flag system
- TypeScript strict mode compliance required
- Build and linting must pass without breaking existing functionality

## Decision

### Core Infrastructure

**Shared Library Modules** (`shared/lib/`)
- `logger.ts` - Structured client-side logging with levels
- `utils.ts` - Common utilities (delay, debounce, generateId, clamp, etc.)
- `http.ts` - HTTP client with abort, retry, and error mapping
- `fetchStream.ts` - Fetch-based streaming for text/event-stream parsing
- `hashing.ts` - SHA-256 hashing utilities for privacy-safe logging

### Streaming Implementation

**Fetch-Based Streaming** (chosen over EventSource)
- `createFetchStream()` - Core streaming utility using fetch ReadableStream
- `parseFetchSSEMessage()` - Parse SSE format from fetch responses
- `parseRagStreamMessage()` - RAG-specific event parsing (token/done/error)
- `createRagStream()` - Higher-level RAG streaming with typed events

**HTTP Client Enhancement**
- AbortController integration for request/stream cancellation
- Retry logic with exponential backoff
- Consistent error mapping to AppError types
- Dedicated `stream()` method for SSE endpoints

### RAG Integration

**useRagStream Hook**
- State management for streaming content
- Feature flag integration (VITE_FEATURE_RAG, VITE_FEATURE_STREAMING)
- Error handling and completion callbacks
- AbortController support for stopping streams

### Privacy & Logging

**Client-Side Hashing**
- SHA-256 hashing using Web Crypto API
- `hashForLogging()` for privacy-safe content logging
- `createLogCacheKey()` for consistent cache key generation
- Short hash utilities for correlation without exposing content

## Alternatives Considered

### Streaming Approach
- **EventSource vs Fetch**: Chose fetch for better control over headers, body, and error handling
- **WebSocket vs SSE**: SSE chosen for better HTTP integration and simpler backend implementation
- **axios vs fetch**: Chose fetch for smaller bundle size and native browser support

### Architecture Patterns
- **Hook vs Context**: Chose hook-based approach for better component integration
- **Service vs Utility**: Chose utility functions for better tree-shaking and composability

## Consequences

### Positive
- ✅ Establishes solid foundation for streaming functionality
- ✅ Type-safe streaming with abort controller support
- ✅ Privacy-safe logging without exposing user content
- ✅ Minimal changes to existing UI components
- ✅ Feature flag integration allows progressive rollout
- ✅ Consistent error handling across HTTP and streaming
- ✅ Build and TypeScript compilation working correctly

### Negative
- ❌ Additional complexity in shared/lib structure
- ❌ Need to update ESLint config for browser APIs
- ❌ GitIgnore conflicts required manual resolution
- ❌ Some pre-existing tests still failing (App.test.tsx, useEventStream.test.ts)

### Neutral
- 📋 Documentation updated to reflect new architecture
- 📋 Ready for Wave 2 migration of existing business logic
- 📋 Streaming capabilities implemented but UI integration pending

## Implementation Notes

### Key Files Added
```
shared/lib/
├── logger.ts           # 2.5KB - Structured logging
├── utils.ts            # 4.6KB - Common utilities  
├── http.ts             # 5.4KB - HTTP client with abort/retry
├── fetchStream.ts      # 6.8KB - Fetch streaming implementation
├── hashing.ts          # 3.0KB - SHA-256 hashing utilities
└── index.ts            # 391B - Re-exports with conflict resolution

features/rag/hooks/
└── useRagStream.ts     # 4.2KB - RAG streaming hook
```

### Environment Variables
- `VITE_FEATURE_RAG=1` - Enable RAG functionality
- `VITE_FEATURE_STREAMING=1` - Enable streaming features

### Integration Points
- Backend streaming endpoint: `POST /api/rag/stream`
- Response format: `text/event-stream` with JSON payloads
- Event types: `start`, `token`, `done`, `error`
- Feature flags coordinate with backend capabilities

### Testing Status
- ✅ TypeScript compilation passes
- ✅ Build process completes successfully  
- ✅ ESLint mostly clean (some pre-existing issues remain)
- ❌ App.test.tsx failing due to content expectations
- ❌ useEventStream.test.ts failing (pre-existing SSE tests)

## Future Considerations

### Wave 2 Planning
- Migrate existing API calls to use new HTTP client
- Complete UI integration with streaming functionality
- Add comprehensive test coverage for streaming
- Implement real backend integration testing

### Performance Optimization
- Code splitting for streaming features
- Bundle size optimization for lib modules
- Memory management for long-running streams

### Security Enhancements
- Rate limiting integration for streaming endpoints
- Enhanced content validation before hashing
- Audit logging for streaming sessions

---

**Decision makers**: Frontend Team  
**Stakeholders**: Backend Team, QA, Product  
**Review**: Should be reviewed after Wave 2 implementation and first production streaming deployment