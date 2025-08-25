# Shared Components

This directory will contain reusable UI components that are used across multiple features.

## Structure (to be implemented in PR2/PR3)

```
components/
  ui/                 # Basic UI components (Button, Input, Card, etc.)
  forms/              # Form-related components
  layout/             # Layout components (Header, Sidebar, etc.)
  charts/             # Data visualization components
  maps/               # Map-related components
  feedback/           # Loading, error, success components
```

## Guidelines

- Components should be feature-agnostic and reusable
- Use TypeScript interfaces for all props
- Follow Chakra UI patterns and design system tokens
- Include JSDoc documentation for public APIs
- Export from index.ts files for clean imports

## Examples (to be migrated)

Current components like Layout, ModernAuthForm, LocationsView, etc. will be refactored and moved to appropriate feature modules or shared components during the migration.