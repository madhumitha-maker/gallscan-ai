# GallScan AI — Interface & Deployment Fix Request

**For:** Antigravity agent, continuing work on the `gallbladder-app` repo
**Context:** `fullstack_implementation_report.md` shows the backend, model, and DB schema built and verified end-to-end. This doc lists 4 issues found in the live app that need fixing before this is considered done.

---

## 1. Nav bar re-renders / "hops" between pages

**Symptom:** The nav bar visibly reloads or shifts when navigating between `index.html`, `upload.html`, `result.html`, etc.

**Root cause:** Each `.html` file almost certainly has its own hardcoded `<nav>...</nav>` markup. Because this is a multi-page static site (not an SPA), every navigation is a full page load — even with identical markup, fonts/CSS/images re-paint, which reads as "hopping."

**Required fix — pick one:**

- **Option A (minimal change, recommended for this stack):** Extract the nav bar into a single shared component (`frontend/components/navbar.js`) that injects identical HTML into a `<div id="navbar-root"></div>` present on every page, with an `active` class applied based on current path. Pair this with:
  - Nav bar CSS using `position: sticky; top: 0;` so it doesn't reflow on scroll either.
  - Preload shared fonts/CSS in `<head>` on every page so there's no flash of unstyled content on navigation.
  - Ensure the nav's HTML, class names, and DOM order are byte-identical across all 7 pages — any divergence (even whitespace-driven layout shift) will still read as a "hop."

- **Option B (more robust, larger change):** Convert the frontend to a single-page app shell (`index.html` as the only real page) with client-side routing (`history.pushState` + a simple router in `app.js`) that swaps only the `<main>` content per route while the nav bar and layout shell never unmount. This fully eliminates the hop but is a bigger refactor — only do this if Option A doesn't feel smooth enough after testing.

**Acceptance criteria:** Clicking every nav link in sequence (Upload → Result → History → Profile → Notifications) shows zero visible flicker/shift in the header across at least 3 manual passes.

---

## 2. Mobile responsiveness

**Symptom:** Layouts assume desktop width; not usable on phone-sized viewports.

**Required fix:**
- Confirm `<meta name="viewport" content="width=device-width, initial-scale=1">` is present in every page's `<head>` (agents sometimes omit this).
- Add responsive breakpoints (suggested: 375px, 768px, 1024px) to every screen:
  - **Nav bar:** collapse to a hamburger menu below 768px; nav links move into a slide-out or dropdown panel.
  - **Upload screen:** drag-and-drop zone shrinks to full-width single column; ensure it's still tappable/droppable on touch.
  - **Result screen:** the original-image / Grad-CAM toggle and the top-3 bar chart should stack vertically on narrow screens instead of side-by-side.
  - **History table:** convert from a table layout to a stacked card list below 768px (table columns don't work on phone width) — each card shows thumbnail, class, confidence, date.
  - **Profile page:** account card and recent-history strip stack vertically.
  - **Notification popover:** on mobile, the popover should become a full-width dropdown or bottom sheet rather than a small fixed-width box that can overflow the viewport.
- Test with actual browser device emulation (iPhone SE width ~375px minimum) — not just resizing the desktop window.

**Acceptance criteria:** No horizontal scroll, no overlapping/clipped elements, and all interactive elements remain tappable (min ~44px touch target) at 375px, 768px, and 1024px widths.

---

## 3. Deploy entirely to Vercel

**Important constraint to resolve first, not skip:** Vercel serverless functions have a deployment size limit (currently 250MB unzipped per function). Your backend depends on **PyTorch + timm + pytorch-grad-cam** for live Grad-CAM — that dependency stack alone is typically 500MB–1GB+, which will not fit in a single Vercel Python function. Before implementing, the agent needs to resolve this one of three ways:

- **Option A — split live Grad-CAM out of the Vercel deploy:** Vercel hosts the frontend (static) + a lightweight FastAPI function using only `onnxruntime` for `/predict` (small, fits fine). Grad-CAM becomes a separate service (Render/Railway/Fly.io, which don't have this size limit) that the Vercel function calls, or Grad-CAM is dropped to a precomputed/static example rather than live-per-upload.
- **Option B — everything on Vercel, drop live Grad-CAM:** Serve predictions via ONNX only on Vercel; Grad-CAM overlay becomes the static sample image from the export zip (`gradcam_samples.png`) rather than a per-upload heatmap. Simplest, but weakens the "explainable" claim in the project title.
- **Option C — don't use Vercel for the backend at all:** Frontend on Vercel, FastAPI + PyTorch backend on Render/Railway/Fly.io (no size limit issue), Neon Postgres already works fine from either. "Entirely on Vercel" isn't achievable with live Grad-CAM in the stack — this is a hosting-platform constraint, not an implementation bug.

**Decide which option before implementing** — I'd lean toward **Option C** given live Grad-CAM was treated as core to the project earlier, but confirm before the agent builds it out.

**Regardless of option chosen, required setup:**
- `vercel.json` routing config: static `frontend/` files served directly, backend routes proxied to the FastAPI function (or external service URL per Option C).
- If deploying the FastAPI app itself to Vercel (Options A/B): use `@vercel/python` runtime with an ASGI entrypoint (`api/index.py` exposing the FastAPI `app` object), per Vercel's Python/ASGI support — confirm current syntax against Vercel's docs since this has changed across Vercel platform versions.
- Environment variables (`DATABASE_URL` with `?sslmode=require` for Neon, `JWT_SECRET`, any other secrets) set in the Vercel project dashboard, **not** committed to the repo — `.env` stays in `.gitignore`.
- CORS updated to allow the deployed frontend origin (not just `localhost`).
- Confirm the Neon connection works from Vercel's serverless environment specifically — cold starts + connection pooling can be an issue; consider Neon's pooled connection string (`-pooler` host) rather than the direct one.

**Acceptance criteria:** Deployed Vercel URL loads the landing page, and a full flow (signup → login → upload → prediction → history) works against the deployed backend and Neon DB, not localhost.

---

## 4. App uses sessionStorage instead of Neon PostgreSQL

**Symptom:** Despite the DB schema and `test_e2e.py` suite passing, the running app appears to persist predictions/history/notifications in browser `sessionStorage` rather than actually reading/writing Neon Postgres — data likely disappears on tab close or doesn't sync across devices/sessions.

**This is a real bug, not a config issue** — the test suite passing means the DB *can* work, but the frontend and/or some routes aren't actually using it. Required fix:

- **Audit every frontend JS file** (`upload.js`, `history.js`, `profile.js`, `notifications.js`, `auth.js`) for any use of `sessionStorage.setItem`/`getItem` that stores *domain data* (predictions, history list, notifications, user profile). Remove these — `sessionStorage` should only ever hold the JWT token itself (or nothing, if using httpOnly cookies instead, which is more secure — worth considering as part of this fix).
- **Confirm every read/write goes through the API:**
  - `/predict` → must `INSERT` into `predictions` table, not just return JSON to be cached client-side.
  - `/history` → must `SELECT` from `predictions` table filtered by `user_id`, not read from a client-side array.
  - `/notifications` → must `SELECT`/`UPDATE` the `notifications` table, not local state.
  - `/users/me` → must `SELECT`/`UPDATE` the `users` table.
- **Verify with a real cross-session test**, not just `test_e2e.py` (which tests the backend directly and may be passing while the frontend bypasses it entirely): log in, create a prediction, close the browser tab completely, reopen, log in again — the prediction must still appear in History. If it doesn't, the frontend is not calling the persisted endpoints correctly.
- **Check `DATABASE_URL` is actually the live Neon connection string at runtime**, not silently falling back to a local/mock/in-memory store on connection failure — add a startup check in `main.py` that fails loudly (crashes with a clear error) if the DB is unreachable, rather than the app continuing to run on some fallback.

**Acceptance criteria:** Data survives a full logout/login cycle and a browser restart, confirmed by inspecting the Neon dashboard's table data directly (not just trusting the UI) — row counts in `predictions`/`notifications` should increase with real usage, independent of any single browser tab.

---

## Suggested order of work

1. Fix #4 first (data persistence) — it's a correctness bug, and #1–#3 are easier to verify once data is actually durable.
2. Fix #1 (nav bar) and #2 (mobile) together — both are frontend-only, no backend risk.
3. Resolve the Option A/B/C decision for #3, then implement deployment last, once the app is confirmed working correctly locally.
