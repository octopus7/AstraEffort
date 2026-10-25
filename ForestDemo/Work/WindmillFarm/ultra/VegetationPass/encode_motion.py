from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,hashlib,statistics
from PIL import Image
P=Path(__file__).resolve().parent;M=P/'Motion'
FF=Path('C:/Users/blendue/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin')
manifest=json.loads((M/'capture_manifest.json').read_text());result=[]
for name,group in manifest['groups'].items():
    frames=group['frames'];assert len(frames)==32
    gaps=[b['world_time_seconds']-a['world_time_seconds'] for a,b in zip(frames,frames[1:])]
    assert min(gaps)>0
    duration=gaps+[statistics.median(gaps)]
    lines=[]
    for frame,dt in zip(frames,duration):lines.extend(["file '%s/%s'"%(name,frame['file']),f'duration {dt:.8f}'])
    # Repeat the last frame so concat observes its duration.
    lines.append("file '%s/%s'"%(name,frames[-1]['file']))
    source=M/(name+'_concat.txt');source.write_text('\n'.join(lines)+'\n')
    output=M/(name+'_wind.mp4')
    fps=1/statistics.mean(gaps)
    # Decode the valid PNG pixels once with Pillow. UE appends trailing bytes that
    # ffmpeg's PNG demuxer can mistake for extra chunks; no source pixels are edited.
    pixels=b''.join(Image.open(M/name/f['file']).convert('RGB').tobytes() for f in frames)
    command=[str(FF/'ffmpeg.exe'),'-hide_banner','-loglevel','error','-xerror','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x720','-framerate',str(fps),'-i','pipe:0','-frames:v','32','-fps_mode','passthrough','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    subprocess.run(command,input=pixels,check=True)
    probe=json.loads(subprocess.check_output([str(FF/'ffprobe.exe'),'-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,duration','-of','json',str(output)],text=True))['streams'][0]
    assert probe['width']==1280 and probe['height']==720 and int(probe['nb_frames'])>=32
    subprocess.run([str(FF/'ffmpeg.exe'),'-hide_banner','-loglevel','error','-xerror','-i',str(output),'-f','null','-'],check=True)
    result.append({'group':name,'file':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'source_frames':32,'captured_world_time_seconds':frames[-1]['world_time_seconds']-frames[0]['world_time_seconds'],'encoded_fps':fps,'encoded':probe,'provenance':'Only actual UE frame PNGs, encoded at their mean captured world-time frame rate; slight per-frame timing variation normalized. No interpolation/generated frames.'})
(M/'video_manifest.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'videos':result},indent=2));print(json.dumps(result,indent=2))
