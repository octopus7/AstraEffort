"""Independent saved-file and export roundtrip checks. No deliverable is modified."""
import bpy, sys, json, math, hashlib
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
asset_dir=Path(args[0]).resolve();slug=asset_dir.name
out_dir=Path(__file__).resolve().parent/'validation';out_dir.mkdir(exist_ok=True)
def inspect(objects):
    objs=[o for o in objects if o.type=='MESH']
    pts=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
    bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]] if pts else [[0]*3,[0]*3]
    tris=0;bad=[];zero_area=0
    for o in objs:
        o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
        zero_area+=sum(t.area<=1e-12 for t in o.data.loop_triangles)
        if any(not math.isfinite(v) for p in o.data.vertices for v in p.co):bad.append(o.name)
    return {'mesh_objects':len(objs),'triangles':tris,'bounds':bounds,'dimensions_m':[bounds[1][i]-bounds[0][i] for i in range(3)],'nonfinite_meshes':bad,'missing_uv':[o.name for o in objs if not o.data.uv_layers],'missing_materials':[o.name for o in objs if not o.data.materials],'degenerate_triangles':zero_area,'cameras':sum(o.type=='CAMERA' for o in objects),'lights':sum(o.type=='LIGHT' for o in objects),'materials':sorted({m.name for o in objs for m in o.data.materials if m})}

report={'asset':slug,'checked_at_utc':datetime.now(timezone.utc).isoformat(),'blender':bpy.app.version_string,'checks':{},'errors':[]}
files=[asset_dir/(slug+ext) for ext in ['.blend','.glb','.fbx']]
for p in files:
    if not p.is_file() or p.stat().st_size<1000:report['errors'].append('Missing or empty '+str(p))
if report['errors']:
    (out_dir/(slug+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');raise RuntimeError(report['errors'])
bpy.ops.wm.open_mainfile(filepath=str(files[0]))
coll=bpy.data.collections.get('ASSET')
if coll is None:report['errors'].append('Missing ASSET collection');objects=list(bpy.context.scene.objects)
else:objects=list(coll.all_objects)
report['source']=inspect(objects)
report['source']['unit_system']=bpy.context.scene.unit_settings.system
report['source']['scale_length']=bpy.context.scene.unit_settings.scale_length
report['source']['unpacked_missing_images']=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).is_file()]
for kind,p in [('glb',files[1]),('fbx',files[2])]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if kind=='glb':bpy.ops.import_scene.gltf(filepath=str(p))
    else:bpy.ops.import_scene.fbx(filepath=str(p),use_anim=False)
    bpy.context.view_layer.update()
    report[kind]=inspect(list(bpy.context.scene.objects))
    if report[kind]['cameras'] or report[kind]['lights']:report['errors'].append(kind+' contains studio camera/light')
    if any(abs(a-b)>max(.005,abs(a)*.005) for a,b in zip(report['source']['dimensions_m'],report[kind]['dimensions_m'])):report['errors'].append(kind+' bounds differ from source by more than 0.5% / 5mm')
    if report[kind]['triangles']!=report['source']['triangles']:report['errors'].append(kind+' triangle count differs from saved source')
for kind in ['source','glb','fbx']:
    st=report[kind]
    if st['mesh_objects']<1 or st['triangles']<1:report['errors'].append(kind+' has no geometry')
    if st['degenerate_triangles']:report['errors'].append(kind+' has zero-area triangles: '+str(st['degenerate_triangles']))
    for field in ['missing_uv','missing_materials','nonfinite_meshes']:
        if st[field]:report['errors'].append(kind+' '+field+': '+str(st[field]))
if report['source']['unpacked_missing_images']:report['errors'].append('Missing external image dependencies')
report['render_files']={}
for name in ['hero.png','rear.png']:
    p=asset_dir/'renders'/name
    report['render_files'][name]={'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else 0}
    if not p.is_file() or p.stat().st_size<10000:report['errors'].append('Missing actual render '+name)
report['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
report['passed']=not report['errors']
(out_dir/(slug+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SET01_REOPEN_VALIDATION '+json.dumps(report))
if report['errors']:raise RuntimeError(report['errors'])
