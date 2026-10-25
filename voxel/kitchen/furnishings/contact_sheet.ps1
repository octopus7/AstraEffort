$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$batchRoot = $PSScriptRoot
$entries = @(
    @('sink_cabinet', 'Sink cabinet'),
    @('kitchen_island', 'Kitchen island'),
    @('dish_cabinet', 'Dish cabinet'),
    @('kitchen_cart', 'Kitchen cart'),
    @('dish_drying_rack', 'Dish drying rack'),
    @('knife_block', 'Knife block')
)
$sheet = New-Object System.Drawing.Bitmap 1560, 1200
$graphics = [System.Drawing.Graphics]::FromImage($sheet)
$graphics.Clear([System.Drawing.Color]::FromArgb(239, 236, 226))
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(48, 56, 57))
$title = New-Object System.Drawing.Font 'Segoe UI', 26, ([System.Drawing.FontStyle]::Bold)
$label = New-Object System.Drawing.Font 'Segoe UI', 18, ([System.Drawing.FontStyle]::Bold)
$small = New-Object System.Drawing.Font 'Segoe UI', 12
$graphics.DrawString('Kitchen Furnishings | Half resolution', $title, $brush, 24, 14)
$graphics.DrawString('Six native voxel models | Actual Blender Cycles previews | Longest grid axis: 64', $small, $brush, 26, 59)
for ($i = 0; $i -lt $entries.Count; $i++) {
    $slug = $entries[$i][0]
    $text = $entries[$i][1]
    $col = $i % 3
    $row = [Math]::Floor($i / 3)
    $x = 20 + 520 * $col
    $y = 94 + 548 * $row
    $path = Join-Path $batchRoot ('assets\' + $slug + '\half\preview.png')
    $sourceImage = [System.Drawing.Image]::FromFile($path)
    $graphics.DrawImage($sourceImage, [int]$x, [int]$y, 500, 500)
    $sourceImage.Dispose()
    $graphics.DrawString($text, $label, $brush, [single]($x + 6), [single]($y + 504))
}
$outputPath = Join-Path $batchRoot 'overview_half.png'
$sheet.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$sheet.Dispose()
$brush.Dispose()
$title.Dispose()
$label.Dispose()
$small.Dispose()
Write-Output $outputPath
