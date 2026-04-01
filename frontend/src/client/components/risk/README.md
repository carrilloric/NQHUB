# Risk Monitor Components (AUT-355)

## Implementation Status: ⚠️ Work In Progress

This directory contains the core components for the Risk Monitor page.

### Completed Components ✅

1. **RiskGauge.tsx** - Circular gauge with color-coded thresholds
   - <70%: Green (#22c55e)
   - 70-90%: Yellow (#f59e0b) warning
   - >90%: Red (#ef4444) danger with pulse animation
   
2. **GlobalKillSwitchBar.tsx** - Always-visible emergency shutdown bar
   - Red alert bar at top of page
   - "KILL ALL BOTS" button with confirmation modal
   - Requires reason before killing
   
3. **KillSwitchButton.tsx** - Per-bot kill switch
   - Confirmation modal with required reason field
   - Validates input before submission
   
4. **CircuitBreakerStatus.tsx** - Circuit breaker status display
   - Shows active/inactive status
   - Color-coded indicators
   
5. **RiskEventFeed.tsx** - Real-time risk event feed
   - Displays last 5 risk events
   - Updates via WebSocket
   - Color-coded by result (PASSED/REJECTED)

### Pending ⏳

- RiskMonitor.tsx page (main component)
- Test suite (10 tests required)
- WebSocket integration verification
- MSW handlers for mocking

### Next Steps

1. Create RiskMonitor.tsx page that:
   - Uses useWebSocket hook with 'risk' and 'bot' channels
   - Risk channel NEVER throttled (highest priority)
   - Shows kill switch alert modal on KillSwitchEvent
   - Displays bot risk cards with gauges

2. Create tests in `pages/__tests__/RiskMonitor.test.tsx`:
   - test_renders_global_kill_switch_bar
   - test_gauge_green_below_70_percent
   - test_gauge_yellow_between_70_and_90
   - test_gauge_red_above_90_percent
   - test_kill_all_requires_reason
   - test_kill_bot_requires_reason
   - test_circuit_breaker_shows_active_status
   - test_risk_event_feed_updates_on_ws_message
   - test_kill_switch_event_shows_critical_alert
   - test_ws_risk_channel_never_throttled

3. Add route to App.tsx

## WebSocket Integration

Uses `useWebSocket` hook from `@/hooks/useWebSocket.ts`:

```typescript
const { connected, latestRiskCheck, latestKillSwitch } = useWebSocket({
  autoSubscribe: ['risk', 'bot'],
  autoConnect: false,
});
```

Risk channel has **HIGHEST PRIORITY** and is NEVER throttled.

## Dependencies

- @/components/ui/button
- @/components/ui/dialog
- @/components/ui/input
- @/components/ui/label
- @/components/ui/card
- @/hooks/useWebSocket
- @/lib/utils (cn helper)
