# Telemedicine Frontend

React UI for the Telemedicine platform. This layer currently focuses on user management (registration, login, dashboards) and connects directly to the Django backend (`telemedicine_project`).

## Prerequisites

- Node.js 18+ (or the version required by Create React App)
- The Django API running locally (default: `http://127.0.0.1:8000`)

## Environment configuration

Create a `.env` file in `telemedicine-frontend/` so the React app knows where to find the API:

```
REACT_APP_API_BASE_URL=http://127.0.0.1:8000
REACT_APP_MEDIA_BASE_URL=http://127.0.0.1:8000
```

Restart `npm start` after changing environment variables.

## Available scripts

```bash
npm install        # first-time setup
npm start          # runs the dev server on http://localhost:3000
npm run build      # production build
npm test           # CRA test runner
```

## Current user flows

- `/register/patient`, `/register/doctor`, `/register/tmc` – role-specific onboarding screens that post to `POST /users/register/`.
- `/login` – authenticates against `POST /users/login/`, stores tokens, and redirects to the role dashboard.
- `/dashboard/patient` – shows the patient profile, doctor directory, and consultation requests.
- `/logout` – clears tokens and redirects to the login screen.

The API helper in `src/api/users.js` automatically injects JWT tokens and refreshes them when needed. All requests read `REACT_APP_API_BASE_URL`, so no code changes are needed when the backend base URL changes.

## Development tips

- Make sure the Django server is running (including `/users/*` and `/consultations/*` endpoints) before testing the UI.
- When working on protected routes, clear your browser’s `localStorage` if you need to simulate a logged-out state.
- For doctor photos or other media served by Django, `REACT_APP_MEDIA_BASE_URL` controls the root URL.

## Next steps

- Build consultation-specific UI (booking confirmation, chat, prescription viewer).
- Add toast notifications instead of `alert()` calls.
- Add test coverage for critical hooks/components using React Testing Library.
