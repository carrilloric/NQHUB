/**
 * MSW Server Setup for Node.js testing environment
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// This configures a request interception server with the given request handlers
export const server = setupServer(...handlers);
