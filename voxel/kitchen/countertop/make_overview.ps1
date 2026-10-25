$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$batchRoot = $PSScriptRoot
$startedAt = [DateTimeOffset]::UtcNow
$items = @(
    @('stand_mixer', 'Stand mixer'),
    @('espresso_machine', 'Espresso machine'),
    @('toaster', 'Two-slot toaster'),
    @('blender', 'Countertop blender'),
    @('stock_pot', 'Stock pot'),
    @('frying_pan', 'Frying pan'),
    @('cutting_board_knife', 'Cutting board + knife')
)
$bitmap = New-Object System.Drawing.Bitmap 1680,1040
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([System.Drawing.Color]::FromArgb(238,234,222))
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$ink = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(48,56,57))
$sage = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(75,105,91))
$white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(247,244,236))
$heading = New-Object System.Drawing.Font 'Segoe UI',28,([System.Drawing.FontStyle]::Bold)
$labelFont = New-Object System.Drawing.Font 'Segoe UI',18,([System.Drawing.FontStyle]::Bold)
$smallFont = New-Object System.Drawing.Font 'Segoe UI',11
$graphics.DrawString('KITCHEN / COUNTERTOP',$heading,$ink,24,12)
$graphics.DrawString('Seven native voxel models | Half resolution | Actual Blender previews',$smallFont,$sage,27,62)
$sources = @()
for ($i=0; $i -lt $items.Count; $i++) {
    $slug = $items[$i][0]
    $label = $items[$i][1]
    $x = 24 + ($i % 4) * 414
    $y = 102 + [math]::Floor($i / 4) * 460
    $imagePath = Join-Path $batchRoot "assets/$slug/half/preview.png"
    $metadata = Get-Content -LiteralPath (Join-Path $batchRoot "assets/$slug/half/metadata.json") -Raw | ConvertFrom-Json
    $picture = [System.Drawing.Image]::FromFile($imagePath)
    if ($picture.Width -ne 768 -or $picture.Height -ne 768) { throw "Wrong native preview dimensions for $slug" }
    $graphics.FillRectangle($white,$x,$y,396,442)
    $graphics.DrawImage($picture,[System.Drawing.Rectangle]::new($x+6,$y+6,384,384))
    $graphics.DrawString($label,$labelFont,$ink,$x+12,$y+391)
    $detail = ($metadata.grid_size -join ' x ') + ' cells | ' + $metadata.occupied_voxels.ToString('N0') + ' occupied'
    $graphics.DrawString($detail,$smallFont,$sage,$x+13,$y+421)
    $picture.Dispose()
    $sources += @{
        asset=$slug
        path="assets/$slug/half/preview.png"
        source_sha256=(Get-FileHash -LiteralPath $imagePath -Algorithm SHA256).Hash.ToLowerInvariant()
        destination_rect=@(($x+6),($y+6),384,384)
    }
}
$graphics.DrawString('HALF SIZE',$labelFont,$sage,1280,610)
$graphics.DrawString("Longest grid axis: 64 voxels`nDouble meters per voxel`nSame physical grid extents`n`nCream / sage / warm oak`nOpaque blue-gray glass`n`nNative VOX + PNG only",$smallFont,$ink,1282,651)
$graphics.DrawString('Each tile is the actual saved half-resolution model, rendered independently with the same camera bounds as its large version.',$smallFont,$sage,27,1010)
$outPath = Join-Path $batchRoot 'overview_half.png'
$bitmap.Save($outPath,[System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
foreach ($item in @($ink,$sage,$white,$heading,$labelFont,$smallFont)) { $item.Dispose() }
$finishedAt = [DateTimeOffset]::UtcNow
$manifest = @{
    type='contact sheet assembled from actual render files'
    started_at_utc=$startedAt.ToString('o')
    finished_at_utc=$finishedAt.ToString('o')
    elapsed_seconds=($finishedAt-$startedAt).TotalSeconds
    size=@(1680,1040)
    source_count=7
    sources=$sources
    sha256=(Get-FileHash -LiteralPath $outPath -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $batchRoot 'overview_half.json') -Encoding UTF8
Write-Output "CONTACT_SHEET_COMPLETE $outPath"
