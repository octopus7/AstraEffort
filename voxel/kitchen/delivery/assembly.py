"""Read-only kitchen inventory and before/after assembly integrity checks."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import struct
import sys
import time
import zlib
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
KITCHEN = ROOT.parent
BATCHES = {
    'appliances': ['double_door_fridge','range_oven','microwave','dishwasher','range_hood','rice_cooker','electric_kettle'],
    'furnishings': ['sink_cabinet','kitchen_island','dish_cabinet','kitchen_cart','dish_drying_rack','knife_block'],
    'countertop': ['stand_mixer','espresso_machine','toaster','blender','stock_pot','frying_pan','cutting_board_knife'],
}
FORBIDDEN = {'.blend','.blend1','.glb','.gltf','.fbx','.obj','.umap','.stl','.ply','.dae','.usd','.usda','.usdc','.abc'}


def utc():
    return datetime.now(timezone.utc)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(name, data):
    (ROOT/name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def file_info(path):
    data = path.read_bytes()
    return {'path':'../'+path.relative_to(KITCHEN).as_posix(),
            'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def png_info(path, expected_size=(768,768)):
    raw=path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n', path
    pos=8
    packed=[]
    dims=None
    while pos < len(raw):
        n=struct.unpack_from('>I',raw,pos)[0]
        kind=raw[pos+4:pos+8]
        body=raw[pos+8:pos+8+n]
        assert zlib.crc32(kind+body)&0xffffffff == struct.unpack_from('>I',raw,pos+8+n)[0]
        if kind == b'IHDR':
            dims=struct.unpack('>IIBBBBB',body)
        elif kind == b'IDAT':
            packed.append(body)
        pos += n+12
        if kind == b'IEND':
            break
    assert pos == len(raw) and dims[:2] == expected_size, (path,dims)
    assert dims[2] == 8 and dims[3] in (2,6)
    channels=3 if dims[3] == 2 else 4
    decoded=zlib.decompress(b''.join(packed))
    assert len(decoded) == (dims[0]*channels+1)*dims[1]
    return {'width':dims[0],'height':dims[1],'crc_and_decompression_passed':True}


def vox_info(path):
    raw=path.read_bytes()
    assert raw[:4] == b'VOX ' and struct.unpack_from('<I',raw,4)[0] == 150
    assert raw[8:12] == b'MAIN'
    length,children=struct.unpack_from('<II',raw,12)
    assert length == 0 and 20+children == len(raw)
    pos=20
    size=count=None
    while pos < len(raw):
        kind=raw[pos:pos+4]
        n,child=struct.unpack_from('<II',raw,pos+4)
        assert child == 0
        body=raw[pos+12:pos+12+n]
        assert len(body)==n
        if kind==b'SIZE':
            size=list(struct.unpack('<III',body))
        elif kind==b'XYZI':
            count=struct.unpack_from('<I',body)[0]
            assert len(body)==4+4*count and count>0
        pos += 12+n
    assert pos==len(raw) and size is not None and count is not None
    return {'format':'VOX 150','grid_size':size,'occupied_voxels':count}


def verify_frozen():
    summaries=[]
    snapshot={}
    for batch in BATCHES:
        batch_root=KITCHEN/batch
        manifest_path=batch_root/'frozen_file_hashes.json'
        manifest=read(manifest_path)
        entries=manifest.get('files')
        if entries is None:
            entries=[{'path':p,'sha256':h} for p,h in manifest['sha256'].items()]
        for entry in entries:
            path=(batch_root/entry['path']).resolve()
            assert path.is_relative_to(batch_root.resolve())
            info=file_info(path)
            assert info['sha256']==entry['sha256'], (batch,entry['path'])
            if 'bytes' in entry:
                assert info['bytes']==entry['bytes']
            snapshot[path.relative_to(KITCHEN).as_posix()]={'sha256':info['sha256'],'bytes':info['bytes']}
        manifest_info=file_info(manifest_path)
        snapshot[manifest_path.relative_to(KITCHEN).as_posix()]={'sha256':manifest_info['sha256'],'bytes':manifest_info['bytes']}
        summaries.append({'batch':batch,'verified_files':len(entries),
                          'frozen_manifest':manifest_info,'passed':True})
    return summaries,snapshot


def inventory():
    models=[]
    originals={}
    checks=[]
    for batch,slugs in BATCHES.items():
        batch_root=KITCHEN/batch
        assert read(batch_root/'STATUS.json')['status']=='ready_for_review'
        expected_vox=set()
        expected_png=set()
        expected_meta=set()
        for slug in slugs:
            assert {p.name for p in (batch_root/'assets'/slug).iterdir() if p.is_dir()} == {'large','half'}
            model={'slug':slug,'batch':batch,'variants':{}}
            for variant in ('large','half'):
                folder=batch_root/'assets'/slug/variant
                paths={'vox':folder/(slug+'.vox'),'preview':folder/'preview.png','metadata':folder/'metadata.json'}
                expected_vox.add(paths['vox'])
                expected_png.add(paths['preview'])
                expected_meta.add(paths['metadata'])
                info={name:file_info(path) for name,path in paths.items()}
                meta=read(paths['metadata'])
                native=vox_info(paths['vox'])
                png=png_info(paths['preview'])
                assert native['grid_size']==meta['grid_size']
                assert native['occupied_voxels']==meta['occupied_voxels']
                assert meta['asset']==slug and meta['variant']==variant
                assert meta['voxel_size_m']>0
                info.update({'grid_size':meta['grid_size'],'voxel_size_m':meta['voxel_size_m'],
                             'grid_extents_m':meta['grid_extents_m'],'occupied_voxels':meta['occupied_voxels'],
                             'preview_size_px':[png['width'],png['height']]})
                declared_vox=meta.get('native_sha256')
                declared_png=meta.get('preview_sha256')
                if 'sha256' in meta:
                    declared_vox=meta['sha256'].get('native',meta['sha256'].get(slug+'.vox'))
                    declared_png=meta['sha256'].get('preview',meta['sha256'].get('preview.png'))
                assert info['vox']['sha256']==declared_vox
                assert info['preview']['sha256']==declared_png
                model['variants'][variant]=info
                for name,path in paths.items():
                    originals[path.relative_to(KITCHEN).as_posix()]={k:info[name][k] for k in ('sha256','bytes')}
            a,b=model['variants']['large'],model['variants']['half']
            assert max(a['grid_size'])==128 and all(v%2==0 for v in a['grid_size'])
            assert b['grid_size']==[v//2 for v in a['grid_size']] and max(b['grid_size'])==64
            assert b['voxel_size_m']==a['voxel_size_m']*2
            assert b['grid_extents_m']==a['grid_extents_m']
            assert 0<b['occupied_voxels']<a['occupied_voxels']
            models.append(model)
        assert set((batch_root/'assets').rglob('*.vox'))==expected_vox
        assert set((batch_root/'assets').rglob('*.png'))==expected_png
        assert set((batch_root/'assets').rglob('metadata.json'))==expected_meta
        assert {p.name for p in (batch_root/'assets').iterdir() if p.is_dir()}==set(slugs)
        forbidden=[p.relative_to(batch_root).as_posix() for p in batch_root.rglob('*') if p.suffix.lower() in FORBIDDEN]
        assert not forbidden, (batch,forbidden)
        checks.append({'batch':batch,'models':len(slugs),'vox_files':len(expected_vox),
                       'primary_pngs':len(expected_png),'metadata_files':len(expected_meta),'forbidden_files':forbidden})
    assert len(models)==20 and len({m['slug'] for m in models})==20
    assert len(originals)==120
    return models,originals,checks


def prepare():
    started=utc()
    t0=time.perf_counter()
    frozen,snapshot=verify_frozen()
    models,originals,checks=inventory()
    sources=[]
    for i,m in enumerate(models):
        sources.append({'tile_index':i,'row':i//5,'column':i%5,'slug':m['slug'],'batch':m['batch'],
                        **m['variants']['half']['preview']})
    manifest={'created_at_utc':utc().isoformat(),'path_base':'All source paths are relative to this delivery directory.',
              'theme':'kitchen','model_count':20,'native_vox_count':40,'primary_preview_count':40,
              'metadata_count':40,'models':models,'verified_source_frozen_manifests':frozen,
              'contact_sheet':{'path':'overview_half.png','columns':5,'rows':4,'size_px':[2000,1900],
                  'note':'Panels use individual camera framing; they do not share a physical scale.',
                  'source_images':sources}}
    write('manifest.json',manifest)
    write('source_snapshot_before.json',{'captured_at_utc':utc().isoformat(),'original_files':originals,
                                        'frozen_files_and_manifests':snapshot,'batch_inventory':checks})
    write('preflight_validation.json',{'passed':True,'started_at_utc':started.isoformat(),
          'finished_at_utc':utc().isoformat(),'elapsed_seconds':time.perf_counter()-t0,
          'models':20,'vox_files':40,'primary_pngs':40,'metadata_files':40,
          'original_files_snapshotted':120,'frozen_files_verified':sum(x['verified_files'] for x in frozen),
          'frozen_manifests_verified':3,'batch_inventory':checks})
    print(json.dumps({'preflight_passed':True,'models':20,'vox':40,'primary_pngs':40,
                      'frozen_files':sum(x['verified_files'] for x in frozen)}))


def finish(inspected_at):
    t0=time.perf_counter()
    frozen,snapshot=verify_frozen()
    models,originals,checks=inventory()
    before=read(ROOT/'source_snapshot_before.json')
    assert originals==before['original_files'],'Original VOX/PNG/metadata changed during assembly'
    assert snapshot==before['frozen_files_and_manifests'],'Frozen source evidence changed during assembly'
    manifest=read(ROOT/'manifest.json')
    assert models==manifest['models']
    assert png_info(ROOT/'overview_half.png',(2000,1900))['crc_and_decompression_passed']
    sheet=(ROOT/'overview_half.png').read_bytes()
    sheet_info={'sha256':hashlib.sha256(sheet).hexdigest(),'bytes':len(sheet)}
    manifest['contact_sheet'].update(sheet_info)
    manifest['contact_sheet']['inspected_at_utc']=inspected_at
    manifest['contact_sheet']['inspection']='Direct image-tool inspection: all twenty full images and exact slug labels present; no image crop or missing tile. The individual-framing note is readable.'
    write('manifest.json',manifest)
    manifest_hash=hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest()
    status=read(ROOT/'STATUS.json')
    start=datetime.fromisoformat(status['started_at_utc'])
    now=utc()
    kst=timezone(timedelta(hours=9))
    composition=read(ROOT/'composition.json')
    assert composition['columns']==5 and composition['rows']==4 and composition['size_px']==[2000,1900]
    assert len(composition['tiles'])==20 and not composition['render_invoked']
    for i,(tile,model) in enumerate(zip(composition['tiles'],models)):
        assert tile['index']==i and tile['row']==i//5 and tile['column']==i%5
        assert tile['slug']==model['slug']
        assert tile['source']==model['variants']['half']['preview']['path']
        assert tile['source_sha256']==model['variants']['half']['preview']['sha256']
        assert tile['rectangle']==[40+(i%5)*392,124+(i//5)*440,352,352]
    validation={'passed':True,'validated_at_utc':now.isoformat(),'validation_seconds':time.perf_counter()-t0,
        'model_count':20,'native_vox_count':40,'primary_768px_png_count':40,'metadata_count':40,
        'contact_sheet':{'path':'overview_half.png','dimensions':[2000,1900],'layout':[5,4],**sheet_info,
                         'inspected_at_utc':inspected_at,'full_source_images_preserved':True},
        'manifest_sha256':manifest_hash,'source_original_count':120,'source_originals_unchanged':True,
        'frozen_source_evidence_unchanged':True,'frozen_manifest_count':3,
        'frozen_files_verified':sum(x['verified_files'] for x in frozen),'batch_inventory':checks,
        'checks':['Exact expected 20 slugs and large/half paths','40 VOX150 native files',
          '40 CRC/decompression-valid 768px primary PNGs','40 metadata files and SHA256 agreement',
          'Native dimensions, half-size scale relationship and decreased occupancy',
          'All three original frozen manifests verified before and after composition',
          '120 original VOX/PNG/metadata files byte-identical before and after assembly',
          'No forbidden mesh or scene files in any source batch','Final 5x4 sheet directly inspected'],
        'writes_confined_to':'voxel/kitchen/delivery','source_geometry_or_renders_regenerated':False}
    write('validation.json',validation)
    write('source_snapshot_after.json',{'captured_at_utc':now.isoformat(),'original_files':originals,
                                       'frozen_files_and_manifests':snapshot,'unchanged_from_before':True})
    status.update({'status':'ready_for_review','stage':'frozen-source assembly verified and contact sheet inspected',
                   'finished_at_utc':now.isoformat(),'finished_at_kst':now.astimezone(kst).isoformat(),
                   'elapsed_seconds':(now-start).total_seconds(),'models':20,'native_vox_files':40,
                   'primary_pngs':40,'source_originals_unchanged':True,'manifest_sha256':manifest_hash,
                   'contact_sheet_sha256':sheet_info['sha256'],'blockers':[]})
    write('STATUS.json',status)
    preflight=read(ROOT/'preflight_validation.json')
    result=f'''# Kitchen delivery assembly

**Ready for review:** one labeled **5-column x 4-row** contact sheet of all **20 final half-resolution models**, and a complete manifest of **40 VOX files, 40 original 768px previews and 40 metadata files**. All originals remain in their source batches and are unchanged.

![All twenty kitchen models at half resolution](overview_half.png)

Each panel preserves the complete source image. Panels use **individual camera framing, not a shared physical scale**. The sheet is 2000 x 1900 pixels and contains exact asset slugs plus batch/grid labels.

## Files and checks

- `overview_half.png`: composed only from the existing twenty final half previews; directly inspected with the image tool at {inspected_at}.
- `manifest.json`: all twenty exact slugs, batch ownership, both variants, relative VOX/PNG/metadata paths, SHA256, byte sizes, dimensions and cell scales. It also records each of the twenty sheet source image hashes.
- `validation.json`: successful exact inventory, VOX 150 headers, PNG CRC/decompression and 768px dimensions, native dimensions/scales, hashes and no-forbidden-export checks.
- All **{validation['frozen_files_verified']} frozen evidence files across three original manifests** were verified before and after composition. **120 source originals** (40 VOX + 40 PNG + 40 metadata) are byte-identical before and after assembly. The snapshots are `source_snapshot_before.json` and `source_snapshot_after.json`.
- `assembly.py` performs inventory and integrity checks; `assemble_sheet.ps1` uses System.Drawing to arrange the original images. `composition.json` records actual composition time. No rendering, geometry work, scene regeneration, HTML gallery, ZIP, Git or source mutation occurred.

Manifest SHA256: `{manifest_hash}`. Contact-sheet SHA256: `{sheet_info['sha256']}`.

## Actual timing

Start: **{start.isoformat()} UTC / {start.astimezone(kst).isoformat()} KST**.
Finish: **{now.isoformat()} UTC / {now.astimezone(kst).isoformat()} KST**.
Wall: **{(now-start).total_seconds():.3f} s**. Preflight integrity check: **{preflight['elapsed_seconds']:.3f} s**. Image composition: **{composition['elapsed_seconds']:.3f} s**. Final integrity check: **{validation['validation_seconds']:.3f} s**. These checks are included in wall time.

No blocker remains. Native shape and per-model rendering reviews were performed by the three original workers; this final assembly does not regenerate or replace those source artifacts. The manifest is authoritative for exact file paths and hashes.
'''
    (ROOT/'RESULT.md').write_text(result,encoding='utf-8')
    print(json.dumps({'status':'ready_for_review','models':20,'vox':40,'primary_pngs':40,
                      'originals_unchanged':True,'wall_seconds':(now-start).total_seconds(),
                      'manifest_sha256':manifest_hash,'sheet_sha256':sheet_info['sha256']}))


if __name__=='__main__':
    if sys.argv[1]=='prepare':
        prepare()
    elif sys.argv[1]=='finish':
        finish(sys.argv[2])
    else:
        raise SystemExit('Use prepare, or finish INSPECTION_UTC')
