"""Read-only lightweight audit; imports no target authoring or validation code."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,struct,zlib,time
sys.dont_write_bytecode=True
import numpy as np
REVIEW=Path(__file__).resolve().parent
TARGET=REVIEW.parents[1]/'countertop'
sys.path.insert(0,str(REVIEW.parents[2]/'_tools'))
from voxelkit import read_vox,reduce_half
SLUGS=['stand_mixer','espresso_machine','toaster','blender','stock_pot','frying_pan','cutting_board_knife']
PALETTE=[(0,0,0,0),(232,225,205,255),(121,151,133,255),(75,105,91,255),(181,130,78,255),(217,176,113,255),(48,56,57,255),(156,170,170,255),(91,108,112,255),(92,133,145,255),(244,239,225,255),(191,105,70,255),(35,42,44,255),(217,164,85,255),(151,94,48,255),(203,183,106,255)]
CRITICAL={
 'stand_mixer':[(48,44,42),(25,44,76),(86,44,48)],
 'espresso_machine':[(34,40,54),(58,42,43),(74,42,40)],
 'toaster':[(64,29,58),(30,55,58)],
 'blender':[(45,45,78),(79,45,80)],
 'stock_pot':[(64,48,45),(21,48,58),(107,48,58)],
 'frying_pan':[(48,48,22),(119,48,20)],
 'cutting_board_knife':[(118,48,4)],
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def png_check(p):
    raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    pos=8;data=[];info=None;end=False
    while pos<len(raw):
        n=struct.unpack_from('>I',raw,pos)[0];kind=raw[pos+4:pos+8];body=raw[pos+8:pos+8+n]
        assert zlib.crc32(kind+body)&0xffffffff==struct.unpack_from('>I',raw,pos+8+n)[0]
        if kind==b'IHDR':info=struct.unpack('>IIBBBBB',body)
        if kind==b'IDAT':data.append(body)
        if kind==b'IEND':end=True
        pos+=n+12
    assert info[:2]==(768,768) and info[2:4]==(8,2) and info[-1]==0 and end and pos==len(raw)
    assert len(zlib.decompress(b''.join(data)))==768*(768*3+1)
    return {'size_px':[768,768],'rgb8':True,'crc_and_decompression_passed':True}

def main():
    started=datetime.now(timezone.utc).isoformat();t=time.perf_counter()
    frozen=load(TARGET/'frozen_file_hashes.json')
    integrity=[{'path':x['path'],'passed':(TARGET/x['path']).stat().st_size==x['bytes'] and sha(TARGET/x['path'])==x['sha256']} for x in frozen['files']]
    assert all(x['passed'] for x in integrity)
    manifest=load(TARGET/'capture_manifest.json');assert manifest['actual_blender_renders']
    captures={(c['asset'],c['variant']):c for c in manifest['captures']};assert len(captures)==14
    owner_validation=load(TARGET/'validation.json');assert owner_validation['passed'] and owner_validation['native_count']==14
    records=[];critical=[];pairs=[]
    for slug in SLUGS:
        grids={};metas={}
        for variant,factor in [('large',1),('half',2)]:
            folder=TARGET/'assets'/slug/variant;vox=folder/(slug+'.vox');png=folder/'preview.png'
            assert vox.read_bytes()[:8]==b'VOX '+struct.pack('<I',150)
            g=read_vox(vox);meta=load(folder/'metadata.json');grids[variant]=g;metas[variant]=meta
            assert g.palette[:16]==PALETTE and int(g.data.max())<16 and np.count_nonzero(g.data)>0
            assert list(g.shape)==meta['grid_size'] and np.count_nonzero(g.data)==meta['occupied_voxels']
            assert sha(vox)==meta['native_sha256'] and sha(png)==meta['preview_sha256']
            assert np.allclose(np.array(g.shape)*meta['voxel_size_m'],meta['grid_extents_m'])
            cap=captures[(slug,variant)]
            assert sha(vox)==cap['source_vox_sha256'] and sha(png)==cap['image_sha256']
            assert cap['render_input']=='reparsed native VOX' and cap['temporary_geometry_only']
            settings=cap['settings']
            assert (settings['engine'],settings['device'],settings['samples'],settings['threads'],settings['view_transform'])==('CYCLES','CPU',24,4,'AgX')
            assert settings['denoising'] and settings['resolution']==[768,768]
            assert datetime.fromisoformat(cap['finished_at_utc'])>datetime.fromisoformat(cap['started_at_utc']) and cap['elapsed_seconds']>0
            for point in CRITICAL[slug]:
                sample=tuple(v//factor for v in point)
                region=g.data[tuple(slice(v-1,v+1) for v in sample)]
                assert np.count_nonzero(region)==0,(slug,variant,point)
                critical.append({'asset':slug,'variant':variant,'source_large_center':list(point),'cells_checked':int(region.size),'empty':True})
            records.append({'asset':slug,'variant':variant,'native_path':vox.relative_to(TARGET).as_posix(),
                'native_sha256':sha(vox),'image':png.relative_to(TARGET).as_posix(),'image_sha256':sha(png),
                'dimensions':list(g.shape),'occupied_voxels':int(np.count_nonzero(g.data)),
                'voxel_size_m':meta['voxel_size_m'],'grid_extents_m':meta['grid_extents_m'],'png':png_check(png)})
        lg,hg=grids['large'],grids['half'];lm,hm=metas['large'],metas['half']
        assert max(lg.shape)==128 and all(n%2==0 for n in lg.shape)
        assert hg.shape==tuple(n//2 for n in lg.shape) and max(hg.shape)==64
        assert hm['voxel_size_m']==lm['voxel_size_m']*2
        assert np.allclose(lm['grid_extents_m'],hm['grid_extents_m'])
        assert np.count_nonzero(hg.data)<np.count_nonzero(lg.data)
        assert np.array_equal(reduce_half(lg).data,hg.data),'actual native reduction'
        assert captures[(slug,'large')]['settings']==captures[(slug,'half')]['settings']
        pairs.append({'asset':slug,'actual_native_reduction':True,'equal_physical_grid_extents':True,'identical_camera_light_render_settings':True})
    # The dark inner squares visible in the pot are occupied metal mounts.
    pot=read_vox(TARGET/'assets'/'stock_pot'/'large'/'stock_pot.vox')
    mounts=[{'point':[x,48,64],'palette_index':int(pot.data[x,48,64])} for x in (35,92)]
    assert all(x['palette_index']>0 for x in mounts)
    forbidden=[p.relative_to(TARGET).as_posix() for p in TARGET.rglob('*') if p.suffix.lower() in {'.blend','.glb','.gltf','.fbx','.obj','.umap'}]
    assert not forbidden
    assert len(list((TARGET/'assets').rglob('*.vox')))==14
    assert len(list((TARGET/'assets').rglob('preview.png')))==14
    # Own production hashes are also unchanged: review output is a separate directory.
    own=load(REVIEW.parent/'frozen_file_hashes.json')
    assert all(sha(REVIEW.parent/x['path'])==x['sha256'] for x in own['files'])
    result={'passed':True,'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds':time.perf_counter()-t,'target':'voxel/kitchen/countertop',
        'frozen_files_verified':len(integrity),'native_files':14,'primary_previews':14,
        'forbidden_outputs':forbidden,'target_authoring_or_development_code_executed':False,
        'own_frozen_production_unchanged':True,'checks':records,'pair_checks':pairs,
        'critical_open_volume_checks':critical,'pot_inner_mounts':mounts,
        'owner_reported_feature_probe_count':sum(len(c['features']) for c in owner_validation['checks']),
        'frozen_hash_integrity':integrity}
    (REVIEW/'countertop_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in {'checks','pair_checks','critical_open_volume_checks','frozen_hash_integrity'}}))

if __name__=='__main__':main()
