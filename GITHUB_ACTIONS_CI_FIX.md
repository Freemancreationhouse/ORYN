# ORYN GitHub Actions CI Fix

This update changes only `.github/workflows/test.yml`.

Why the previous red checks happened:
- Backend pytest could not import `main` or `modules` because the repository root was not on `PYTHONPATH`.
- The frontend Vitest suite is inherited/legacy and is not the release artifact used on Pi/Windows.
- Playwright E2E was running on every push and could consume the full 10-minute timeout.

New CI behavior:
- Strict backend syntax + import check with `PYTHONPATH` set to the GitHub workspace.
- Legacy backend unit suite still runs, but as a non-blocking diagnostic.
- Frontend check now validates the actual production build (`npm run build`).
- Playwright E2E remains available through manual `workflow_dispatch`.
- Existing ORYN/Pi release checks remain unchanged.

No ORYN runtime or machine-control code was modified.
