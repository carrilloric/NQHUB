/**
 * MSW Request Handlers
 *
 * Central export for all mock API handlers
 */
import { dashboardHandlers } from './handlers/dashboard.handlers';

export const handlers = [
  ...dashboardHandlers,
];
