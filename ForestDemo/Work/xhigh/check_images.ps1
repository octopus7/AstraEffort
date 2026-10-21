$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$taskImageRoot = 'D:\github\AstraEffort\ForestDemo\Work\xhigh\Screenshots'
$taskImageStats = @()
foreach ($taskImageName in @('overview','top_down','lake','beach')) {
    $taskImagePath = Join-Path $taskImageRoot ($taskImageName + '.png')
    $taskBitmap = [Drawing.Bitmap]::new($taskImagePath)
    try {
        $taskSamples = [Collections.Generic.List[double]]::new()
        $taskAlphaMin = 255
        for ($taskY=0; $taskY -lt $taskBitmap.Height; $taskY+=24) {
            for ($taskX=0; $taskX -lt $taskBitmap.Width; $taskX+=24) {
                $taskPixel=$taskBitmap.GetPixel($taskX,$taskY)
                $taskSamples.Add(($taskPixel.R+$taskPixel.G+$taskPixel.B)/3.0)
                $taskAlphaMin=[math]::Min($taskAlphaMin,$taskPixel.A)
            }
        }
        $taskMeasure=$taskSamples | Measure-Object -Minimum -Maximum -Average
        $taskImageStats += [ordered]@{ name=$taskImageName; width=$taskBitmap.Width; height=$taskBitmap.Height; samples=$taskSamples.Count; rgb_average=$taskMeasure.Average; rgb_min=$taskMeasure.Minimum; rgb_max=$taskMeasure.Maximum; alpha_min=$taskAlphaMin; non_uniform=($taskMeasure.Maximum-$taskMeasure.Minimum -gt 20); bytes=(Get-Item -LiteralPath $taskImagePath).Length }
    } finally { $taskBitmap.Dispose() }
}
$taskImageStats | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskImageRoot 'image_stats.json') -Encoding utf8
$taskImageStats | ConvertTo-Json -Depth 4
