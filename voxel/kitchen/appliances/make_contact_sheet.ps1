$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$batchRoot = $PSScriptRoot
$sheet = New-Object System.Drawing.Bitmap 1600,1000
$graphics = [System.Drawing.Graphics]::FromImage($sheet)
$graphics.Clear([System.Drawing.Color]::FromArgb(244,239,225))
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$darkBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(48,56,57))
$sageBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(75,105,91))
$cardBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(232,225,205))
$titleFont = New-Object System.Drawing.Font 'Segoe UI',28,([System.Drawing.FontStyle]::Bold),([System.Drawing.GraphicsUnit]::Pixel)
$nameFont = New-Object System.Drawing.Font 'Segoe UI',20,([System.Drawing.FontStyle]::Bold),([System.Drawing.GraphicsUnit]::Pixel)
$smallFont = New-Object System.Drawing.Font 'Segoe UI',15,([System.Drawing.FontStyle]::Regular),([System.Drawing.GraphicsUnit]::Pixel)
$graphics.DrawString('KITCHEN  /  APPLIANCES', $titleFont, $sageBrush, 32, 20)
$graphics.DrawString('Half resolution native voxels - actual Cycles renders from saved VOX files', $smallFont, $darkBrush, 32, 58)
$items = @(
  @('double_door_fridge', 'Double-door fridge'),
  @('range_oven', 'Range and oven'),
  @('microwave', 'Microwave'),
  @('dishwasher', 'Open dishwasher'),
  @('range_hood', 'Range hood'),
  @('rice_cooker', 'Rice cooker'),
  @('electric_kettle', 'Electric kettle')
)
for ($i = 0; $i -lt $items.Count; $i++) {
  $col = $i % 4
  $row = [math]::Floor($i / 4)
  $left = 32 + $col * 388
  $top = 92 + $row * 440
  $graphics.FillRectangle($cardBrush, $left, $top, 372, 424)
  $assetFolder = Join-Path $batchRoot ('assets/' + $items[$i][0] + '/half')
  $preview = [System.Drawing.Image]::FromFile((Join-Path $assetFolder 'preview.png'))
  $graphics.DrawImage($preview, [System.Drawing.Rectangle]::new($left+8,$top+8,356,356))
  $preview.Dispose()
  $meta = Get-Content -LiteralPath (Join-Path $assetFolder 'metadata.json') -Raw | ConvertFrom-Json
  $graphics.DrawString($items[$i][1], $nameFont, $darkBrush, $left+12, $top+369)
  $gridLabel = ($meta.grid_size -join ' x ') + ' vox  |  ' + [math]::Round($meta.voxel_size_m * 1000, 2) + ' mm cell'
  $graphics.DrawString($gridLabel, $smallFont, $sageBrush, $left+12, $top+398)
}
$graphics.DrawString('7 appliances', $titleFont, $sageBrush, 1220, 635)
$graphics.DrawString("Large + half native VOX`nNo saved scene or mesh exports`nCream / sage / charcoal`nOpaque blue-gray glass`n768 px source previews", $nameFont, $darkBrush, 1220, 686)
$graphics.DrawString('The studio ground is render-only. Objects have individual real-world scales.', $smallFont, $darkBrush, 32, 972)
$sheet.Save((Join-Path $batchRoot 'overview_half.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$sheet.Dispose()
$darkBrush.Dispose()
$sageBrush.Dispose()
$cardBrush.Dispose()
$titleFont.Dispose()
$nameFont.Dispose()
$smallFont.Dispose()
Write-Output 'overview_half.png written from seven actual half-resolution previews.'
