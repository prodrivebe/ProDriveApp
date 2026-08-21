# ProDrive Dispatcher Design System

Premium European executive transport visual language for the dispatcher web application.

## Tokens (`tokens.ts`)

- **Colours:** navy foundation, ivory surfaces, champagne accent, semantic states
- **Radii, shadows, spacing, typography, transitions, layout**

## Theme (`theme.ts`)

MUI theme with component overrides for buttons, inputs, cards, tables, dialogs, chips, and navigation.

## Components

- `PageHeader` — page title, subtitle, actions
- `PremiumCard` — elevated content panel with optional header
- `StatTile` — KPI metric tile with tabular numerals
- `StatusBadge` — unified semantic status chips

## Usage

```tsx
import { PageHeader, StatTile, StatusBadge } from "../design-system";
```

Apply tokens via theme — avoid hardcoded hex values in pages.
