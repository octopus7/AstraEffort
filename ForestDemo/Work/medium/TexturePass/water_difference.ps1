$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$root='D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass'
$a=[Drawing.Bitmap]::FromFile("$root/Screenshots/water_t0.png")
$b=[Drawing.Bitmap]::FromFile("$root/Screenshots/water_t1.png")
function Compare-Region($x0,$y0,$w,$h){
 $sum=0.0;$changed=0;$maximum=0
 for($y=$y0;$y -lt ($y0+$h);$y+=2){for($x=$x0;$x -lt ($x0+$w);$x+=2){$ca=$a.GetPixel($x,$y);$cb=$b.GetPixel($x,$y);$delta=([Math]::Abs([int]$ca.R-$cb.R)+[Math]::Abs([int]$ca.G-$cb.G)+[Math]::Abs([int]$ca.B-$cb.B))/3.0;$sum+=$delta;if($delta -gt 8){$changed++};$maximum=[Math]::Max($maximum,$delta)}}
 $count=($w/2)*($h/2)
 return @{region_xywh=@($x0,$y0,$w,$h);sampling_stride=2;mean_absolute_rgb_byte_difference=$sum/$count;fraction_pixels_above_8=$changed/$count;maximum_rgb_byte_difference=$maximum}
}
# This rectangle lies inside visible sea in the verified common beach camera.
$water=Compare-Region 1320 600 500 160
$sky=Compare-Region 800 160 500 160
$a.Dispose();$b.Dispose()
$manifest=Get-Content "$root/Screenshots/capture_manifest.json" -Raw|ConvertFrom-Json
$t0=$manifest.captures|Where-Object name -eq water_t0
$t1=$manifest.captures|Where-Object name -eq water_t1
$dt=$t1.world_time_seconds-$t0.world_time_seconds
if($dt -le 0 -or $water.mean_absolute_rgb_byte_difference -lt 1){throw 'No sufficient temporal water evidence'}
@{status='passed';world_time_delta_seconds=$dt;first_world_time_seconds=$t0.world_time_seconds;second_world_time_seconds=$t1.world_time_seconds;water_region=$water;static_sky_control=$sky;interpretation='Fixed camera, continuous shader Time drives analytic water; measured water region change complements two actual renders. This is artistic animation, not a fluid simulation.'}|ConvertTo-Json -Depth 6|Set-Content "$root/water_animation_validation.json" -Encoding utf8
