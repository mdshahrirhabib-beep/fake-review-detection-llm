$ErrorActionPreference = "Stop"

$Root = Join-Path `
    $env:USERPROFILE `
    "Downloads\phase2B_M4D_FOLD_2_DEBERTA\phase2B_M4D_FOLD_2_DEBERTA"

$RegistryPath = Join-Path $Root "SHA256SUMS.txt"
$ManifestPath = Join-Path $Root "fold_2_manifest.json"

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

$ActualManifestHash = (
    Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256
).Hash.ToLowerInvariant()

$Verified = 0
$Registry = @{}
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

    if ($Registry.ContainsKey($RelativePath)) {
        throw "STOP - duplicate SHA256SUMS entry: $RelativePath"
    }

    $Registry[$RelativePath] = $ExpectedFileHash
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

if (-not $Registry.ContainsKey("fold_2_manifest.json")) {
    throw "STOP - manifest is absent from SHA256SUMS.txt."
}

if ($Registry["fold_2_manifest.json"] -ne $ActualManifestHash) {
    throw "STOP - manifest hash differs from SHA256SUMS.txt."
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

if ($Manifest.status -ne "FROZEN_FOLD_2_DEBERTA_COMPLETE") {
    throw "STOP - manifest completion status differs."
}

if ($Manifest.fold.seed -ne 44) {
    throw "STOP - manifest seed is not 44."
}

if (
    $Manifest.fold.train_n -ne 1917 -or
    $Manifest.fold.test_n -ne 479 -or
    $Manifest.fold.llama_test_n -ne 158
) {
    throw "STOP - manifest Fold-2 row counts differ."
}

if (
    $Manifest.training.epochs -ne 4 -or
    $Manifest.training.total_optimizer_updates -ne 240 -or
    $Manifest.training.no_tuning -ne $true -or
    $Manifest.training.no_early_stopping -ne $true -or
    $Manifest.training.final_epoch_only -ne $true
) {
    throw "STOP - manifest training contract differs."
}

if (
    $Manifest.inference.primary_rows -ne 479 -or
    $Manifest.inference.llama_rows -ne 158 -or
    $Manifest.inference.one_time_final_epoch_inference -ne $true -or
    $Manifest.inference.test_used_for_tuning_or_selection -ne $false
) {
    throw "STOP - manifest inference contract differs."
}

$ExpectedUpstream = @{
    "t2_manifest_payload_sha256" = "b87c3945e0b50df788801c14cb9fcb2c88bf569e7c4556d9bfc168f8eb18cba8"
    "initialisation_manifest_payload_sha256" = "171154b7225ded4b88d0024a5ba20e2314bee3213dc0d16c3575a40bec13fd45"
    "m2_contract_payload_sha256" = "53fad9f300b6dbe6c10cc6951bfc746a3dd27415018d4da902ae2fccb8fda202"
    "m3a_manifest_payload_sha256" = "46118cc8794e5568a4cea30a930a17114c493e15cce5dc6b3947c007b1f5845e"
    "m4b_fold_1_manifest_payload_sha256" = "fc07453492cc661b7b2033613d868660ba34231c9f94bc9cdcbe841539d4d578"
}

foreach ($Name in $ExpectedUpstream.Keys) {
    if ($Manifest.upstream.$Name -ne $ExpectedUpstream[$Name]) {
        throw "STOP - upstream contract differs: $Name"
    }
}

$ArtifactEntries = @($Manifest.artifact_files.PSObject.Properties)

if ($ArtifactEntries.Count -ne 14) {
    throw "STOP - expected 14 manifest artifact entries; found $($ArtifactEntries.Count)."
}

foreach ($Property in $ArtifactEntries) {
    $RelativePath = $Property.Name
    $Identity = $Property.Value

    if (-not $Registry.ContainsKey($RelativePath)) {
        throw "STOP - manifest file is absent from SHA256SUMS: $RelativePath"
    }

    if ($Identity.sha256.ToLowerInvariant() -ne $Registry[$RelativePath]) {
        throw "STOP - manifest/registry hash differs: $RelativePath"
    }

    $LocalRelativePath = $RelativePath.Replace(
        "/",
        [System.IO.Path]::DirectorySeparatorChar
    )
    $FilePath = Join-Path $Root $LocalRelativePath

    if ([long]$Identity.bytes -ne (Get-Item -LiteralPath $FilePath).Length) {
        throw "STOP - manifest/file size differs: $RelativePath"
    }
}

Write-Host ""
Write-Host "Artifact root:       $Root"
Write-Host "Registry SHA256:     $ActualRegistryHash"
Write-Host "Manifest SHA256:     $ActualManifestHash"
Write-Host "Manifest payload:    $($Manifest.manifest_payload_sha256)"
Write-Host "Files verified:      $Verified registry files"
Write-Host "Total artifact files: $($AllFiles.Count)"
Write-Host "Artifact entries:     $($ArtifactEntries.Count)"
Write-Host ""
Write-Host `
    "PASS - extracted Fold-2 artifact is internally complete and checksum-valid." `
    -ForegroundColor Green
