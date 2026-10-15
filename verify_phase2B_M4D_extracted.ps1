$ErrorActionPreference = "Stop"

$Root = Join-Path `
    $env:USERPROFILE `
    "Downloads\phase2B_M4D_FOLD_2_DEBERTA\phase2B_M4D_FOLD_2_DEBERTA"

$RegistryPath = Join-Path $Root "SHA256SUMS.txt"
$ManifestPath = Join-Path $Root "fold_2_manifest.json"

$ExpectedRegistryHash = `
    "d6d40fad8ead80c137f6bff8ff280bd5679c2cc61d442ccdd555c552f7da8254"
$ExpectedManifestHash = `
    "bd54e98efff90af35b199a55e264055c446cc7f0628fbedc0b3462d1a2aeb1c7"

if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "STOP - extracted Fold-2 artifact directory was not found: $Root"
}

if (-not (Test-Path -LiteralPath $RegistryPath -PathType Leaf)) {
    throw "STOP - SHA256SUMS.txt is missing."
}

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "STOP - fold_2_manifest.json is missing."
}

$ActualRegistryHash = (
    Get-FileHash -LiteralPath $RegistryPath -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualRegistryHash -ne $ExpectedRegistryHash) {
    throw "STOP - SHA256SUMS.txt does not match the frozen M4D output."
}

$ActualManifestHash = (
    Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualManifestHash -ne $ExpectedManifestHash) {
    throw "STOP - fold_2_manifest.json does not match the frozen M4D output."
}

$Verified = 0
$Lines = Get-Content -LiteralPath $RegistryPath

foreach ($Line in $Lines) {
    if ([string]::IsNullOrWhiteSpace($Line)) {
        continue
    }

    if ($Line -notmatch "^([0-9a-fA-F]{64})  (.+)$") {
        throw "STOP - invalid SHA256SUMS entry: $Line"
    }

    $ExpectedFileHash = $Matches[1].ToLowerInvariant()
    $RelativePath = $Matches[2]
    $LocalRelativePath = $RelativePath.Replace(
        "/",
        [System.IO.Path]::DirectorySeparatorChar
    )
    $FilePath = Join-Path $Root $LocalRelativePath

    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        throw "STOP - registry file is missing: $RelativePath"
    }

    $ActualFileHash = (
        Get-FileHash -LiteralPath $FilePath -Algorithm SHA256
    ).Hash.ToLowerInvariant()

    if ($ActualFileHash -ne $ExpectedFileHash) {
        throw "STOP - checksum mismatch: $RelativePath"
    }

    $Verified += 1
    Write-Host "PASS - $RelativePath"
}

if ($Verified -ne 15) {
    throw "STOP - expected 15 registry entries; verified $Verified."
}

$AllFiles = @(
    Get-ChildItem -LiteralPath $Root -File -Recurse
)

if ($AllFiles.Count -ne 16) {
    throw "STOP - expected 16 total artifact files; found $($AllFiles.Count)."
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json

if ($Manifest.step -ne "M4D") {
    throw "STOP - manifest step is not M4D."
}

if ($Manifest.fold.test_fold -ne 2) {
    throw "STOP - manifest test fold is not 2."
}

Write-Host ""
Write-Host "Artifact root:       $Root"
Write-Host "Registry SHA256:     $ActualRegistryHash"
Write-Host "Manifest SHA256:     $ActualManifestHash"
Write-Host "Manifest payload:    $($Manifest.manifest_payload_sha256)"
Write-Host "Files verified:      $Verified registry files"
Write-Host "Total artifact files: $($AllFiles.Count)"
Write-Host ""
Write-Host `
    "PASS - extracted Fold-2 artifact is internally complete and checksum-valid." `
    -ForegroundColor Green
