# ADR-001: Frontend Foundation Architecture (PR2)

## Status
Accepted

## Date
2025-08-25

## Context
Following the initial feature-first refactor in PR1, PR2 implements the foundational layer to provide:
- Consistent theming and UI component library
- Type-safe API client with error normalization  
- Reactive data patterns with RemoteData types
- Observability and metrics scaffolding
- Internationalization support
- Testing infrastructure with MSW
- Storybook documentation system

The goal is to establish robust patterns and infrastructure that future feature development can build upon.

## Decision

### Theming & UI Components
- **Chakra UI**: Selected for mature component library with excellent TypeScript support and theming system
- **Enhanced Theme**: Extended default Chakra theme with:
  - Custom color palettes (primary, gray scales)
  - Consistent design tokens (spacing, typography, shadows)
  - Light/dark mode support with system preference detection
  - localStorage persistence for theme preference
- **Shared UI Library**: Created reusable components (Button, Card, Panel, Skeleton, ErrorState, LoadingState, ToggleThemeButton) following Chakra patterns

### Data Management Patterns  
- **RemoteData Types**: Implemented discriminated union pattern for async operation states
  - `{ kind: 'idle' | 'loading' | 'success' | 'error' }`
  - Type-safe state transitions with type guards
  - Factory functions for consistent state creation
- **AppError Normalization**: Centralized error mapping from HTTP responses to consistent AppError types
  - Network, timeout, client (4xx), server (5xx), unknown error kinds
  - Status code and detail preservation where available

### HTTP Client & API Layer
- **Custom HTTP Client**: Built on fetch API instead of axios for lighter footprint
  - 10-second configurable timeout with AbortController
  - Automatic JSON parsing with fallback to text
  - Bearer token injection from localStorage
  - Error mapping to AppError types
- **React Query Integration**: Enhanced default configuration
  - Smart retry logic: 2 retries for network/5xx errors, none for 4xx
  - 5-minute stale time, 10-minute garbage collection
  - Centralized query keys with consistent patterns

### Observability & Monitoring
- **Development Logging**: Console-based logger with structured messages
- **Metrics Scaffolding**: recordMetric function for future analytics integration
- **Performance Timing**: withTiming wrapper using Performance API marks
- **React Tracing**: useTrace hook for component lifecycle monitoring
- **Future-Ready**: FEATURE_ANALYTICS_UPLOAD flag for backend integration

### Configuration Management
- **Zod Schema Validation**: Runtime validation of environment configuration
- **Multi-Source Config**: window.__APP_CONFIG__ for runtime injection, fallback to build-time env vars
- **Feature Flags**: FEATURE_RAG, FEATURE_ANALYTICS_UPLOAD for progressive feature enablement
- **Locale Support**: DEFAULT_LOCALE configuration with en/nl support

### Internationalization
- **i18next**: Lightweight i18n with React integration
- **Namespace Organization**: common, ui, errors namespaces for structured translations
- **Context Provider**: I18nProvider with locale switching capability
- **useT Hook**: Consistent translation interface across components

### Testing Infrastructure
- **MSW (Mock Service Worker)**: API mocking for tests and Storybook
- **Handlers**: Mock endpoints for locations, RAG, meta, health
- **Test Utilities**: Type guards, error mapping, configuration validation
- **Component Testing**: React Testing Library with Chakra providers

### Documentation & Development Tools
- **Storybook**: Component documentation with theme switching
- **Story Coverage**: UI components, RemoteData patterns, interactive examples
- **Development Workflow**: Stories showcase component variations and states

## Consequences

### Positive
- **Type Safety**: Comprehensive TypeScript coverage with runtime validation
- **Developer Experience**: Storybook for component development, MSW for testing
- **Scalability**: Modular architecture ready for feature team development
- **Maintainability**: Consistent patterns, centralized error handling, shared utilities
- **Performance**: Optimized HTTP client, smart caching, lazy loading preparation

### Negative  
- **Bundle Size**: Increased from i18next, MSW dev dependencies, Storybook
- **Learning Curve**: Team needs familiarity with RemoteData patterns, new abstractions
- **Early Optimization**: Some patterns may be over-engineered for current needs

### Mitigation Strategies
- Bundle analysis and code splitting for production builds
- Documentation and examples for new patterns
- Progressive adoption - existing code can gradually migrate to new patterns

## Implementation Notes

### Directory Structure
```
src/
├── shared/
│   ├── api/           # HTTP client, error mapping, query keys
│   ├── ui/            # Reusable components
│   ├── types/         # RemoteData, AppError definitions  
│   ├── config/        # Runtime configuration
│   ├── observability/ # Logging, metrics, tracing
│   ├── i18n/          # Internationalization
│   ├── theme/         # Enhanced Chakra theme
│   └── lib/           # Utility functions
├── app/providers/     # Enhanced provider composition
├── tests/             # Test utilities, MSW setup
└── features/          # Placeholder for future feature modules
```

### Key Patterns
- Provider composition in strict dependency order
- Factory functions for state creation (remoteData.*)
- Centralized query keys for cache management
- Discriminated unions for type-safe state handling

## Future Considerations
- Code splitting strategy for feature modules
- Backend analytics integration when FEATURE_ANALYTICS_UPLOAD enabled
- Advanced error recovery patterns
- Performance monitoring integration
- A11y enhancements for UI components

---

**Decision makers**: Frontend Team  
**Stakeholders**: Full development team, QA, DevOps  
**Review**: This decision should be reviewed after 2-3 feature implementations to assess effectiveness.