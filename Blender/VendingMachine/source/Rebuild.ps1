param(
    [string]$Blender = 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe',
    [switch]$SkipBuild,
    [switch]$SkipFinalize,
    [switch]$SkipRenders
)
$assetRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$jobs = @()
if (-not $SkipBuild) { $jobs += 'build_vending' }
if (-not $SkipFinalize) { $jobs += 'finalize_vending' }
if (-not $SkipRenders) { $jobs += 'render_and_validate'; $jobs += 'verify_glb_geometry' }
foreach ($job in $jobs) {
    $scriptPath = Join-Path $PSScriptRoot ($job + '.py')
    $logPath = Join-Path $assetRoot ('logs/' + $job + '_rebuild.log')
    & $Blender --background --factory-startup --threads 4 --python $scriptPath *> $logPath
    if ($LASTEXITCODE -ne 0) { throw "$job failed. See $logPath" }
}
Write-Output "Asset pipeline completed in $assetRoot. Inspect the actual renders before distribution."
