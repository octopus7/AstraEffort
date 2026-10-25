"""Independent read-only saved-artifact check. Does not import or run target authoring code."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,struct,sys,time
sys.dont_write_bytecode=True
import numpy as np
HERE=Path(__file__).resolve().parent
TARGET=HERE.parents[1]/'appliances'
sys.path.insert(0,str(HERE.parents[2]/'_tools'))
from voxelkit import read_vox,reduce_half,grid_stats

SLUGS=['double_door_fridge','range_oven','microwave','dishwasher','range_hood','rice_cooker','electric_kettle']
PALETTE=[(0,0,0,0),(232,225,205,255),(121,151,133,255),(75,105,91,255),(181,130,78,255),(217,176,113,255),(48,56,57,255),(156,170,170,255),(91,108,112,255),(92,133,145,255),(244,239,225,255),(191,105,70,255),(35,42,44,255),(217,164,85,255),(151,94,48,255),(203,183,106,255)]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(test,label):
    if not test:raise AssertionError(label)

def main():
    start=datetime.now(timezone.utc);timer=time.perf_counter()
    check(TARGET.resolve()==Path('D:/github/AstraEffort/voxel/kitchen/appliances').resolve(),'target scope')
    status=read(TARGET/'STATUS.json');validation=read(TARGET/'validation.json')
    cm=read(TARGET/'capture_manifest.json');frozen=read(TARGET/'frozen_file_hashes.json')
    check(status['status']=='ready_for_review','target readiness')
    check(validation['passed'] and not validation['source_only'],'target declared saved validation')
    capture={(c['asset'],c['variant']):c for c in cm['captures']}
    vr={(v['asset'],v['variant']):v for v in validation['records']}
    check(len(capture)==14 and len(vr)==14,'evidence roster')
    hashes=[]
    for relative,digest in frozen['sha256'].items():
        p=TARGET/relative
        check(p.resolve().is_relative_to(TARGET.resolve()),'frozen path escape')
        actual=sha(p);check(actual==digest,'frozen hash '+relative)
        hashes.append({'path':relative,'sha256':actual})
    rows=[];pair_checks=[];feature_count=0
    for slug in SLUGS:
        gs={}; metas={}
        for variant,divisor in [('large',1),('half',2)]:
            dst=TARGET/'assets'/slug/variant
            vox=dst/(slug+'.vox');png=dst/'preview.png';meta=read(dst/'metadata.json')
            raw=vox.read_bytes();check(raw[:8]==b'VOX '+struct.pack('<I',150),slug+'/'+variant+' VOX150')
            g=read_vox(vox)
            check(max(g.shape)==128//divisor and (divisor!=1 or all(x%2==0 for x in g.shape)),slug+'/'+variant+' dimensions')
            check(g.palette[:16]==PALETTE and 0<int(g.data.max())<16,slug+'/'+variant+' palette')
            stats=grid_stats(g,meta['voxel_size_m'])
            for field in ['grid_size','occupied_voxels','occupancy_sha256']:
                check(meta[field]==stats[field],slug+'/'+variant+' metadata '+field)
            check(np.allclose(meta['grid_extents_m'],stats['grid_extents_m']),slug+'/'+variant+' physical extents')
            check(meta['half_postprocess'] is None,slug+'/'+variant+' unexpected half correction')
            nv,pv=sha(vox),sha(png);c=capture[(slug,variant)];v=vr[(slug,variant)]
            check(nv==meta['sha256']['native']==c['source_vox_sha256']==v['native_sha256'],slug+'/'+variant+' native hash evidence')
            check(pv==meta['sha256']['preview']==c['image_sha256']==v['preview_sha256'],slug+'/'+variant+' PNG hash evidence')
            head=png.read_bytes()[:24]
            check(head[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',head[16:24])==(768,768),slug+'/'+variant+' PNG dimensions')
            check(c['rendered_from_reparsed_vox'] and c['actual_blender_render'],slug+'/'+variant+' capture source declaration')
            s=c['settings']
            check(s['engine']=='CYCLES' and s['device']=='CPU' and s['threads']==4 and s['samples']==24 and s['denoising'] and s['view_transform']=='AgX' and s['resolution']==[768,768],slug+'/'+variant+' render settings')
            check(len(s['lights'])==3 and s['world_strength']>0,slug+'/'+variant+' lighting evidence')
            check(datetime.fromisoformat(c['finished_at_utc'])>datetime.fromisoformat(c['started_at_utc']) and c['elapsed_seconds']>0,slug+'/'+variant+' actual timestamps')
            probes=[]
            for probe in v['feature_probes']:
                lo,hi=probe['large_grid_box']
                region=g.data[tuple(slice(a//divisor,b//divisor) for a,b in zip(lo,hi))]
                indices=np.unique(region).tolist()
                check(region.size>0 and indices==[probe['expected_index']],slug+'/'+variant+' feature '+probe['name'])
                probes.append({'feature':probe['name'],'saved_indices':indices,'cells':int(region.size),'passed':True})
                feature_count+=1
            rows.append({'asset':slug,'variant':variant,'native_path':vox.relative_to(TARGET).as_posix(),'preview_path':png.relative_to(TARGET).as_posix(),'native_sha256':nv,'preview_sha256':pv,'grid_size':list(g.shape),'voxel_size_m':meta['voxel_size_m'],'grid_extents_m':stats['grid_extents_m'],'occupied_bounds_m':stats['bounds_m'],'occupied_voxels':stats['occupied_voxels'],'checks_passed':True,'feature_probes':probes,'capture_started_at_utc':c['started_at_utc'],'capture_finished_at_utc':c['finished_at_utc']})
            gs[variant]=g;metas[variant]=meta
        check(gs['half'].shape==tuple(n//2 for n in gs['large'].shape),slug+' exact half grid')
        check(abs(metas['half']['voxel_size_m']-2*metas['large']['voxel_size_m'])<1e-12,slug+' doubled cell size')
        check(np.allclose(metas['large']['grid_extents_m'],metas['half']['grid_extents_m']),slug+' same physical grid')
        check(np.count_nonzero(gs['half'].data)<np.count_nonzero(gs['large'].data),slug+' actual reduction')
        check(np.array_equal(reduce_half(gs['large']).data,gs['half'].data),slug+' exact saved-data half reduction')
        check(capture[(slug,'large')]['settings']==capture[(slug,'half')]['settings'],slug+' same camera/lights/settings')
        pair_checks.append({'asset':slug,'exact_half_reduction':True,'same_physical_extents':True,'same_camera_lights_render_settings':True})
    forbidden=[p.relative_to(TARGET).as_posix() for p in TARGET.rglob('*') if p.suffix.lower() in {'.blend','.glb','.fbx','.obj','.umap'}]
    check(not forbidden,'forbidden output files')
    check(len(list((TARGET/'assets').rglob('*.vox')))==14,'native count')
    check(len(list((TARGET/'assets').rglob('preview.png')))==14,'preview count')
    result={'passed':True,'started_at_utc':start.isoformat(),'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.perf_counter()-timer,'target':str(TARGET),'target_writes':False,'target_code_executed':False,'frozen_files_checked':len(hashes),'native_files_checked':14,'png_files_checked':14,'saved_native_feature_probes':feature_count,'forbidden_outputs':forbidden,'frozen_hashes':hashes,'records':rows,'pairs':pair_checks,'upstream_validation_summary':{k:v for k,v in validation.items() if k!='records'},'capture_manifest_sha256':sha(TARGET/'capture_manifest.json'),'validation_sha256':sha(TARGET/'validation.json'),'frozen_manifest_sha256':sha(TARGET/'frozen_file_hashes.json')}
    (HERE/'appliances_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','elapsed_seconds','frozen_files_checked','native_files_checked','png_files_checked','saved_native_feature_probes','target_writes','target_code_executed']}))
    print(json.dumps([{'asset':r['asset'],'variant':r['variant'],'dimensions':r['grid_size'],'scale':r['voxel_size_m'],'features':[p['feature'] for p in r['feature_probes']]} for r in rows if r['variant']=='half']))

if __name__=='__main__':main()
