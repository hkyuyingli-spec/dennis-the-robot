# NutriBot React client

This directory contains the shared React + TypeScript app used for browser builds and the Capacitor Android wrapper. The legacy Streamlit app remains at the repository root and is not replaced by this client.

## Entry points and configuration

- `src/main.tsx` mounts the React app; `src/App.tsx` contains the shared chat interface.
- `src/api.ts` calls the Python backend. It contains no provider credentials.
- `vite.config.ts` defines the web development proxy and build modes.
- `capacitor.config.ts` points Capacitor at the generated `dist/` assets.
- `android/` is the native Capacitor Android project, generated from this shared client.
- `VITE_API_BASE_URL` is the public HTTPS API origin used by packaged Android builds. Copy `.env.android.example` to `.env.android` and set the real backend URL; this is an endpoint, not a secret.

## Local development

In one terminal, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:GROQ_API_KEY = "your-server-side-key"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

Vite serves the client at `http://localhost:5173` and proxies `/api` requests to the local backend on port 8000. Keep `GROQ_API_KEY` only in the backend environment or a server-side secret manager.

## Build targets

Web:

```powershell
npm --prefix frontend run build:web
```

The static web build is emitted to `frontend/dist/`. Deploy it behind an HTTPS reverse proxy that routes `/api` to the backend, or set an appropriate `VITE_API_BASE_URL` at build time.

Android:

1. Configure `frontend/.env.android` with the deployed HTTPS API URL.
2. From the repository root, run:

```powershell
npm --prefix frontend run build:android
npm --prefix frontend run android:open
```

`build:android` builds the same React source in Android mode and synchronizes the web assets into the Capacitor Android project. Then use Android Studio to build/sign the package, or run `npm --prefix frontend run android:run` with an Android SDK/device configured.

The API must allow the deployed web origin and the Capacitor origin in `NUTRIBOT_CORS_ORIGINS`. CORS is not authentication; deploy the API behind platform-level abuse controls and add user authentication before exposing it publicly.

## Keep the existing Streamlit app

The existing app remains runnable from the repository root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The root `index.html`, `manifest.json`, `sw.js`, Python modules, and Streamlit config remain separate from the Vite client.
