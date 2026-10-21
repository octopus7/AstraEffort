$ErrorActionPreference = 'Stop'
$workRoot = 'D:\github\AstraEffort\ForestDemo\Work\ultra'
$scratchProject = 'D:\github\AstraEffort\ForestDemo\Saved\Workers\ultra\ForestDemo'
$finalAssets = 'D:\github\AstraEffort\ForestDemo\Content\Forest\ultra'
$finalMap = 'D:\github\AstraEffort\ForestDemo\Content\Maps\ultra.umap'
$validation = Get-Content -LiteralPath (Join-Path $workRoot 'validation.json') -Raw | ConvertFrom-Json
$runtime = Get-Content -LiteralPath (Join-Path $workRoot 'runtime_validation.json') -Raw | ConvertFrom-Json
$visual = Get-Content -LiteralPath (Join-Path $workRoot 'visual_review.json') -Raw | ConvertFrom-Json
if (!$validation.success -or !$runtime.success -or !$visual.approved) { throw 'Validation or author visual review has not passed.' }
$activeEditor = @(Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor-Cmd.exe'" | Where-Object { $_.CommandLine -like '*Saved\Workers\ultra\ForestDemo*' })
if ($activeEditor.Count -gt 0) { throw 'Private editor must be closed before publishing.' }
Add-Type -AssemblyName System.Drawing
$images = @()
foreach ($name in @('overview','top_down','lake','beach','hero')) {
    $path = Join-Path $workRoot "Screenshots\$name.png"
    $bitmap = [Drawing.Bitmap]::FromFile($path)
    try {
        if ($bitmap.Width -ne 1920 -or $bitmap.Height -ne 1080) { throw "Wrong resolution: $name" }
        $values = @()
        for ($y=20; $y -lt 1080; $y+=41) {
            for ($x=20; $x -lt 1920; $x+=43) {
                $pixel=$bitmap.GetPixel($x,$y)
                $values += ($pixel.R+$pixel.G+$pixel.B)/765.0
            }
        }
        $stats=$values | Measure-Object -Minimum -Maximum -Average
        if ($stats.Average -lt .01 -or ($stats.Maximum-$stats.Minimum) -lt .15) { throw "Blank/dark image: $name" }
        $imageHash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        if ($visual.image_sha256.$name -ne $imageHash) { throw "Image changed after author review: $name" }
        $images += [ordered]@{name=$name; width=$bitmap.Width; height=$bitmap.Height; sampled_mean=$stats.Average; sampled_min=$stats.Minimum; sampled_max=$stats.Maximum; sha256=$imageHash}
    } finally { $bitmap.Dispose() }
}
if (($images.sha256 | Select-Object -Unique).Count -ne 5) { throw 'Some camera images are identical.' }
$sourceAssets=Join-Path $scratchProject 'Content\Forest\ultra'
New-Item -ItemType Directory -Force -Path $finalAssets | Out-Null
Get-ChildItem -LiteralPath $sourceAssets | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $finalAssets -Recurse -Force }
Copy-Item -LiteralPath (Join-Path $scratchProject 'Content\Maps\ultra.umap') -Destination $finalMap -Force
$inventory=@()
Get-ChildItem -LiteralPath $sourceAssets -Recurse -File | ForEach-Object {
    $relative=[IO.Path]::GetRelativePath($sourceAssets,$_.FullName)
    $destination=Join-Path $finalAssets $relative
    $sourceHash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    $destinationHash=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
    if ($sourceHash -ne $destinationHash) { throw "Copy differs: $relative" }
    $inventory += [ordered]@{path=$destination;bytes=$_.Length;sha256=$destinationHash}
}
$mapHash=(Get-FileHash -LiteralPath $finalMap -Algorithm SHA256).Hash
if ($mapHash -ne (Get-FileHash -LiteralPath (Join-Path $scratchProject 'Content\Maps\ultra.umap') -Algorithm SHA256).Hash) { throw 'Map copy differs.' }
$inventory += [ordered]@{path=$finalMap;bytes=(Get-Item -LiteralPath $finalMap).Length;sha256=$mapHash}
$record=[ordered]@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o');private_editor_closed=$true;files=$inventory;images=$images;verified_copy=$true}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $workRoot 'publication.json') -Encoding utf8
Write-Output "Published and hash-verified $($inventory.Count) files; 5 distinct 1920x1080 render images verified."
