import pathlib,json,re,shutil,hashlib,datetime
from PIL import Image,ImageStat
W=pathlib.Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass');calls=json.loads((W/'imagegen_calls.json').read_text());rows=[]
parse=lambda x:datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=datetime.timezone.utc)
for c in calls:
 src=pathlib.Path(re.search(r'as (C:.*?\.png) by default',c['output_hint']).group(1));dst=W/'Generated'/f"{c['id']}_original.png";shutil.copy2(src,dst)
 im=Image.open(dst).convert('RGB');means=ImageStat.Stat(im).mean
 linear=lambda v:((v/255+.055)/1.055)**2.4 if v/255>.04045 else v/255/12.92
 c.update({'original_path':str(src),'workspace_path':str(dst),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'size':im.size,'mean_linear_rgb':[linear(v) for v in means],'elapsed_seconds':(parse(c['end']['current_time'])-parse(c['begin']['current_time'])).total_seconds(),'edits':'none; exact tool output copied byte-for-byte'})
 rows.append(c)
sizes={tuple(r['size']) for r in rows};assert len(sizes)==1 and next(iter(sizes))[0]==next(iter(sizes))[1]
summed=sum(r['elapsed_seconds'] for r in rows);wall=(max(parse(r['end']['current_time']) for r in rows)-min(parse(r['begin']['current_time']) for r in rows)).total_seconds()
manifest={'tool':'built-in image_gen.imagegen','parallel_calls':5,'summed_call_seconds':summed,'union_wall_seconds':wall,'parallel_overlap_seconds':summed-wall,'common_square_resolution':next(iter(sizes))[0],'calls':rows,'mapping':{'plaster':['Plaster','Cream','Leather'],'wood':['Wood','Trim','Ochre'],'stone':['Stone','StoneLight','Gravel','Path','Dark','Earth','Brick'],'metal':['Roof','RoofEdge','Metal','Rail'],'foliage':['Grass','Hill','Leaf','LeafLight','Flower']},'exceptions':{'Glass':'plain tinted window glass, no generated texture','Lamp':'emissive light pane, no generated texture','SkyBackdrop':'unlit presentation background, not authored surface density scope'}}
(W/'imagegen_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in manifest.items() if k!='calls'},indent=2))
