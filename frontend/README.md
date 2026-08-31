# Smart Study Monitor Frontend

An independent React/Vite dashboard for the Smart Study Monitor Python application. It currently uses mock session data and browser webcam access only; it does not change or call `../app.py`.

## Run locally

From this `frontend` folder:

```bash
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Click **Start Monitoring** to grant browser camera permission. If permission is unavailable, the dashboard remains usable in simulation mode.

## Architecture

- `src/components/` — focused UI components
- `src/hooks/useMonitoringSession.js` — session state plus optional browser webcam lifecycle
- `src/services/monitoringService.js` — mock data and the future FastAPI integration boundary

When a FastAPI backend is ready, replace the commented methods in `src/services/monitoringService.js` and connect them from the monitoring hook. The existing Python detection loop remains untouched.
