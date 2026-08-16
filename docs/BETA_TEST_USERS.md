# Beta and demo test users

These accounts are seeded locally by `backend/app/scripts/seed_dev.py` and related ensure scripts.

## Dispatcher web (username login)

| Role | Username | Password |
|------|----------|----------|
| Demo admin | `demo.admin` | `DemoAdmin123!` |
| Demo dispatcher | `demo.dispatcher` | `DemoDispatch123!` |
| Legacy admin | `admin` | `Admin123!` |
| Legacy dispatcher | `dispatcher` | `Dispatch123!` |

## Mobile driver app

| Role | Username | Password |
|------|----------|----------|
| Mobile demo driver | `driver1` | `ProDrive2026!` |

Full email: `driver1@prodrive.demo`

## Notes

- Username login accepts either the email local part (for example `admin`) or a full email address.
- Drivers are blocked from the dispatcher web UI and must use the mobile app.
- Run backend seed in development: `python -m app.scripts.seed_dev`
