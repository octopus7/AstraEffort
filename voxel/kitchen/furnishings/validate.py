"""Fresh separate verification of saved native files and actual capture evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,struct,sys,time,zlib
sys.dont_write_bytecode=True
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT.parents[1]/'_tools'))
from voxelkit import read_vox,reduce_half,grid_stats
from build import make_assets,PALETTE
from features import probe_features
from support_check import components

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def png_info(path):
    raw=Path(path).read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n','PNG signature'
    pos=8;idat=[];info=None;ended=False
    while pos<len(raw):
        n=struct.unpack_from('>I',raw,pos)[0];typ=raw[pos+4:pos+8];body=raw[pos+8:pos+8+n]
        crc=struct.unpack_from('>I',raw,pos+8+n)[0]
        assert zlib.crc32(typ+body)&0xffffffff==crc,'PNG CRC'
        if typ==b'IHDR':info=struct.unpack('>IIBBBBB',body)
        elif typ==b'IDAT':idat.append(body)
        elif typ==b'IEND':ended=True
        pos+=12+n
    assert ended and pos==len(raw),'PNG end'
    assert info is not None
    width,height,depth,color,compression,filter_method,interlace=info
    assert depth==8 and color in (2,6) and not interlace,'expected 8-bit RGB/RGBA'
    scan=zlib.decompress(b''.join(idat));channels=3 if color==2 else 4
    assert len(scan)==height*(1+width*channels),'PNG scanline length'
    return {'width':width,'height':height,'bit_depth':depth,'color_type':color,'crc_and_zlib_passed':True}

def validate(native_only=False):
    t=time.perf_counter();started=utc();errors=[];records=[]
    assets=make_assets();captures=[]
    if not native_only:
        manifest=json.loads((ROOT/'capture_manifest.json').read_text(encoding='utf-8'))
        assert manifest['actual_blender_renders'] and manifest['no_scene_or_mesh_exports']
        captures=manifest['captures'];assert len(captures)==12,'twelve captures'
    for asset in assets:
        saved={};half=reduce_half(asset.grid)
        for variant,expected,scale in [('large',asset.grid,asset.voxel_size),('half',half,asset.voxel_size*2)]:
            path=ROOT/'assets'/asset.slug/variant/(asset.slug+'.vox')
            raw=path.read_bytes();assert raw[:8]==b'VOX '+struct.pack('<I',150),'VOX 150'
            g=read_vox(path);saved[variant]=g
            assert np.array_equal(expected.data,g.data),'full source/saved occupancy roundtrip'
            assert g.palette[:len(PALETTE)]==PALETTE,'palette roundtrip'
            assert g.shape==expected.shape,'native dimensions'
            assert 0<int(g.data.max())<len(PALETTE),'palette index bounds'
            meta=json.loads((path.parent/'metadata.json').read_text(encoding='utf-8'))
            stats=grid_stats(g,scale)
            assert meta['voxel_size_m']==scale
            assert meta['occupied_voxels']==stats['occupied_voxels']
            assert meta['sha256'][path.name]==sha(path),'metadata native hash'
            probes=probe_features(asset.slug,g,variant)
            connected_parts=components(g)
            assert len(connected_parts)==1,'all visible parts must physically contact model: '+asset.slug+'/'+variant
            for p in probes:
                if not p['passed']:errors.append(asset.slug+'/'+variant+': '+p['feature'])
            rec={'asset':asset.slug,'variant':variant,'native_sha256':sha(path),'grid_size':list(g.shape),
                 'occupied_voxels':stats['occupied_voxels'],'voxel_size_m':scale,
                 'native_roundtrip_passed':True,'feature_probes':probes,
                 'six_neighbor_connected_components':len(connected_parts)}
            if not native_only:
                image=path.parent/'preview.png';info=png_info(image)
                assert (info['width'],info['height'])==(768,768),'768px PNG'
                assert meta['sha256']['preview.png']==sha(image),'metadata PNG hash'
                cap=next(c for c in captures if c['asset']==asset.slug and c['variant']==variant)
                assert cap['source_native_sha256']==sha(path) and cap['image_sha256']==sha(image),'capture hashes'
                assert cap['render_from_reopened_vox'] and cap['elapsed_seconds']>0
                s=cap['settings']
                assert (s['engine'],s['device'],s['threads'],s['samples'],s['view_transform'])==('CYCLES','CPU',4,24,'AgX')
                assert s['denoising'] and s['resolution']==[768,768]
                rec['png']=info;rec['image_sha256']=sha(image);rec['render_settings_passed']=True
            records.append(rec)
        large=saved['large'];small=saved['half']
        assert list(small.shape)==[n//2 for n in large.shape]
        assert max(large.shape)==128 and all(n%2==0 for n in large.shape)
        assert max(small.shape)==64
        assert 0<np.count_nonzero(small.data)<np.count_nonzero(large.data),'native occupancy actually reduced'
        assert np.allclose(np.array(large.shape)*asset.voxel_size,np.array(small.shape)*asset.voxel_size*2)
        if not native_only:
            pair=[c for c in captures if c['asset']==asset.slug]
            assert pair[0]['settings']==pair[1]['settings'],'identical camera/light bounds across pair'
    forbidden=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.suffix.lower() in ('.blend','.glb','.gltf','.fbx','.obj','.umap')]
    assert not forbidden,'forbidden exports: '+repr(forbidden)
    vox_files=list((ROOT/'assets').rglob('*.vox'));assert len(vox_files)==12
    if not native_only:
        assert len(list((ROOT/'assets').rglob('preview.png')))==12
    result={'passed':not errors,'scope':'native_only' if native_only else 'native_and_renders',
            'started_at_utc':started,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-t,
            'asset_count':6,'native_count':12,'preview_count':0 if native_only else 12,
            'feature_probe_count':sum(len(r['feature_probes']) for r in records),
            'forbidden_exports':forbidden,'errors':errors,'variants':records}
    out=ROOT/('native_validation.json' if native_only else 'validation.json')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='variants'}),flush=True)
    if errors:raise AssertionError('; '.join(errors))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native-only',action='store_true')
    validate(p.parse_args().native_only)
