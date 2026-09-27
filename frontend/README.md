# React frontend

React, TypeScript, Vite, React Router, and plain CSS. Node 24 and npm are required. No global npm packages are needed.

## Development

Start the FastAPI backend on port 8000, then run:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite forwards `/api/*` to `http://127.0.0.1:8000/*`, so local development needs no CORS configuration. To change the backend address, copy `.env.example` to `.env.local` and set `API_PROXY_TARGET`. This is a server-side proxy setting, not a browser-exposed variable.

## Included

- Public overview and example request form.
- Registration and login using the existing API.
- Protected account and dataset pages, with return-to-page after login.
- CSV upload, catalog, column metadata, and quota display.
- Loading, empty, validation, network error, and expired-session handling.
- Responsive styles and accessible labels, navigation, and form status messages.

Bearer tokens are kept only in React state. Reloading or closing the page signs the user out; a 401 on an authenticated request also clears the session. Sign out clears the local session; it does not revoke the backend's JWT. Add a backend-managed session or refresh-token flow when persistent login is needed. Passwords and tokens are never written to browser storage.

## Structure

```text
src/
  api/          Fetch wrapper, error parsing, response types
  auth/         Session context/provider and route guard
  components/   Shared application layout
  pages/        Overview, login/register, account, datasets
  App.tsx       Route definitions
  main.tsx      Application entry point
  styles.css    Shared styles and responsive layout
```

Add a page under `src/pages/` and register it in `App.tsx`. Place private routes under `RequireAuth`. Use `useAuth().request` for authenticated calls so expired credentials are handled consistently. Use `apiRequest` for public calls. Both accept normal fetch options, including abort signals; use `FormData` for uploads without manually setting `Content-Type`.

Response interfaces in `src/api/types.ts` mirror the backend schemas. Keep them in sync when changing API contracts; the fetch wrapper does not perform runtime schema validation.

## Checks

```bash
npm run lint
npm run format:check
npm run typecheck
npm run build
npx playwright install chromium
npm test
```

Browser tests run in Chromium at desktop and mobile sizes. They intercept API requests, so PostgreSQL and the backend are not required. On Linux, Playwright may need system browser libraries; CI installs these using `npx playwright install --with-deps chromium`.

Run `npm run format` to apply the shared Prettier formatting rules.

`npm run preview` serves the production build on port 4173, using the same local API proxy. It is for local verification, not production hosting.

## Docker

From the repository root, use `docker compose --profile ui up --build`. The frontend is available on port 5173. Its image builds with Node and serves static files with unprivileged Nginx on port 8080.

Nginx forwards `/api/` to `API_UPSTREAM` (default `http://backend:8000`) and falls back to `index.html` for client routes. Hashed assets are cached; HTML is revalidated. `API_UPSTREAM` has no trailing slash and must be an HTTP(S) URL reachable from the frontend container. DNS resolution uses Docker's internal resolver.

The proxy defaults to an 11 MiB request-body limit (`CLIENT_MAX_BODY_SIZE=11m`) to accommodate a 10 MiB file plus multipart fields. If you raise backend `MAX_UPLOAD_BYTES`, raise this limit too. The backend still enforces its exact file limit. The proxy replaces forwarded client headers; Compose trusts those headers and keeps the backend's published port bound to loopback. Keep direct backend access restricted when deploying behind a proxy.

References: [Vite](https://vite.dev/guide/), [React Router](https://reactrouter.com/start/declarative/installation).
