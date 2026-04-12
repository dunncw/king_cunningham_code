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
Write-Host "[build] Building ..."
python build.py
if ($LASTEXITCODE -ne 0) { Write-Error "Build failed."; exit 1 }

# Verify expected outputs exist
foreach ($f in @("dist\KC_app.zip", "dist\KC_app.zip.sha256", "dist\launcher.exe", "dist\version.txt")) {
    if (-not (Test-Path $f)) { Write-Error "Missing expected output: $f"; exit 1 }
}

# ── 2. Commit version bump if needed ────────────────────────────────────────
$staged = git diff --name-only HEAD -- version.txt src/main.py
if ($staged) {
    Write-Host "[git] Committing version bump ..."
    git add version.txt src/main.py
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
