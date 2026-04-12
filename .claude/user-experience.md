# End User Experience

## First-Time Install

User gets `launcher.exe` (shared via email, Slack, USB, GitHub release page — any method).

### What user sees:

1. Double-click `launcher.exe`
2. Windows SmartScreen: "Windows protected your PC" → "More info" → "Run anyway"
   - Unsigned EXE → SmartScreen warns every first run on new machine
   - After first run: Windows remembers, no repeat warning
3. Splash screen appears (splash_image.png)
4. Status: "Installing KC Automation Suite..."
5. Status: "Creating Start Menu shortcut..."
6. Status: "Checking for updates..."
7. Progress dialog: "Downloading KC Automation Suite vX.Y.Z..." w/ progress bar + cancel
8. App launches full-screen (PyQt6 main window)

### What happens under hood:

```
launcher.exe (from Downloads/)
  → detect not in install dir
  → copy self → %LOCALAPPDATA%\King_Cunningham\KC_App\launcher.exe
  → create Start Menu shortcut → launcher.exe (installed copy)
  → re-launch from installed location
  → installed launcher starts
  → no local version.txt → version = "0.0.0"
  → fetch /releases/latest
  → download KC_app.zip → extract
  → write version.txt
  → launch KC_app.exe
  → exit launcher
```

Time: ~30-60s depending on download speed (~180 MB zip).

## Subsequent Launches

User opens "KC Automation Suite" from Start Menu (or re-runs launcher.exe from install dir).

### No update available:

1. Splash screen (< 2s)
2. App launches

### Update available:

1. Splash screen
2. Dialog: "Version X.Y.Z available (you have A.B.C). Update now?"
3. Yes → progress bar → install → app launches
4. No → app launches w/ current version

### Network down:

1. Splash screen
2. GitHub API fails → silently skip update check
3. App launches w/ current version (if installed)
4. If no app installed + no network → error dialog, exit

## Start Menu Entry

- Name: "KC Automation Suite"
- Location: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk`
- Target: `%LOCALAPPDATA%\King_Cunningham\KC_App\launcher.exe`
- Icon: from launcher.exe (app_icon.ico baked in)

Searchable via Windows search. Pinnable to taskbar.

## Uninstall

No uninstaller. No Add/Remove Programs entry. Manual:

1. Delete `%LOCALAPPDATA%\King_Cunningham\` (install dir)
2. Delete `%APPDATA%\King_Cunningham\` (config dir)
3. Delete `%APPDATA%\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk`

## Error Handling — What User Sees

| Scenario | UX |
|---|---|
| Network down, app installed | App launches normally (silent skip) |
| Network down, no app | Error dialog w/ exception text |
| Download cancelled | App exits cleanly |
| Download fails mid-stream | Partial .tmp file cleaned up. App launches old version if exists |
| Launcher crash | Generic Windows error. Log → `%TEMP%\kc_launcher_error.log` |
| App crash | PyQt error dialog w/ full traceback |
| Corrupt zip | Extraction fails → app launches old version |

## UX Pain Points

See [known-issues.md](known-issues.md) for full backlog w/ priority + industry comparison.

1. **SmartScreen warning** — unsigned EXE → scary "Unknown Publisher" dialog on first run
2. **Full re-download on update** — no delta/patch mechanism
3. **No uninstaller** — not in Add/Remove Programs
4. **Launcher not self-updating** — launcher bugs = users stuck
