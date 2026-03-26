# Sidebar Navigation Structure

Complete guide to NQHUB's sidebar navigation architecture, routes, and implementation.

## Table of Contents

- [Overview](#overview)
- [Navigation Hierarchy](#navigation-hierarchy)
- [Route Mappings](#route-mappings)
- [Translation Keys](#translation-keys)
- [Implementation Details](#implementation-details)
- [Adding New Sections](#adding-new-sections)
- [Role-Based Access](#role-based-access)

---

## Overview

NQHUB's sidebar navigation uses **React Router 6** with a hierarchical structure organized by functional modules. The navigation supports:

- **Visual Grouping**: Sections can have group labels for better organization
- **Role-Based Access**: Certain items only visible to specific user roles
- **i18n Support**: All labels fully translatable (English/Spanish)
- **Collapsed Mode**: Sidebar can collapse to icon-only view
- **Active State Indicators**: Visual feedback for current route

**Key Files**:
- `frontend/src/client/components/layout/Sidebar.tsx` - Sidebar component
- `frontend/src/client/App.tsx` - Route definitions
- `frontend/src/client/locales/en.json` - English translations
- `frontend/src/client/locales/es.json` - Spanish translations

---

## Navigation Hierarchy

### Visual Structure

```
NQHUB SIDEBAR
│
├── Dashboard (/)
│
├── ┌─ DATA MODULE ─────────────────┐  ← Visual group label
│   └─ Data Module (/data)            ← Single entry with 3 internal tabs
│       ├─ Data Ingest & ETL          ← Tab within /data page
│       ├─ Charts                     ← Tab within /data page
│       └─ Pattern Detection          ← Tab within /data page
│
├── Statistical Analysis (/statistical-analysis)
│   ├─ Exploratory Data Analysis      ← Tab within page
│   ├─ Unsupervised Learning          ← Tab within page
│   └─ Linear Regression              ← Tab within page
│
├── Backtesting Rule-Based (/backtesting/rule-based)
│
├── Backtesting AI (/backtesting/ai)
│
├── BOT Module (/bot) [trader/admin only]
│
├── Settings (/settings)
│
├── Help (/help)
│
└── Admin Section [admin only]
    ├─ User Management (/admin/users)
    └─ Invitations (/admin/invitations)
```

### Key Architectural Decisions

1. **Data Module Consolidation** (December 2025):
   - **Before**: Separate entries for "Data Ingest & ETL" and "Charts"
   - **After**: Single "Data Module" entry with 3 internal tabs
   - **Reason**: Eliminated duplication, cleaner navigation

2. **Statistical Analysis Independence** (December 2025):
   - **Before**: "Data Analysis" tab inside Data Module
   - **After**: Independent "Statistical Analysis" section
   - **Reason**: Distinct functionality deserves standalone section

3. **Backtesting Split** (December 2025):
   - **Before**: Single "Backtesting" entry
   - **After**: "Backtesting Rule-Based" and "Backtesting AI"
   - **Reason**: Different methodologies and target users

---

## Route Mappings

### Complete Route Table

| Route Path | Component | Page Title | Access |
|------------|-----------|------------|--------|
| `/` | Index.tsx | Landing Page | Public |
| `/dashboard` | Dashboard.tsx | Dashboard | Protected |
| `/data` | DataModule.tsx | Data Module | Protected |
| `/statistical-analysis` | StatisticalAnalysis.tsx | Statistical Analysis | Protected |
| `/backtesting/rule-based` | (Placeholder) | Backtesting Rule-Based | Protected |
| `/backtesting/ai` | (Placeholder) | Backtesting AI | Protected |
| `/bot` | (Placeholder) | BOT Module | Protected (trader/admin) |
| `/settings` | (Placeholder) | Settings | Protected |
| `/help` | (Placeholder) | Help | Protected |
| `/admin/users` | (Placeholder) | User Management | Protected (admin) |
| `/admin/invitations` | (Placeholder) | Invitations | Protected (admin) |

### Internal Tabs (Not in Sidebar)

#### Data Module (`/data`)
- **Tab**: `ingest` - Data Ingest & ETL section
- **Tab**: `charts` - Multi-chart viewer with indicators
- **Tab**: `patterns` - Pattern Detection (FVG, LP, OB)

#### Statistical Analysis (`/statistical-analysis`)
- **Tab**: `eda` - Exploratory Data Analysis
- **Tab**: `unsupervised` - Unsupervised Learning
- **Tab**: `regression` - Linear Regression

---

## Translation Keys

### Navigation Labels (en.json)

```json
{
  "nav": {
    "dashboard": "Dashboard",
    "dataModule": "Data Module",
    "dataModuleLabel": "DATA MODULE",
    "statisticalAnalysis": "Statistical Analysis",
    "backtestingRules": "Backtesting Rule-Based",
    "backtestingAI": "Backtesting AI",
    "botModule": "BOT Module",
    "settings": "Settings",
    "help": "Help",
    "userManagement": "User Management",
    "invitations": "Invitations"
  }
}
```

### Navigation Labels (es.json)

```json
{
  "nav": {
    "dashboard": "Dashboard",
    "dataModule": "Módulo de Datos",
    "dataModuleLabel": "MÓDULO DE DATOS",
    "statisticalAnalysis": "Análisis Estadístico",
    "backtestingRules": "Backtesting Basado en Reglas",
    "backtestingAI": "Backtesting AI",
    "botModule": "Módulo BOT",
    "settings": "Configuración",
    "help": "Ayuda",
    "userManagement": "Gestión de Usuarios",
    "invitations": "Invitaciones"
  }
}
```

### Usage Pattern

```typescript
import { useI18n } from '@/state/app';

const { t } = useI18n();

// Regular label
const label = t("nav.dashboard"); // "Dashboard" (en) or "Dashboard" (es)

// Group label (uppercase tracking)
const groupLabel = t("nav.dataModuleLabel"); // "DATA MODULE" or "MÓDULO DE DATOS"
```

---

## Implementation Details

### Sidebar Component Structure

**Location**: `frontend/src/client/components/layout/Sidebar.tsx`

```typescript
export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const ui = useUI();

  const items = [
    { to: "/dashboard", icon: Home, label: t("nav.dashboard"), visible: true },
    {
      to: "/data",
      icon: TrendingUp,
      label: t("nav.dataModule"),
      visible: true,
      groupLabel: t("nav.dataModuleLabel"), // Optional group label
    },
    {
      to: "/statistical-analysis",
      icon: Calculator,
      label: t("nav.statisticalAnalysis"),
      visible: true,
    },
    {
      to: "/backtesting/rule-based",
      icon: FileCode,
      label: t("nav.backtestingRules"),
      visible: true,
    },
    {
      to: "/backtesting/ai",
      icon: Brain,
      label: t("nav.backtestingAI"),
      visible: true,
    },
    {
      to: "/bot",
      icon: Bot,
      label: t("nav.botModule"),
      visible: user?.role === "trader" || user?.role === "admin", // Role-based
    },
    { to: "/settings", icon: Cog, label: t("nav.settings"), visible: true },
    { to: "/help", icon: HelpCircle, label: t("nav.help"), visible: true },
  ];

  return (
    <aside className={cn(/* ... */, ui.sidebarCollapsed ? "w-16" : "w-64")}>
      <nav>
        {items.filter((i) => i.visible).map(({ to, icon: Icon, label, groupLabel }) => (
          <React.Fragment key={to}>
            {/* Group Label */}
            {groupLabel && !ui.sidebarCollapsed && (
              <div className="mt-4 mb-2 px-3 text-[0.6rem] font-bold uppercase tracking-[0.3em] text-muted-foreground/50">
                {groupLabel}
              </div>
            )}
            {/* Nav Link */}
            <NavLink to={to} className={({ isActive }) => cn(/* ... */)}>
              {({ isActive }) => (
                <>
                  <span className={cn(/* Active indicator */)} />
                  <Icon className={cn(/* Icon styles */)} />
                  {!ui.sidebarCollapsed && <span>{label}</span>}
                </>
              )}
            </NavLink>
          </React.Fragment>
        ))}
        {/* Admin-only section */}
        {user?.role === "admin" && (
          <>
            <NavLink to="/admin/users">{/* User Management */}</NavLink>
            <NavLink to="/admin/invitations">{/* Invitations */}</NavLink>
          </>
        )}
      </nav>
    </aside>
  );
};
```

### Route Configuration

**Location**: `frontend/src/client/App.tsx`

```typescript
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>
        {/* Public */}
        <Route path="/" element={<Index />} />

        {/* Protected Routes */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/data" element={<ProtectedRoute><DataModule /></ProtectedRoute>} />
        <Route path="/statistical-analysis" element={<ProtectedRoute><StatisticalAnalysis /></ProtectedRoute>} />
        <Route path="/backtesting/rule-based" element={<ProtectedRoute><WithLayout title="Backtesting Rule-Based" /></ProtectedRoute>} />
        <Route path="/backtesting/ai" element={<ProtectedRoute><WithLayout title="Backtesting AI" /></ProtectedRoute>} />
        <Route path="/bot" element={<ProtectedRoute><WithLayout title="BOT Module" /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><WithLayout title="Settings" /></ProtectedRoute>} />
        <Route path="/help" element={<ProtectedRoute><WithLayout title="Help" /></ProtectedRoute>} />

        {/* Admin Routes */}
        <Route path="/admin/users" element={<ProtectedRoute><WithLayout title="User Management" /></ProtectedRoute>} />
        <Route path="/admin/invitations" element={<ProtectedRoute><WithLayout title="Invitations" /></ProtectedRoute>} />

        {/* Catch-all (must be last) */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
```

### Icon Mapping

| Route | Lucide Icon | Visual Meaning |
|-------|-------------|----------------|
| `/dashboard` | `Home` | Home/Dashboard |
| `/data` | `TrendingUp` | Market data, charts |
| `/statistical-analysis` | `Calculator` | Statistical analysis |
| `/backtesting/rule-based` | `FileCode` | Code-based rules |
| `/backtesting/ai` | `Brain` | AI/ML models |
| `/bot` | `Bot` | Automated trading |
| `/settings` | `Cog` (Settings) | Configuration |
| `/help` | `HelpCircle` | Help/Support |
| `/admin/users` | `LayoutDashboard` | Admin panel |
| `/admin/invitations` | `Mail` | Email invitations |

---

## Adding New Sections

### Step-by-Step Guide

#### 1. Create Page Component

```bash
# Example: Adding "Risk Management" section
touch frontend/src/client/pages/RiskManagement.tsx
```

```typescript
// RiskManagement.tsx
import React from 'react';
import { useI18n } from '@/state/app';

export const RiskManagement: React.FC = () => {
  const { t } = useI18n();

  return (
    <div className="p-6">
      <h1>{t("nav.riskManagement")}</h1>
      {/* Your content */}
    </div>
  );
};
```

#### 2. Add Translation Keys

**en.json**:
```json
{
  "nav": {
    "riskManagement": "Risk Management"
  }
}
```

**es.json**:
```json
{
  "nav": {
    "riskManagement": "Gestión de Riesgo"
  }
}
```

#### 3. Add Route to App.tsx

```typescript
import { RiskManagement } from "@/pages/RiskManagement";

// Inside <Routes>
<Route
  path="/risk-management"
  element={<ProtectedRoute><RiskManagement /></ProtectedRoute>}
/>
```

**⚠️ IMPORTANT**: Add route **BEFORE** the catch-all `*` route!

#### 4. Add Sidebar Entry

```typescript
import { Shield } from "lucide-react"; // Choose appropriate icon

const items = [
  // ... existing items
  {
    to: "/risk-management",
    icon: Shield,
    label: t("nav.riskManagement"),
    visible: true, // Or role-based: user?.role === "admin"
  },
];
```

#### 5. (Optional) Add Group Label

```typescript
{
  to: "/risk-management",
  icon: Shield,
  label: t("nav.riskManagement"),
  visible: true,
  groupLabel: t("nav.riskManagementLabel"), // "RISK MANAGEMENT"
}
```

**Translation**:
```json
{
  "nav": {
    "riskManagement": "Risk Management",
    "riskManagementLabel": "RISK MANAGEMENT"
  }
}
```

### Best Practices

1. **Naming Convention**:
   - Route path: lowercase with hyphens (`/risk-management`)
   - Component: PascalCase (`RiskManagement.tsx`)
   - Translation key: camelCase (`riskManagement`)

2. **Icon Selection**:
   - Use [Lucide Icons](https://lucide.dev/) for consistency
   - Choose icons that visually represent the section
   - Import only needed icons to reduce bundle size

3. **Role-Based Access**:
   ```typescript
   visible: user?.role === "admin" || user?.role === "trader"
   ```

4. **Group Labels**:
   - Use sparingly (only for major sections)
   - Always uppercase with increased letter-spacing
   - Only show when sidebar is NOT collapsed

5. **Route Order**:
   - Group related routes together
   - Admin routes at the bottom
   - Catch-all `*` route MUST be last

---

## Role-Based Access

### User Roles

NQHUB supports 4 user roles with different access levels:

| Role | Access Level | Sidebar Items |
|------|--------------|---------------|
| `admin` | Full access | All items + Admin section |
| `trader` | BOT access | All items except Admin |
| `analystSenior` | Analysis only | All items except BOT and Admin |
| `analystJunior` | Analysis only | All items except BOT and Admin |

### Implementation

**Visibility Control**:
```typescript
{
  to: "/bot",
  icon: Bot,
  label: t("nav.botModule"),
  visible: user?.role === "trader" || user?.role === "admin",
}
```

**Protected Routes**:
```typescript
<Route
  path="/bot"
  element={
    <ProtectedRoute requiredRole={["trader", "admin"]}>
      <BotModule />
    </ProtectedRoute>
  }
/>
```

**Admin-Only Section**:
```typescript
{user?.role === "admin" && (
  <>
    <NavLink to="/admin/users">{/* User Management */}</NavLink>
    <NavLink to="/admin/invitations">{/* Invitations */}</NavLink>
  </>
)}
```

### Access Control Matrix

| Section | Admin | Trader | Analyst Sr | Analyst Jr |
|---------|-------|--------|------------|------------|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Data Module | ✅ | ✅ | ✅ | ✅ |
| Statistical Analysis | ✅ | ✅ | ✅ | ✅ |
| Backtesting Rule-Based | ✅ | ✅ | ✅ | ✅ |
| Backtesting AI | ✅ | ✅ | ✅ | ✅ |
| BOT Module | ✅ | ✅ | ❌ | ❌ |
| Settings | ✅ | ✅ | ✅ | ✅ |
| Help | ✅ | ✅ | ✅ | ✅ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| Invitations | ✅ | ❌ | ❌ | ❌ |

---

## Styling

### Visual Design System

**Colors** (from TailwindCSS theme):
- **Active Item**: `bg-primary/10`, `border-primary/40`, `text-foreground`
- **Hover Item**: `bg-sidebar-accent/60`, `border-primary/30`, `text-foreground`
- **Inactive Item**: `text-muted-foreground/80`, `border-transparent`
- **Group Label**: `text-muted-foreground/50`
- **Active Indicator**: `bg-primary/80` (3px vertical bar)

**Typography**:
- **Nav Items**: `text-[0.72rem]`, `font-semibold`, `uppercase`, `tracking-[0.18em]`
- **Group Labels**: `text-[0.6rem]`, `font-bold`, `uppercase`, `tracking-[0.3em]`

**Spacing**:
- **Sidebar Width**: Expanded `w-64` (256px), Collapsed `w-16` (64px)
- **Item Padding**: `px-3 py-2.5`
- **Group Label Margin**: `mt-4 mb-2`

### Active State Indicator

```typescript
<span
  className={cn(
    "pointer-events-none absolute left-2 top-1/2 h-7 w-[3px] -translate-y-1/2 rounded-full bg-primary/80 transition-opacity",
    isActive ? "opacity-100" : "opacity-0 group-hover:opacity-50"
  )}
/>
```

---

## Troubleshooting

### Issue: Sidebar item not showing

**Possible causes**:
1. `visible: false` in items array
2. Role-based access restriction
3. User not authenticated
4. Translation key missing

**Solution**:
```typescript
// Check visibility
console.log(items.filter(i => i.visible));

// Check user role
console.log(user?.role);

// Check translations
console.log(t("nav.yourKey"));
```

### Issue: Route not working

**Possible causes**:
1. Route defined after catch-all `*` route
2. Missing `<ProtectedRoute>` wrapper
3. Component not imported

**Solution**:
1. Move route before `<Route path="*" .../>`
2. Wrap in `<ProtectedRoute>`
3. Import component at top of App.tsx

### Issue: Active state not highlighting

**Possible causes**:
1. Route path mismatch (e.g., `/data` vs `/data/`)
2. NavLink not using `isActive` prop
3. CSS classes not applied

**Solution**:
```typescript
// Use exact path match
<NavLink to="/data" end>

// Check isActive prop
className={({ isActive }) => cn(
  isActive ? "bg-primary/10" : "bg-transparent"
)}
```

### Issue: Group label not showing

**Possible causes**:
1. Sidebar collapsed (`ui.sidebarCollapsed === true`)
2. Missing `groupLabel` property
3. Translation key missing

**Solution**:
```typescript
// Check collapsed state
{groupLabel && !ui.sidebarCollapsed && (
  <div>{groupLabel}</div>
)}

// Add groupLabel to item
{
  to: "/data",
  groupLabel: t("nav.dataModuleLabel")
}
```

---

## Related Documentation

- **CLAUDE.md** - Complete architecture guide
- **README.md** - Project overview
- **PATTERN_DETECTION_GUIDE.md** - Pattern Detection routes and UI
- **frontend/README.md** - Frontend architecture details
- **docs/DATABASE_SCHEMA.md** - Database structure (affects admin routes)
