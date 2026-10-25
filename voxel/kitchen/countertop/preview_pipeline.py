"""Batch-local native-only build and ephemeral render pipeline. Never saves a scene or mesh."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, sys, time
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT.parents[1]/'_tools'))
from voxelkit import write_vox,read_vox,reduce_half,grid_stats
from build import make_assets, PALETTE

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def native_build(assets):
    start=utc(); t0=time.perf_counter(); entries=[]
    for a in assets:
        assert max(a.grid.shape)==128 and all(n%2==0 for n in a.grid.shape)
        h=reduce_half(a.grid)
        if a.half_postprocess: a.half_postprocess(h)
        for variant,g,scale in [('large',a.grid,a.voxel_size),('half',h,a.voxel_size*2)]:
            dst=ROOT/'assets'/a.slug/variant; dst.mkdir(parents=True,exist_ok=True)
            vox=dst/f'{a.slug}.vox'; write_vox(vox,g); saved=read_vox(vox)
            assert np.array_equal(saved.data,g.data)
            assert saved.palette[:len(PALETTE)]==PALETTE
            meta={'asset':a.slug,'label':a.label,'variant':variant,'format':'MagicaVoxel VOX150',
                  'coordinate_system':'X right, Y back, Z up; front -Y','origin':'XY grid center, bottom grid plane Z=0',
                  'palette':PALETTE,'notes':a.notes,'half_method':'2x2x2 nonempty majority; largest palette index breaks ties',
                  'half_postprocess':'none','native_roundtrip_passed':True,'native_sha256':sha(vox),
                  'same_physical_grid_extents':True,**grid_stats(saved,scale)}
            write_json(dst/'metadata.json',meta)
            entries.append({'asset':a.slug,'variant':variant,'native_sha256':sha(vox),'occupied_voxels':meta['occupied_voxels']})
    result={'started_at_utc':start,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-t0,'native_count':len(entries),'entries':entries}
    write_json(ROOT/'logs'/('native_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json'),result)
    write_json(ROOT/'native_build.json',result)
    write_json(ROOT/'palette.json',{'source':'BRIEF.md common fixed palette, newly applied to countertop models','additional_shades':[],'rgba':PALETTE})
    print('NATIVE_BUILD_COMPLETE '+json.dumps({'files':len(entries),'seconds':result['elapsed_seconds']}),flush=True)
    return result

def render_assets(assets,only=None):
    import bpy
    from blender_pipeline import build_surface,add_studio
    captures=[]; start=utc(); t0=time.perf_counter(); mesh_seconds=0.; render_seconds=0.
    previous=[]
    manifest=ROOT/'capture_manifest.json'
    if only and manifest.exists():
        previous=[c for c in json.loads(manifest.read_text(encoding='utf-8'))['captures'] if c['asset']!=only]
    for a in assets:
        if only and a.slug!=only: continue
        large_path=ROOT/'assets'/a.slug/'large'/f'{a.slug}.vox'
        large_reparsed=read_vox(large_path)
        bounds=grid_stats(large_reparsed,a.voxel_size)['bounds_m']
        for variant,scale in [('large',a.voxel_size),('half',a.voxel_size*2)]:
            dst=ROOT/'assets'/a.slug/variant; vox=dst/f'{a.slug}.vox'
            saved=read_vox(vox)
            mt=time.perf_counter(); obj,surface=build_surface(a,saved,scale)
            settings=add_studio(bounds)
            scene=bpy.context.scene
            settings['lighting']=[{'name':ob.name,'type':ob.data.type,'location':list(ob.location),'rotation_radians':list(ob.rotation_euler),'energy':ob.data.energy,'size':ob.data.size} for ob in scene.objects if ob.type=='LIGHT']
            settings['world_color']=[float(v) for v in scene.world.node_tree.nodes['Background'].inputs[0].default_value]
            settings['world_strength']=float(scene.world.node_tree.nodes['Background'].inputs[1].default_value)
            settings['camera_bounds_source']='reparsed large native occupied bounds, reused for half'
            settings['camera_bounds_m']=bounds
            mesh_time=time.perf_counter()-mt; mesh_seconds+=mesh_time
            png=dst/'preview.png'; scene.render.filepath=str(png)
            capture_start=utc(); rt=time.perf_counter()
            bpy.ops.render.render(write_still=True)
            duration=time.perf_counter()-rt; render_seconds+=duration
            capture={'asset':a.slug,'variant':variant,'image':png.relative_to(ROOT).as_posix(),
                     'started_at_utc':capture_start,'finished_at_utc':utc(),'elapsed_seconds':duration,
                     'surface_build_seconds':mesh_time,'settings':settings,'render_input':'reparsed native VOX',
                     'source_vox_sha256':sha(vox),'image_sha256':sha(png),'temporary_geometry_only':True}
            captures.append(capture)
            meta=json.loads((dst/'metadata.json').read_text(encoding='utf-8'))
            meta.update({'surface':surface,'preview_sha256':sha(png),'rendered_from_reparsed_native':True,'exported_geometry':False})
            write_json(dst/'metadata.json',meta)
            write_json(manifest,{'actual_blender_renders':True,'blender_version':bpy.app.version_string,'captures':previous+captures})
            print('ACTUAL_PREVIEW_COMPLETE '+a.slug+'/'+variant+' '+str(round(duration,3))+'s',flush=True)
    result={'started_at_utc':start,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-t0,'surface_build_seconds':mesh_seconds,'render_seconds':render_seconds,'captures_completed':len(captures),'only_asset':only}
    log=ROOT/'logs'/('render_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
    write_json(log,result)
    write_json(ROOT/'render_timing.json',result)
    return result

def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    parser=argparse.ArgumentParser()
    parser.add_argument('--native-only',action='store_true')
    parser.add_argument('--render-only',action='store_true')
    parser.add_argument('--asset')
    args=parser.parse_args(argv)
    (ROOT/'logs').mkdir(exist_ok=True)
    st=utc(); timer=time.perf_counter(); authored_start=time.perf_counter(); assets=make_assets(); authored_seconds=time.perf_counter()-authored_start
    if args.asset: assets=[a for a in assets if a.slug==args.asset]
    assert assets
    if not args.render_only: native_build(assets)
    render=None
    if not args.native_only: render=render_assets(assets,args.asset)
    result={'started_at_utc':st,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-timer,'grid_generation_seconds':authored_seconds,'render':render,'arguments':argv}
    write_json(ROOT/'logs'/('pipeline_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json'),result)
    print('PIPELINE_COMPLETE '+json.dumps(result),flush=True)

if __name__=='__main__': main()
