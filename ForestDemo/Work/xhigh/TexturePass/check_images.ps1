$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$taskDir='D:\github\AstraEffort\ForestDemo\Work\xhigh\TexturePass\Screenshots'
$taskStats=@()
foreach($taskName in @('overview','top_down','lake','beach','water_t0','water_t1')) {
 $taskPath=Join-Path $taskDir ($taskName+'.png')
 $taskBmp=[Drawing.Bitmap]::new($taskPath)
 try {
  $taskValues=[Collections.Generic.List[double]]::new();$taskAlpha=255
  for($taskY=0;$taskY -lt $taskBmp.Height;$taskY+=12){for($taskX=0;$taskX -lt $taskBmp.Width;$taskX+=12){
   $taskPixel=$taskBmp.GetPixel($taskX,$taskY);$taskValues.Add(($taskPixel.R+$taskPixel.G+$taskPixel.B)/3.0);$taskAlpha=[math]::Min($taskAlpha,$taskPixel.A)
  }}
  $taskM=$taskValues|Measure-Object -Minimum -Maximum -Average
  $taskStats += [ordered]@{name=$taskName;width=$taskBmp.Width;height=$taskBmp.Height;rgb_average=$taskM.Average;rgb_min=$taskM.Minimum;rgb_max=$taskM.Maximum;alpha_min=$taskAlpha;non_uniform=($taskM.Maximum-$taskM.Minimum -gt 20);sha256=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash}
 }finally{$taskBmp.Dispose()}
}
$taskA=[Drawing.Bitmap]::new((Join-Path $taskDir 'water_t0.png'));$taskB=[Drawing.Bitmap]::new((Join-Path $taskDir 'water_t1.png'))
try{
 $taskDelta=0.0;$taskChanged=0;$taskCount=0;$taskMax=0
 for($taskY=0;$taskY -lt $taskA.Height;$taskY+=4){for($taskX=0;$taskX -lt $taskA.Width;$taskX+=4){
  $taskP=$taskA.GetPixel($taskX,$taskY);$taskQ=$taskB.GetPixel($taskX,$taskY)
  $taskD=([math]::Abs([int]$taskP.R-[int]$taskQ.R)+[math]::Abs([int]$taskP.G-[int]$taskQ.G)+[math]::Abs([int]$taskP.B-[int]$taskQ.B))/3.0
  $taskDelta+=$taskD;$taskMax=[math]::Max($taskMax,$taskD);$taskCount++;if($taskD -gt 8){$taskChanged++}
 }}
 $taskManifest=Get-Content -LiteralPath (Join-Path $taskDir 'capture_manifest.json') -Raw | ConvertFrom-Json -DateKind String
 $taskV0=$taskManifest.views|Where-Object name -eq water_t0;$taskV1=$taskManifest.views|Where-Object name -eq water_t1
 $taskSeconds=([DateTimeOffset]::Parse($taskV1.captured_at_utc)-[DateTimeOffset]::Parse($taskV0.captured_at_utc)).TotalSeconds
 $taskEvidence=[ordered]@{same_camera=(($taskV0.position_cm|ConvertTo-Json -Compress) -eq ($taskV1.position_cm|ConvertTo-Json -Compress));elapsed_capture_seconds=$taskSeconds;world_time_delta_seconds=($taskV1.render_world_time_seconds-$taskV0.render_world_time_seconds);sampled_pixels=$taskCount;sample_stride=4;mean_absolute_rgb_difference=($taskDelta/$taskCount);max_absolute_rgb_difference=$taskMax;fraction_pixels_difference_over_8=($taskChanged/$taskCount);passed=($taskChanged/$taskCount -gt .03 -and $taskSeconds -ge 8);method='Read-only pixel comparison of actual untouched UE renders; no image editing'}
}finally{$taskA.Dispose();$taskB.Dispose()}
$taskStats|ConvertTo-Json -Depth 6|Set-Content -Encoding utf8 -LiteralPath (Join-Path $taskDir 'image_stats.json')
$taskEvidence|ConvertTo-Json -Depth 6|Set-Content -Encoding utf8 -LiteralPath (Join-Path $taskDir 'water_animation_evidence.json')
$taskEvidence|ConvertTo-Json -Depth 6
