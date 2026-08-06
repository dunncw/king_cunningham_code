# Build and publish a GitHub release.
#
# Usage:
#   .\scripts\release.ps1           # Build, tag, publish full release
#   .\scripts\release.ps1 -Draft    # Build, tag, save as draft (no users notified)
#
# Reads the version from version.txt. Update that file before running.
# Commits any version bump to src/main.py automatically.

param(
    [switch]$Draft
)

$ErrorActionPreference = "Stop"

$version = (Get-Content version.txt -Raw).Trim()
$tag     = "v$version"

Write-Host "[release] Version: $version  Tag: $tag"

# ── 1. Build ────────────────────────────────────────────────────────────────
# Use the venv interpreter explicitly. A bare "python" resolves to system Python,
# which lacks pyinstaller and fails mid-build with a bare FileNotFoundError.
$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual env not found at .venv. Create it before releasing."
    exit 1
}
$venvScripts = Split-Path $venvPython -Parent
$env:PATH = "$venvScripts;$env:PATH"

Write-Host "[build] Building ..."
& $venvPython build.py
if ($LASTEXITCODE -ne 0) { Write-Error "Build failed."; exit 1 }

# Verify expected outputs exist
foreach ($f in @("dist\KC_app.zip", "dist\KC_app.zip.sha256", "dist\launcher.exe", "dist\version.txt")) {
    if (-not (Test-Path $f)) { Write-Error "Missing expected output: $f"; exit 1 }
}

# ── 2. Commit version bump if needed ────────────────────────────────────────
# build.py syncs __version__ into launcher/launcher.py too, so commit it here.
# Leaving it out strands the launcher a version ahead of version.txt.
$versionFiles = @("version.txt", "src/main.py", "launcher/launcher.py")
$staged = git diff --name-only HEAD -- $versionFiles
if ($staged) {
    Write-Host "[git] Committing version bump ..."
    git add $versionFiles
    git commit -m "chore: bump version to $version"
}

# ── 3. Tag ──────────────────────────────────────────────────────────────────
if (git tag -l $tag) {
    Write-Error "Tag $tag already exists. Delete it first: git tag -d $tag"
    exit 1
}
git tag $tag
git push origin (git branch --show-current) --tags
Write-Host "[git] Pushed tag $tag"

# ── 4. GitHub release ───────────────────────────────────────────────────────
$releaseArgs = @($tag, "dist\KC_app.zip", "dist\KC_app.zip.sha256", "dist\launcher.exe", "--title", $tag)
if ($Draft) {
    $releaseArgs += "--draft"
    Write-Host "[gh] Creating draft release $tag ..."
} else {
    Write-Host "[gh] Creating release $tag ..."
}

gh release create @releaseArgs
if ($LASTEXITCODE -ne 0) { Write-Error "gh release create failed."; exit 1 }

Write-Host ""
Write-Host "[done] Release $tag published."
if (-not $Draft) {
    Write-Host "      Users will receive the update on their next launcher run."
}
