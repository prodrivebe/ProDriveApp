# ProDrive Frontend

Dispatcher operations board and web dashboard for ProDrive transport companies.

## Stack

- React 19 + TypeScript
- Vite
- Material UI
- React Router
- TanStack Query
- React Hook Form + Zod
- Axios
- Vitest + Testing Library

## Development

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` and `/uploads` to `http://localhost:8000`.

Set `VITE_API_BASE_URL` when building for production (default `/api/v1`).

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Type-check and production build |
| `npm run test` | Run Vitest test suite |
| `npm run preview` | Preview production build |

## Structure

```text
src/
  app/          Application shell, theme, router, providers
  components/   Shared UI components
  features/     Feature schemas and domain helpers
  hooks/        Auth and permission hooks
  layouts/      Main dispatcher layout
  pages/        Route-level screens
  services/     Typed API clients
  types/        Shared API types
  utils/        Formatting and error helpers
```

## Authentication

Uses backend JWT login at `/api/v1/auth/login` with refresh token rotation. Drivers are blocked from the dispatcher UI.

Default dev credentials (after seeding):

- Email: `admin@example.com`
- Password: `Admin123!`
