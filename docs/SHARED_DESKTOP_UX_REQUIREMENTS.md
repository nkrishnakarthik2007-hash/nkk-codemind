# Shared NKK Desktop App Experience

This document records product-wide desktop requirements for NKK DroidBox and the future NKK CodeMind desktop application. CodeMind is currently a CLI prototype, so these are requirements for its future desktop shell, not a claim that its updater or UI already exists.

## 1. Release-aware update notifications

- The application must distinguish a GitHub commit, a pull request, a CI build artifact, and a published stable GitHub Release.
- A user-facing app update exists only after the release pipeline has succeeded and a stable release with installable update assets is published.
- Installed applications check the published release feed, download and stage updates inside the application, show real progress, and ask before restarting to apply the update.
- Normal updates must not require uninstalling/reinstalling. User data must remain outside the install directory and survive upgrades and rollback.
- Portable/developer builds must clearly state that they cannot self-update.
- When a new version is ready, show a short Telugu action phrase so the user immediately understands what to do: **కొత్త update వచ్చింది — ఇన్‌స్టాల్ చేసుకో**. Keep the rest of the product UI in English.
- Do not tell the user to install until the release workflow and release assets are actually verified.

## 2. Startup experience and logs

- Never expose a blank/black window between process start, splash screen, and first usable frame.
- Keep the branded splash visible until the main window has rendered its first frame.
- Show genuine startup phases; do not use a fake fixed delay as a substitute for initialization.
- Write persistent local application logs for startup milestones, exceptions, update checks, project loading, agent sessions, and tool failures.
- Store logs under the product's per-user application-data directory, not beside the executable, so updates do not overwrite them.
- Rotate and bound logs; never log passwords, access tokens, or full private prompts by default.
- Provide a diagnostics viewer with search, severity filters, copy, and open-folder actions.
- Sharing logs externally requires explicit user consent and a clear disclosure. The user must be able to inspect the destination because public GitHub issues are public.
- The diagnostic report must include both app startup logs and the relevant runtime/agent logs, with best-effort secret and personal-path redaction.

## 3. APK and app identity (DroidBox)

- APK library tiles and dock entries should show the actual Android launcher icon and app label when extractable.
- Support common PNG and WebP resources, and use a stable fallback when an APK uses unsupported adaptive-icon/resource formats.
- Backfill missing icons for APKs already in the user's library after an app update without deleting APKs or changing their package data.
- Preserve the original APK and app data during DroidBox upgrades.

## 4. Implementation status

- DroidBox: Velopack in-app update download/staging already exists for installed Setup builds. Startup logging, splash-to-window handover, diagnostics coverage, and broader icon extraction are being improved in the current feature branch.
- CodeMind: no desktop shell or in-app updater exists yet. Apply these requirements when the Tauri/React desktop shell and release pipeline are implemented.
