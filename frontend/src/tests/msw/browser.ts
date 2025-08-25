import { setupWorker } from 'msw/browser';

import { handlers } from './handlers';

// Setup worker for browser environment (Storybook)
export const worker = setupWorker(...handlers);