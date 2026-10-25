from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess
from PIL import Image
P=Path(__file__).resolve().parent
FF=Path('C:/Users/blendue/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe');PROBE=FF.with_name('ffprobe.exe')
data=json.loads((P/'Motion/capture_manifest.json').read_text());videos=[]
for group in ('canal','rainy_street'):
    rows=[r for r in data['frames'] if r['group']==group];assert len(rows)==40
    duration=rows[-1]['world_time_seconds']-rows[0]['world_time_seconds'];fps=(len(rows)-1)/duration
    out=P/'Motion'/(group+'_rain.mp4')
    cmd=[str(FF),'-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x720','-framerate',str(fps),'-i','pipe:0','-an','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for r in rows:
        im=Image.open(r['file']).convert('RGB');assert im.size==(1280,720);proc.stdin.write(im.tobytes())
    proc.stdin.close();error=proc.stderr.read().decode();code=proc.wait();assert code==0,error
    info=json.loads(subprocess.check_output([str(PROBE),'-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,duration','-of','json',str(out)]))['streams'][0]
    assert int(info['nb_frames'])==40
    check=subprocess.run([str(FF),'-v','error','-i',str(out),'-f','null','-'],capture_output=True,text=True);assert check.returncode==0 and not check.stderr,check.stderr
    videos.append({'group':group,'file':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_frames':40,'captured_world_time_span':duration,'encoded_fps':fps,'encoded':info,'decode_verified':True,'provenance':'Only actual UE frame pixels. Pillow RGB decode preserves source pixels and ignores trailing container data. Encoded at mean capture frame rate; slight per-frame timing variation normalized. No generated or interpolated frames.'})
(P/'Motion/video_manifest.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'videos':videos},indent=2));print(json.dumps(videos,indent=2))
