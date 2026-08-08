# ProDrive Dispatcher Dashboard

React + TypeScript + Material UI web app for dispatchers and admins.

## Prerequisites

- Node.js 20+
- ProDrive backend running at http://localhost:8000

## Setup

```bash
cd dispatcher-dashboard
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173

## Dev credentials

| Email | Password |
|-------|----------|
| admin@example.com | Admin123! |
| dispatcher@example.com | Dispatch123! |

## Sprint 002 v1 screens

- Login
- Operations dashboard (KPI widgets)
- Orders list, detail, assign driver
- Create order wizard with AI parse
- Customers list
- Fleet overview
- Notifications
- Reports
- Global search in top bar

## Build

```bash
npm run build
npm run preview
```

The Vite dev server proxies `/api` to the backend. CORS is also enabled on the API for `http://localhost:5173`.
