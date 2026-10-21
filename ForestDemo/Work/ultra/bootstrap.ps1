$ErrorActionPreference = 'Stop'
$repoRoot = 'D:\github\AstraEffort'
$scratchRoot = Join-Path $repoRoot 'ForestDemo\Saved\Workers\ultra'
$projectRoot = Join-Path $scratchRoot 'ForestDemo'
New-Item -ItemType Directory -Force -Path $projectRoot, (Join-Path $scratchRoot 'logs'), (Join-Path $projectRoot 'Content') | Out-Null
$baselinePaths = git -C $repoRoot ls-tree -r --name-only 7558c8f -- ForestDemo/Source ForestDemo/Config ForestDemo/ForestDemo.uproject
foreach ($relativePath in $baselinePaths) {
    $destination = Join-Path $scratchRoot $relativePath
    New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
    $content = git -C $repoRoot show "7558c8f:$relativePath"
    [IO.File]::WriteAllText($destination, ($content -join "`n"), (New-Object Text.UTF8Encoding($false)))
}
Copy-Item -LiteralPath (Join-Path $repoRoot 'ForestDemo\Binaries') -Destination (Join-Path $projectRoot 'Binaries') -Recurse -Force
$engineConfig = Join-Path $projectRoot 'Config\DefaultEngine.ini'
Add-Content -LiteralPath $engineConfig -Value "`n[/Script/Engine.RendererSettings]`nr.AllowStaticLighting=False`nr.DynamicGlobalIlluminationMethod=1`nr.ReflectionMethod=1`nr.Shadow.Virtual.Enable=1`n"
Write-Output $projectRoot
