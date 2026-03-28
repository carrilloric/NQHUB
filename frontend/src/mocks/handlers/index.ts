/**
 * MSW Request Handlers
 */

import { authHandlers } from './auth.handlers';
import { featuresHandlers } from './features.handlers';
import { backtestingHandlers } from './backtesting.handlers';
import { mlHandlers } from './ml.handlers';
import { approvalHandlers } from './approval.handlers';
import { botsHandlers } from './bots.handlers';
import { ordersHandlers } from './orders.handlers';
import { riskHandlers } from './risk.handlers';
import { tradesHandlers } from './trades.handlers';
import { settingsHandlers } from './settings.handlers';
import { strategiesHandlers } from './strategies.handlers';
import { assistantHandlers } from './assistant.handlers';
import { websocketHandlers } from './websocket.handlers';
import { dataExplorerHandlers } from './data-explorer.handlers';

export const handlers = [
  ...authHandlers,
  ...featuresHandlers,
  ...backtestingHandlers,
  ...mlHandlers,
  ...approvalHandlers,
  ...botsHandlers,
  ...ordersHandlers,
  ...riskHandlers,
  ...tradesHandlers,
  ...settingsHandlers,
  ...strategiesHandlers,
  ...assistantHandlers,
  ...websocketHandlers,
  ...dataExplorerHandlers,
];