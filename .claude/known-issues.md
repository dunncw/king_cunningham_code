# Known Issues + Industry Recommendations

> **Living doc** — tracks current state. Update as issues fixed or new ones found.
> Status marks defined in [CLAUDE.local.md](CLAUDE.local.md#status-marks--living-doc-legend).

## Bugs Fixed (This Review)

| Status | Issue | Fix | File |
|---|---|---|---|
| `DONE` | Splash msg on closed widget | Re-show splash after update confirm dialog | `launcher/launcher.py` |
| `DONE` | .gitignore fused entries | Add missing newline between two paths | `.gitignore` |
| `DONE` | release.ps1 missing launcher.exe | Add `dist/launcher.exe` to `gh release create` args | `scripts/release.ps1` |
| `DONE` | Error log clobber | Append w/ timestamp instead of overwrite | `launcher/launcher.py` |
| `DONE` | Deprecated block_cipher | Remove from both .spec files | `KC_app.spec`, `launcher/launcher.spec` |

## Open Issues

### HIGH

**`[WONT]` No code signing**
- SmartScreen blocks unsigned EXEs on first run per version
- Decision: not worth cost ($100-400/yr) for current user base
- Mitigation: README documents SmartScreen bypass steps (click "More info" → "Run anyway")
- Revisit if user base grows or trust becomes blocker

**`[DONE]` No integrity verification on downloads**
- Downloaded ZIP not hash-checked → corrupt/tampered zips silently accepted
- Fix: build.py generates `KC_app.zip.sha256`, release.ps1 uploads as asset, launcher verifies after download
- setup_binaries.py: pinned SHA-256 for Tesseract installer (from winget manifest)

**`[DONE]` Launcher not self-updating**
- Self-install ran only on first launch (not-in-install-dir check)
- Fix: `__version__` in launcher.py (synced by build.py), compared against release tag. If newer → download new launcher.exe from release asset, rename-self → launcher.old.exe, swap in new, re-launch. Old cleaned up on next start
- Graceful: if release has no launcher.exe asset or download fails, skips silently

**`[NEXT]` No rollback on failed extraction**
- `_install_from_zip` renames old → KC_app_old, extracts new
- If extraction fails (disk full, permissions) → old renamed, new broken
- KC_app_old cleanup runs next launch but app won't start until then
- Fix: verify extraction success before deleting old. Rename back on failure

### MEDIUM

**`[WATCH]` No CI/CD pipeline**
- No `.github/workflows/` → builds manual only
- Industry: GH Actions workflow → build on tag push → auto-publish release
- Eliminates "works on my machine" builds
- Pattern: `on: push: tags: ['v*']` → build → `gh release create`

**`[WATCH]` No uninstaller / Add-Remove Programs entry**
- Users can't cleanly remove app
- Industry: NSIS/Inno Setup installer → registers w/ Windows → appears in "Apps & features"
- Alt: add uninstall script + registry entry via launcher

**`[WATCH]` ~180 MB full downloads for minor updates**
- No delta/patch mechanism
- Industry patterns: binary diff (bsdiff/courgette), modular updates, or accept trade-off for simplicity
- Current approach = simple + reliable. Trade-off acceptable at current user count

**`[WATCH]` Version tag inconsistency**
- Git tags: `v0.0.12-1`, `v0.0.13.1` — mix dash + dot separators
- `_parse_version` splits on `.` only → dash versions → ValueError → silently skip update
- Fix: standardize on `vX.Y.Z` only. Never use dash/extra dots in tags

**`[WATCH]` No telemetry / crash reporting**
- Launcher log = local file only. No visibility into user-side failures
- Industry: Sentry, Bugsnag, or simple POST-to-endpoint on crash
- Privacy trade-off. At minimum: encourage users to share `%TEMP%\kc_launcher_error.log`

### LOW

**`[WATCH]` Double splash on first install**
- First run → splash → self-install → re-launch → splash again
- Users see two splash flashes
- Fix: pass flag via CLI arg to skip splash on re-launched instance

**`[WATCH]` GitHub API rate limit**
- Unauthenticated: 60 req/hr per IP
- Won't hit this w/ few users. At scale → add `Accept: application/vnd.github.v3+json` header + optional token

**`[WATCH]` Launcher bundles PyQt6 unnecessarily large**
- Launcher only uses QSplashScreen, QMessageBox, QProgressDialog
- PyQt6 = ~30 MB of launcher's ~40 MB
- Alt: use tkinter (stdlib) or win32 API for dialogs → launcher < 10 MB

## Industry Standard Comparison

| Practice | KC App | Status | Industry Standard |
|---|---|---|---|
| Auto-update | Yes (launcher checks GitHub) | `DONE` | Yes (Electron/Squirrel, Sparkle, WinSparkle) |
| Code signing | No | `WONT` | Yes (EV cert for SmartScreen trust) |
| Installer framework | No (self-install via code) | `WATCH` | NSIS/Inno Setup/WiX/MSIX |
| Add/Remove Programs | No | `WATCH` | Yes (via installer) |
| Delta updates | No (full zip) | `WATCH` | Common (bsdiff, courgette, partial zips) |
| Hash verification | Yes (SHA256 asset + pinned hashes) | `DONE` | Yes (SHA256 published w/ release) |
| CI/CD build | No | `WATCH` | Yes (GH Actions, Azure Pipelines) |
| Crash reporting | Local file only | `WATCH` | Sentry/Bugsnag + remote collection |
| Rollback | Manual (rename KC_app_old) | `NEXT` | Automatic on failed update |
| Launcher self-update | Yes (rename-swap-relaunch) | `DONE` | Yes (two-phase self-replace) |

## Priority Order for Improvements

1. ~~Code signing~~ → `WONT` — too expensive, README mitigates
2. ~~Hash verification~~ → `DONE`
3. CI/CD pipeline (`WATCH` — when manual builds become pain point)
4. Rollback on failed extraction (`NEXT` — robustness)
5. ~~Launcher self-update~~ → `DONE`
6. Uninstaller (`WATCH` — professionalism)
7. Delta updates (`WATCH` — only if user count grows)
