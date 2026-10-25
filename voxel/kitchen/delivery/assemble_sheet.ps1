$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$assemblyStarted = [datetime]::UtcNow
$assemblyWatch = [System.Diagnostics.Stopwatch]::StartNew()
$deliveryRoot = $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $deliveryRoot 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.models.Count -ne 20) { throw 'Expected exactly 20 model records.' }
$sheet = New-Object System.Drawing.Bitmap 2000,1900
$canvas = [System.Drawing.Graphics]::FromImage($sheet)
$canvas.Clear([System.Drawing.Color]::FromArgb(244,239,225))
$canvas.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$canvas.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$dark = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(48,56,57))
$sage = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(75,105,91))
$card = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(232,225,205))
$titleFont = New-Object System.Drawing.Font 'Segoe UI',32,([System.Drawing.FontStyle]::Bold),([System.Drawing.GraphicsUnit]::Pixel)
$nameFont = New-Object System.Drawing.Font 'Segoe UI',18,([System.Drawing.FontStyle]::Bold),([System.Drawing.GraphicsUnit]::Pixel)
$smallFont = New-Object System.Drawing.Font 'Segoe UI',14,([System.Drawing.FontStyle]::Regular),([System.Drawing.GraphicsUnit]::Pixel)
$canvas.DrawString('KITCHEN  /  20 NATIVE VOXEL MODELS', $titleFont, $sage, 28, 18)
$canvas.DrawString('Final half-resolution previews - actual renders from saved native VOX files', $smallFont, $dark, 28, 61)
$canvas.DrawString('Each panel uses individual camera framing. Panels do not share a physical scale.', $smallFont, $dark, 28, 83)
$tileRecords = @()
for ($i = 0; $i -lt 20; $i++) {
    $model = $manifest.models[$i]
    $column = $i % 5
    $row = [math]::Floor($i / 5)
    $left = 28 + $column * 392
    $top = 112 + $row * 440
    $canvas.FillRectangle($card, $left, $top, 376, 424)
    $source = Join-Path $deliveryRoot $model.variants.half.preview.path
    $picture = [System.Drawing.Image]::FromFile($source)
    if ($picture.Width -ne 768 -or $picture.Height -ne 768) { throw "Unexpected source image size: $source" }
    $canvas.DrawImage($picture, [System.Drawing.Rectangle]::new($left+12,$top+12,352,352))
    $picture.Dispose()
    $canvas.DrawString($model.slug, $nameFont, $dark, $left+12, $top+371)
    $subtitle = $model.batch + '  |  ' + ($model.variants.half.grid_size -join ' x ') + ' vox'
    $canvas.DrawString($subtitle, $smallFont, $sage, $left+12, $top+397)
    $tileRecords += [ordered]@{ index=$i; row=$row; column=$column; slug=$model.slug; source=$model.variants.half.preview.path; source_sha256=$model.variants.half.preview.sha256; rectangle=@(($left+12),($top+12),352,352); crop='none - complete original image' }
}
$canvas.DrawString('20 models  |  40 native VOX files  |  40 original 768px previews preserved  |  Cream, sage, oak and charcoal palette', $smallFont, $dark, 28, 1875)
$sheet.Save((Join-Path $deliveryRoot 'overview_half.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$canvas.Dispose()
$sheet.Dispose()
$dark.Dispose()
$sage.Dispose()
$card.Dispose()
$titleFont.Dispose()
$nameFont.Dispose()
$smallFont.Dispose()
$assemblyWatch.Stop()
$record = [ordered]@{ started_at_utc=$assemblyStarted.ToString('o'); finished_at_utc=[datetime]::UtcNow.ToString('o'); elapsed_seconds=$assemblyWatch.Elapsed.TotalSeconds; method='System.Drawing composition of unchanged actual source PNGs'; columns=5; rows=4; size_px=@(2000,1900); source_images=20; render_invoked=$false; original_images_modified=$false; tiles=$tileRecords }
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $deliveryRoot 'composition.json') -Encoding UTF8
Write-Output 'Composed all 20 complete source images into overview_half.png (5 columns x 4 rows).'
