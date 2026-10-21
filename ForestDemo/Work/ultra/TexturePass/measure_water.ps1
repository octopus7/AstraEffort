$ErrorActionPreference='Stop'
$taskRoot='D:\github\AstraEffort\ForestDemo\Work\ultra\TexturePass'
Add-Type -AssemblyName System.Drawing
$a=[Drawing.Bitmap]::FromFile((Join-Path $taskRoot 'Screenshots\water_t0.png'))
$b=[Drawing.Bitmap]::FromFile((Join-Path $taskRoot 'Screenshots\water_t1.png'))
try {
    if($a.Width-ne 1920 -or $a.Height-ne 1080 -or $b.Width-ne 1920 -or $b.Height-ne 1080){throw 'Unexpected water capture dimensions'}
    $count=0; $changed=0; $sum=0.0; $maximum=0
    for($y=0;$y-lt 1080;$y+=4){
        for($x=0;$x-lt 1920;$x+=4){
            $p=$a.GetPixel($x,$y);$q=$b.GetPixel($x,$y)
            $delta=[Math]::Abs([int]$p.R-[int]$q.R)+[Math]::Abs([int]$p.G-[int]$q.G)+[Math]::Abs([int]$p.B-[int]$q.B)
            $count++;$sum+=$delta;$maximum=[Math]::Max($maximum,$delta)
            if($delta-ge 12){$changed++}
        }
    }
    $manifest=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'Screenshots\capture_manifest.json')|ConvertFrom-Json -DateKind String
    $v0=$manifest.views|Where-Object name -eq water_t0
    $v1=$manifest.views|Where-Object name -eq water_t1
    $timeDelta=$v1.shader_world_time_seconds-$v0.shader_world_time_seconds
    $record=[ordered]@{method='Unmodified actual UE frames; every fourth pixel, sum absolute RGB byte difference. Temporal rendering noise may contribute; visual review must confirm moving water patterns.';first='Screenshots/water_t0.png';second='Screenshots/water_t1.png';utc_delta_seconds=([DateTimeOffset]::Parse($v1.captured_at_utc)-[DateTimeOffset]::Parse($v0.captured_at_utc)).TotalSeconds;shader_world_time_delta_seconds=$timeDelta;identical_camera=(($v0.location|ConvertTo-Json -Compress)-eq($v1.location|ConvertTo-Json -Compress))-and(($v0.rotation_pitch_yaw_roll|ConvertTo-Json -Compress)-eq($v1.rotation_pitch_yaw_roll|ConvertTo-Json -Compress));sample_count=$count;changed_samples_at_least_12_rgb=$changed;changed_percent=100*$changed/$count;mean_absolute_difference_per_channel=$sum/$count/3;maximum_sum_rgb_difference=$maximum;passed=($changed-gt 100 -and $timeDelta-gt 1)}
    $record|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $taskRoot 'water_motion_validation.json') -Encoding utf8
    $record|ConvertTo-Json -Depth 5
} finally {$a.Dispose();$b.Dispose()}

