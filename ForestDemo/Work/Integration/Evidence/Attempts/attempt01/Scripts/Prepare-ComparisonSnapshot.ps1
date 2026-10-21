param(
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{40}$')][string]$BaselineCommit,
    [ValidatePattern('^[a-z0-9-]+$')][string]$SnapshotLabel = 'comparison',
    [switch]$ApplyFinalDefaults
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$repoRoot = Split-Path -Parent $projectRoot
$workersRoot = Join-Path $projectRoot 'Saved/Workers/Supervisor'
$scratch = [IO.Path]::GetFullPath((Join-Path $workersRoot ('Integration-' + $BaselineCommit + '-' + $SnapshotLabel)))
if (!$scratch.StartsWith([IO.Path]::GetFullPath($workersRoot) + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe scratch path' }
if (Test-Path -LiteralPath $scratch) { throw "Scratch already exists; preserve it and inspect before reuse: $scratch" }
$resolved = (& git -C $repoRoot rev-parse --verify ($BaselineCommit + '^{commit}')).Trim()
if ($LASTEXITCODE -ne 0 -or $resolved -ne $BaselineCommit) { throw 'Commit could not be resolved exactly' }
$private = Join-Path $scratch 'Project'
$evidence = Join-Path $scratch 'Evidence'
[IO.Directory]::CreateDirectory($private) | Out-Null
[IO.Directory]::CreateDirectory($evidence) | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
function Write-Json($path, $value) { [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 14) + "`n", $utf8) }
function Inventory($base, $subpaths) {
    $rows = @(foreach ($relative in $subpaths) {
        $target = Join-Path $base $relative
        if (Test-Path -LiteralPath $target -PathType Leaf) { $files = @(Get-Item -LiteralPath $target) }
        elseif (Test-Path -LiteralPath $target -PathType Container) { $files = @(Get-ChildItem -LiteralPath $target -File -Recurse) }
        else { throw "Required snapshot path missing: $target" }
        foreach ($file in $files) {
            [ordered]@{ path = [IO.Path]::GetRelativePath($base, $file.FullName).Replace('\','/'); bytes = $file.Length; sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
        }
    })
    return @($rows | Sort-Object path)
}
$archive = Join-Path $scratch 'baseline.tar'
& git -C $repoRoot archive --format=tar ('--output=' + $archive) ($resolved + ':ForestDemo') ForestDemo.uproject Config Source Content
if ($LASTEXITCODE -ne 0) { throw 'git archive failed' }
& tar -xf $archive -C $private
if ($LASTEXITCODE -ne 0) { throw 'Archive extraction failed' }
$scope = @('ForestDemo.uproject','Config','Source','Content')
$baseline = Inventory $private $scope
Write-Json (Join-Path $evidence 'baseline_snapshot.json') ([ordered]@{commit=$resolved;created_at_utc=[DateTimeOffset]::UtcNow.ToString('o');archive_sha256=(Get-FileHash -LiteralPath $archive).Hash.ToLowerInvariant();files=$baseline})

# The baseline native module has not changed since initial project creation.
# Refuse to seed it if any current shared native source differs from this commit.
$frozenSource = Inventory $private @('Source')
$sharedSource = Inventory $projectRoot @('Source')
if (Compare-Object @($frozenSource.path) @($sharedSource.path)) { throw 'Shared native Source file set differs from committed baseline' }
$sourceCorrespondence = @(foreach ($file in $frozenSource) {
    $frozenText = [IO.File]::ReadAllText((Join-Path $private $file.path)).Replace("`r`n","`n")
    $sharedText = [IO.File]::ReadAllText((Join-Path $projectRoot $file.path)).Replace("`r`n","`n")
    if ($frozenText -cne $sharedText) { throw "Shared native source differs beyond line endings: $($file.path)" }
    $canonicalHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($frozenText))).ToLowerInvariant()
    [ordered]@{path=$file.path;committed_raw_sha256=$file.sha256;shared_raw_sha256=($sharedSource|Where-Object path -eq $file.path).sha256;canonical_lf_utf8_sha256=$canonicalHash;equal_after_line_ending_normalization=$true}
})
$binaryNames = @('UnrealEditor-ForestDemo.dll','UnrealEditor-ForestDemo.pdb','UnrealEditor.modules','ForestDemoEditor.target')
$seed = Join-Path $projectRoot 'Binaries/Win64'
$destination = Join-Path $private 'Binaries/Win64'
[IO.Directory]::CreateDirectory($destination) | Out-Null
$moduleRecord = Get-Content -LiteralPath (Join-Path $seed 'UnrealEditor.modules') -Raw | ConvertFrom-Json
if (@($moduleRecord.Modules.PSObject.Properties.Name).Count -ne 1 -or $moduleRecord.Modules.ForestDemo -ne 'UnrealEditor-ForestDemo.dll') { throw 'Unexpected native module seed' }
$binaries = @(foreach ($name in $binaryNames) {
    $from = Join-Path $seed $name; $to = Join-Path $destination $name
    $hash = (Get-FileHash -LiteralPath $from).Hash.ToLowerInvariant()
    Copy-Item -LiteralPath $from -Destination $to
    if ((Get-FileHash -LiteralPath $to).Hash.ToLowerInvariant() -ne $hash) { throw "Binary copy mismatch: $name" }
    [ordered]@{name=$name;seed=$from;sha256=$hash;last_write_utc=(Get-Item -LiteralPath $from).LastWriteTimeUtc.ToString('o')}
})
$sourceCommit = (& git -C $repoRoot log -1 --format=%H $resolved -- ForestDemo/Source).Trim()
Write-Json (Join-Path $evidence 'native_binary_seed.json') ([ordered]@{source_commit=$sourceCommit;canonical_source_hashes_equal=$true;source_normalization='UTF-8 text with CRLF normalized to LF; raw hashes retained separately';source_files=$sourceCorrespondence;module_build_id=$moduleRecord.BuildId;binaries=$binaries;limitation='Source correspondence and existing baseline binary identities are recorded. This is not reproducible-build proof; native Hello automation must pass in the isolated project.'})

if ($ApplyFinalDefaults) {
    $config = Join-Path $private 'Config/DefaultEngine.ini'
    $text = [IO.File]::ReadAllText($config)
    foreach ($key in @('EditorStartupMap','GameDefaultMap')) {
        $pattern = '(?m)^' + $key + '=[^\r\n]*'
        if ([regex]::Matches($text,$pattern).Count -ne 1) { throw "Expected exactly one $key" }
        $text = [regex]::Replace($text,$pattern,($key+'=/Game/Maps/medium'))
    }
    [IO.File]::WriteAllText($config,$text,$utf8)
    $retired = [IO.Path]::GetFullPath((Join-Path $private 'Content/Maps/main.umap'))
    if ($retired -ne [IO.Path]::GetFullPath((Join-Path $scratch 'Project/Content/Maps/main.umap'))) { throw 'Unexpected main-map path' }
    if (!(Test-Path -LiteralPath $retired -PathType Leaf)) { throw 'Baseline main.umap missing' }
    Remove-Item -LiteralPath $retired
}
$candidate = Inventory $private $scope
$old = @{}; foreach ($f in $baseline) { $old[$f.path]=$f.sha256 }
$new = @{}; foreach ($f in $candidate) { $new[$f.path]=$f.sha256 }
$changes = @(foreach ($path in @(@($old.Keys)+@($new.Keys) | Sort-Object -Unique)) {
    if ($old[$path] -ne $new[$path]) { [ordered]@{path=$path;before=$old[$path];after=$new[$path]} }
})
if ($ApplyFinalDefaults -and (($changes.path | Sort-Object) -join '|') -ne 'Config/DefaultEngine.ini|Content/Maps/main.umap') { throw 'Unexpected candidate changes' }
$expected = @('medium','high','xhigh','ultra','MountainStation_medium','MountainStation_high','MountainStation_xhigh','MountainStation_ultra')
$mapNames = @(Get-ChildItem -LiteralPath (Join-Path $private 'Content/Maps') -File -Recurse -Filter '*.umap' | ForEach-Object BaseName)
if ($ApplyFinalDefaults -and (Compare-Object ($expected|Sort-Object) ($mapNames|Sort-Object))) { throw 'Expected exactly eight maps' }
Write-Json (Join-Path $evidence 'candidate_snapshot.json') ([ordered]@{commit=$resolved;created_at_utc=[DateTimeOffset]::UtcNow.ToString('o');changes=$changes;files=$candidate})
$engine = 'C:/Program Files/Epic Games/UE_5.7/Engine'
$engineModules = @(foreach ($tree in @('Source','Plugins')) { Get-ChildItem -LiteralPath (Join-Path $engine $tree) -Recurse -File -Filter '*.Build.cs' | ForEach-Object { $_.Name -replace '\.Build\.cs$','' } }) | Sort-Object -Unique
$request = [ordered]@{baseline_commit=$resolved;project=$private;engine=$engine;evidence=$evidence;candidate_manifest=(Join-Path $evidence 'candidate_snapshot.json');engine_script_modules=@($engineModules);expected_maps=$expected;expected_default_map='/Game/Maps/medium';final_defaults_applied=[bool]$ApplyFinalDefaults}
Write-Json (Join-Path $scratch 'request.json') $request
Write-Output ([ordered]@{scratch=$scratch;request=(Join-Path $scratch 'request.json');baseline_commit=$resolved;candidate_change_count=$changes.Count;ue_launched=$false} | ConvertTo-Json)
