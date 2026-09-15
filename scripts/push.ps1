$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VersionFile = Join-Path $RootDir "VERSION"
$ManifestFile = Join-Path $RootDir "PROJECT_MANIFEST.md"

Set-Location $RootDir
git rev-parse --is-inside-work-tree | Out-Null

if (-not (Test-Path $VersionFile)) { throw "Missing VERSION" }
if (-not (Test-Path $ManifestFile)) { throw "Missing PROJECT_MANIFEST.md" }

$Version = (Get-Content $VersionFile -Raw).Trim()
if ($Version -notmatch '^(\d+)\.(\d+)\.(\d+)$') {
    throw "VERSION must use MAJOR.MINOR.PATCH"
}
$NextVersion = "$($Matches[1]).$($Matches[2]).$([int]$Matches[3] + 1)"
Set-Content -Path $VersionFile -Value $NextVersion -Encoding utf8

$Manifest = Get-Content $ManifestFile -Raw
$Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
if ($Manifest -notmatch 'Versione corrente:') { throw "PROJECT_MANIFEST.md has an unexpected format" }
if ($Manifest -notmatch '\d{4}-\d{2}-\d{2} ') { throw "PROJECT_MANIFEST.md has an unexpected format" }
$Manifest = [regex]::Replace($Manifest, '(?m)^Versione corrente:.*$', "Versione corrente: ``$NextVersion``", 1)
$Manifest = [regex]::Replace($Manifest, '(?m)^\d{4}-\d{2}-\d{2} .*?$', $Timestamp, 1)
Set-Content -Path $ManifestFile -Value $Manifest -Encoding utf8

git add -A
$StagedFiles = git diff --cached --name-only
if ($StagedFiles -notcontains "VERSION") { throw "VERSION is not staged; refusing to commit" }
git commit -m "Update version to $NextVersion"
git push -u origin HEAD
git tag -a "v$NextVersion" -m "Release v$NextVersion"
git push origin "v$NextVersion"