# PayGate Frontend

Modern React + Vite + TypeScript + Tailwind frontend for the PayGate backend.

## Dev Setup

1. Install dependencies
```
cd paygate_frontend
npm install
```

2. Run backend (Django) on http://localhost:8000 and ensure CORS and cookies are configured for dev.

3. Start frontend
```
npm run dev
```
Vite proxy forwards requests to `/paygate/**` to `http://localhost:8000`.

## Pages
- Login, Register (merchant)
- Dashboard (shows API key)
- Orders (create order)
- Payments (process payment)
- Refunds (process refund)
- Admin stats (admin only)

## Notes
- Access token is stored in memory and sessionStorage (for reload persistence). Refresh token is an HttpOnly cookie, refreshed automatically by interceptor on 401.
- Update backend cookie SameSite and CORS for cross-origin development.




