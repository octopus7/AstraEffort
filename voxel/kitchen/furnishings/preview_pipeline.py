"""Batch-local native VOX + PNG runner. Never saves a mesh or Blender scene."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys,time
sys.dont_write_bytecode=True
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT.parents[1]/'_tools'))
from voxelkit import write_vox,read_vox,reduce_half,grid_stats
from build import make_assets,PALETTE,PALETTE_NAMES
from features import probe_features

def utc():return datetime.now(timezone.utc).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def update_status(stage):
    p=ROOT/'STATUS.json';s=json.loads(p.read_text(encoding='utf-8'))
    s['stage']=stage;s['last_updated_at_utc']=utc();dump(p,s)

def native_build(only_asset=None):
    t=time.perf_counter();started=utc();update_status('native_build')
    ta=time.perf_counter();assets=make_assets();author_seconds=time.perf_counter()-ta
    if only_asset:assets=[a for a in assets if a.slug==only_asset]
    if not assets:raise ValueError('unknown asset')
    records=[];errors=[]
    dump(ROOT/'palette.json',{'new_shades':False,'palette':[{'index':i,'name':name,'rgba':list(c)} for i,(name,c) in enumerate(zip(PALETTE_NAMES,PALETTE))]})
    for asset in assets:
        assert max(asset.grid.shape)==128 and all(n%2==0 for n in asset.grid.shape)
        half=reduce_half(asset.grid)
        if asset.half_postprocess:asset.half_postprocess(half)
        for variant,grid,scale in [('large',asset.grid,asset.voxel_size),('half',half,asset.voxel_size*2)]:
            dst=ROOT/'assets'/asset.slug/variant;dst.mkdir(parents=True,exist_ok=True)
            path=dst/(asset.slug+'.vox');write_vox(path,grid);reopened=read_vox(path)
            assert np.array_equal(grid.data,reopened.data),'native occupancy differs'
            assert grid.palette==reopened.palette[:len(grid.palette)],'native palette differs'
            probes=probe_features(asset.slug,reopened,variant)
            for p in probes:
                if not p['passed']:errors.append(f"{asset.slug}/{variant}: {p['feature']} {p['found_palette_indices']}")
            meta={'asset':asset.slug,'label':asset.label,'variant':variant,'format':'MagicaVoxel VOX 150',
                  'coordinate_system':'X right, Y back, Z up; front -Y','origin':'XY grid center; grid bottom Z=0',
                  'notes':asset.notes,'palette':PALETTE,'half_method':'2x2x2 nonempty majority; higher palette index breaks ties',
                  'half_postprocess':'none','same_physical_grid_extents':True,
                  'native_roundtrip_passed':True,'render_only_surface':True,
                  'authored_at_utc':utc(),**grid_stats(reopened,scale),
                  'sha256':{path.name:sha(path)},'feature_probes':probes}
            dump(dst/'metadata.json',meta)
            records.append({'asset':asset.slug,'variant':variant,'native_sha256':sha(path),
                            'occupied_voxels':meta['occupied_voxels'],'feature_probes':probes})
    result={'passed':not errors,'started_at_utc':started,'finished_at_utc':utc(),
            'elapsed_seconds':time.perf_counter()-t,'occupancy_authoring_seconds':author_seconds,
            'variants':records,'errors':errors}
    dump(ROOT/('native_build_'+only_asset+'.json' if only_asset else 'native_build.json'),result)
    print(json.dumps({'native_build_passed':not errors,'variants':len(records),'seconds':result['elapsed_seconds'],'errors':errors}),flush=True)
    if errors:raise AssertionError('; '.join(errors))

def render(only_asset=None):
    import bpy
    from blender_pipeline import build_surface,add_studio
    update_status('rendering');started=utc();t=time.perf_counter()
    assets=make_assets();captures=[];surfaces=[]
    if only_asset:assets=[a for a in assets if a.slug==only_asset]
    if not assets:raise ValueError('unknown asset')
    manifest=ROOT/'capture_manifest.json'
    if only_asset and manifest.exists():
        captures=[c for c in json.loads(manifest.read_text(encoding='utf-8'))['captures'] if c['asset']!=only_asset]
    for asset in assets:
        large_path=ROOT/'assets'/asset.slug/'large'/(asset.slug+'.vox')
        saved_large=read_vox(large_path)
        assert np.array_equal(asset.grid.data,saved_large.data),'source/native mismatch before render'
        camera_bounds=grid_stats(saved_large,asset.voxel_size)['bounds_m']
        for variant,scale in [('large',asset.voxel_size),('half',asset.voxel_size*2)]:
            dst=ROOT/'assets'/asset.slug/variant;vox=dst/(asset.slug+'.vox')
            reparse_started=utc();reopened=read_vox(vox)
            expected=asset.grid if variant=='large' else reduce_half(asset.grid)
            assert np.array_equal(expected.data,reopened.data),'render native differs from authored'
            native_hash=sha(vox);surface_t=time.perf_counter()
            # The geometry source is explicitly the REOPENED VOX, never asset.grid.
            obj,surface=build_surface(asset,reopened,scale)
            surface_seconds=time.perf_counter()-surface_t
            settings=add_studio(camera_bounds)
            scene=bpy.context.scene;scene.render.image_settings.color_depth='8'
            settings['camera_bounds_from_large_native_m']=camera_bounds
            settings['clip_start_m']=scene.camera.data.clip_start
            settings['clip_end_m']=scene.camera.data.clip_end
            settings['image_format']='PNG';settings['color_mode']='RGB';settings['color_depth']=8
            settings['world_background_rgba']=list(scene.world.node_tree.nodes['Background'].inputs[0].default_value)
            settings['world_strength']=scene.world.node_tree.nodes['Background'].inputs[1].default_value
            settings['lights']=[{'name':o.name,'type':o.data.type,'shape':o.data.shape,'energy_w':o.data.energy,
                                 'size_m':o.data.size,'location_m':list(o.location),'rotation_radians':list(o.rotation_euler)}
                                for o in scene.objects if o.type=='LIGHT']
            settings['studio_floor_is_render_only']=True
            image=dst/'preview.png';scene.render.filepath=str(image)
            render_started=utc();rt=time.perf_counter();bpy.ops.render.render(write_still=True)
            capture={'asset':asset.slug,'variant':variant,'image':image.relative_to(ROOT).as_posix(),
                     'source_native':vox.relative_to(ROOT).as_posix(),'source_native_sha256':native_hash,
                     'source_reparsed_at_utc':reparse_started,'render_from_reopened_vox':True,
                     'started_at_utc':render_started,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-rt,
                     'surface_seconds':surface_seconds,'settings':settings,'image_sha256':sha(image)}
            captures.append(capture);surfaces.append(surface)
            meta=json.loads((dst/'metadata.json').read_text(encoding='utf-8'))
            meta['surface']=surface;meta['sha256']['preview.png']=sha(image)
            meta['rendered_at_utc']=capture['finished_at_utc'];dump(dst/'metadata.json',meta)
            dump(manifest,{'actual_blender_renders':True,'renderer_version':bpy.app.version_string,
                           'native_geometry_is_authoritative':True,'no_scene_or_mesh_exports':True,'captures':captures})
            print('FURNISHING_RENDER_COMPLETE '+asset.slug+'/'+variant+' '+str(round(capture['elapsed_seconds'],3))+' s',flush=True)
    run={'started_at_utc':started,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-t,
         'captures_this_run':2*len(assets),'surface_seconds':sum(c['surface_seconds'] for c in captures if not only_asset or c['asset']==only_asset),
         'render_seconds':sum(c['elapsed_seconds'] for c in captures if not only_asset or c['asset']==only_asset),
         'thread_limit':4,'blender_version':bpy.app.version_string,'argv':sys.argv}
    dump(ROOT/'logs'/('render_timing_'+(only_asset or 'all')+'.json'),run)
    update_status('rendered_awaiting_visual_inspection')

def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    parser=argparse.ArgumentParser();parser.add_argument('--native-only',action='store_true')
    parser.add_argument('--render-only',action='store_true');parser.add_argument('--asset')
    args=parser.parse_args(argv)
    if not args.render_only:native_build(args.asset)
    if not args.native_only:render(args.asset)

if __name__=='__main__':main()
