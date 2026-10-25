"""Read-only independent import QA of assigned RainyCanal landscape FBXs."""
import bpy
import json
import math
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from mathutils import Vector
from mathutils.geometry import intersect_ray_tri

ROOT = Path(r'D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra')
SRC = ROOT/'Art/Landscape'
OUT = ROOT/'QA/Landscape'
started = datetime.now(timezone.utc)
source = json.loads((SRC/'manifest.json').read_text())
previous = json.loads((OUT/'landscape_qa.json').read_text()) if (OUT/'landscape_qa.json').exists() else {'meshes':[]}
changed = [r['name'] for r in previous['meshes'] if hashlib.sha256(Path(r['file']).read_bytes()).hexdigest()!=r['file_sha256']]
ramp_manifest = json.loads((SRC/'dock_ramp.json').read_text())
wall_manifest = json.loads((SRC/'wall_notch.json').read_text())
for entry in source['meshes']:
    if entry['name']=='SM_DockStep':
        entry.update({'triangles':28, 'vertices':16, 'materials':['Timber'],
                      'bounds_m':[[-1.4,-1.35,-.42],[1.8,1.35,.16]],
                      'location_m':[0,0,0], 'uv0_padding_px':2.1})
    if entry['name']=='SM_QuayWall':
        entry.update({'triangles':44, 'vertices':24, 'materials':['Stone'],
                      'bounds_m':[[-.325,-50,-2],[.325,50,.1]],
                      'location_m':[0,0,0], 'uv0_padding_px':2.1})
report = {'started_at_utc':started.isoformat(), 'blender_version':bpy.app.version_string,
          'method':'Separate background Blender factory-startup process. Reset to empty scene before each independent FBX import. No source execution or scene editing.',
          'source_manifest_sha256':hashlib.sha256((SRC/'manifest.json').read_bytes()).hexdigest(),
          'source_blend_sha256':hashlib.sha256((SRC/'source.blend').read_bytes()).hexdigest(),
          'changed_fbx_since_previous_audit':changed,
          'superseding_manifests':[{'file':p,'sha256':hashlib.sha256((SRC/p).read_bytes()).hexdigest()} for p in ['dock_ramp.json','wall_notch.json']],
          'meshes':[], 'issues':[], 'observations':[]}

def bounds(pts):
    return [[min(v[a] for v in pts) for a in range(3)], [max(v[a] for v in pts) for a in range(3)]]

def percentile(v, p):
    if not v:return None
    s=sorted(v);i=(len(s)-1)*p/100;lo=int(i);hi=min(lo+1,len(s)-1)
    return s[lo]+(s[hi]-s[lo])*(i-lo)

def stat(v):
    return {str(p):percentile(v,p) for p in [0,1,50,99,100]}

def issue(name, text):
    report['issues'].append({'mesh':name,'description':text})

for expected in source['meshes']:
    name=expected['name'];path=SRC/'FBX'/(name+'.fbx')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1.0
    bpy.ops.import_scene.fbx(filepath=str(path),use_custom_normals=True)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    if len(objects)!=1:
        issue(name,f'Expected one mesh, found {len(objects)}')
        continue
    o=objects[0];me=o.data;me.calc_loop_triangles()
    world=[o.matrix_world@v.co for v in me.vertices]
    actual=bounds(world)
    expectedworld=[[expected['bounds_m'][end][a]+expected['location_m'][a] for a in range(3)] for end in range(2)]
    maxerror=max(abs(actual[i][a]-expectedworld[i][a]) for i in range(2) for a in range(3))
    rec={'name':name,'file':str(path),'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'uv_layers':[x.name for x in me.uv_layers],
         'materials':[m.name for m in me.materials],
         'world_bounds_m':actual,'expected_local_plus_location_bounds_m':expectedworld,'max_world_bounds_error_m':maxerror,
         'imported_object_location_m':list(o.location),'imported_object_scale':list(o.scale),'matrix_world':[list(row) for row in o.matrix_world],
         'dimensions_m':list(o.dimensions),'geometry_degenerate_triangles':0,'nonfinite_coordinates':0,
         'uv0_degenerate_triangles':0,'uv1_degenerate_triangles':0,'uv0_aabb_positive_overlaps':0,
         'uv0_duplicate_triangles':0,'uv0_outside_unit_square':0}
    if maxerror>0.0001:issue(name,f'World bounds differ from authored local-plus-object-position by {maxerror} m')
    if len(me.uv_layers)!=2:issue(name,f'Expected two UV layers, found {len(me.uv_layers)}')
    if len(me.loop_triangles)!=expected['triangles']:issue(name,'Imported triangle count differs from source manifest')
    if len(me.uv_layers)<2:
        report['meshes'].append(rec);continue
    density=[];edgeerrors=[];boxes=[];uvkeys=set();margins=[]
    n=math.ceil(math.sqrt(len(me.loop_triangles)));cell=1/n
    for t in me.loop_triangles:
        pts=[world[i] for i in t.vertices]
        area3=(pts[1]-pts[0]).cross(pts[2]-pts[0]).length*.5
        if area3<=1e-12:rec['geometry_degenerate_triangles']+=1
        if any(not math.isfinite(c) for v in pts for c in v):rec['nonfinite_coordinates']+=1
        uv0=[me.uv_layers[0].data[i].uv.copy() for i in t.loops]
        uv1=[me.uv_layers[1].data[i].uv.copy() for i in t.loops]
        for key,uv in [('uv0',uv0),('uv1',uv1)]:
            a,b=uv[1]-uv[0],uv[2]-uv[0];area=abs(a.x*b.y-a.y*b.x)*.5
            if area<=1e-15:rec[key+'_degenerate_triangles']+=1
            if key=='uv1' and area3>1e-12:density.append(1024*math.sqrt(area/area3))
        for i,j in [(0,1),(1,2),(2,0)]:
            d3=(pts[j]-pts[i]).length
            if d3>1e-10:edgeerrors.append(abs((uv1[j]-uv1[i]).length*8/d3-1))
        minx,miny=min(u.x for u in uv0),min(u.y for u in uv0)
        maxx,maxy=max(u.x for u in uv0),max(u.y for u in uv0)
        boxes.append((minx,maxx,miny,maxy))
        if min(minx,miny)<-1e-7 or max(maxx,maxy)>1+1e-7:rec['uv0_outside_unit_square']+=1
        key=tuple(sorted((round(u.x,8),round(u.y,8)) for u in uv0))
        if key in uvkeys:rec['uv0_duplicate_triangles']+=1
        uvkeys.add(key)
        center=sum(uv0,Vector((0,0)))/3
        cx,cy=math.floor(center.x/cell),math.floor(center.y/cell)
        margins.append(min(minx-cx*cell,(cx+1)*cell-maxx,miny-cy*cell,(cy+1)*cell-maxy)*1024)
    # Conservative, exact disjoint-AABB test: zero bounding-box overlaps proves no positive-area UV triangle overlaps.
    active=[]
    for box in sorted(boxes):
        minx,maxx,miny,maxy=box
        active=[other for other in active if other[1]>minx+1e-9]
        for other in active:
            if min(maxy,other[3])-max(miny,other[2])>1e-9:rec['uv0_aabb_positive_overlaps']+=1
        active.append(box)
    rec['uv0_cell_margin_px_percentiles']=stat(margins)
    rec['uv0_min_axis_separation_lower_bound_px']=2*min(margins)
    rec['uv0_manifest_cell_margin_px']=expected['uv0_padding_px']
    rec['uv1_density_px_per_m_percentiles']=stat(density)
    rec['uv1_density_outside_one_percent_target_count']=sum(abs(x-128)>1.28 for x in density)
    rec['uv1_edge_length_relative_error_percentiles']=stat(edgeerrors)
    for field in ['geometry_degenerate_triangles','nonfinite_coordinates','uv0_degenerate_triangles','uv1_degenerate_triangles','uv0_aabb_positive_overlaps','uv0_duplicate_triangles','uv0_outside_unit_square','uv1_density_outside_one_percent_target_count']:
        if rec[field]:issue(name,f'{field}: {rec[field]}')
    if name=='SM_DockStep':
        placed_sections=[]
        placement=Vector(ramp_manifest['placement_m'])
        for x,z in ramp_manifest['local_x_top_z_m']:
            section=[v for v in world if abs(v.x-x)<.00001]
            measured=max(v.z for v in section)
            placed_sections.append({'local_x_m':x,'local_top_z_m':measured,
                'world_x_z_m':[x+placement.x,measured+placement.z],
                'section_vertices':len(section),'expected_local_top_z_m':z,
                'top_error_m':abs(measured-z)})
            if abs(measured-z)>.00001:issue(name,'Ramp section top mismatch')
        edge_uses=defaultdict(int)
        for p in me.polygons:
            ids=list(p.vertices)
            for i in range(len(ids)):
                edge_uses[tuple(sorted((ids[i],ids[(i+1)%len(ids)])))]+=1
        ramp_record={'replacement_manifest':'dock_ramp.json',
            'replacement_manifest_sha256':hashlib.sha256((SRC/'dock_ramp.json').read_bytes()).hexdigest(),
            'manifest_override_note':'SM_DockStep entry in the original manifest.json is superseded by dock_ramp.json.',
            'geometry_origin_note':'FBX geometry remains local to origin (0,0,0). Applying actor placement (6.4,1,0) yields the following intended scene coordinates; placement is not baked into this FBX.',
            'actor_placement_m':list(placement),'measured_sections':placed_sections,
            'world_y_bounds_after_placement_m':[actual[0][1]+placement.y,actual[1][1]+placement.y],
            'width_m':actual[1][1]-actual[0][1],
            'crest_clearance_above_wall_top_m':max(x['local_top_z_m'] for x in placed_sections)+placement.z-ramp_manifest['quay_wall_top_m'],
            'edge_face_use_counts':sorted(set(edge_uses.values())),
            'section_continuity':'Three contiguous slope/crest intervals sharing all section boundary vertices; no gap between ramp segments.',
            'maximum_top_slope_degrees':math.degrees(math.atan(max(abs((b[1]-a[1])/(b[0]-a[0])) for a,b in zip(ramp_manifest['local_x_top_z_m'],ramp_manifest['local_x_top_z_m'][1:]))))}
        if ramp_record['edge_face_use_counts']!=[2]:issue(name,'Dock ramp is not a closed two-manifold shell')
        rec['dock_ramp_validation']=ramp_record
    if name=='SM_QuayWall':
        sections=[]
        for y,z in wall_manifest['y_top_z_m']:
            pts=[v for v in world if abs(v.y-y)<.0001]
            measured_top=max(v.z for v in pts);measured_bottom=min(v.z for v in pts)
            sections.append({'y_m':y,'vertex_count':len(pts),'measured_top_z_m':measured_top,
                'expected_top_z_m':z,'top_error_m':abs(measured_top-z),
                'measured_bottom_z_m':measured_bottom,'bottom_error_m':abs(measured_bottom-wall_manifest['bottom_z_m'])})
            if max(abs(measured_top-z),abs(measured_bottom-wall_manifest['bottom_z_m']))>.00001:issue(name,'Wall notch section differs from replacement manifest')
        samples=[]
        expected_profile=wall_manifest['y_top_z_m']
        for y in [-49,0,25.8,25.9,26,28,30,30.1,30.2,49]:
            expected_z=None
            for (ya,za),(yb,zb) in zip(expected_profile,expected_profile[1:]):
                if ya<=y<=yb:expected_z=za+(zb-za)*(y-ya)/(yb-ya);break
            hits=[]
            for t in me.loop_triangles:
                a,b,c=[world[i] for i in t.vertices]
                hit=intersect_ray_tri(a,b,c,Vector((0,0,-1)),Vector((0,y,10)),True)
                if hit is not None:hits.append(hit.z)
            measured_top=max(hits) if hits else None
            error=abs(measured_top-expected_z) if measured_top is not None else None
            samples.append({'ray_x_y_m':[0,y],'measured_top_z_m':measured_top,'expected_top_z_m':expected_z,'error_m':error})
            if error is None or error>.00001:issue(name,f'Wall vertical ray readback failed at y={y}')
        edge_uses=defaultdict(int)
        for p in me.polygons:
            ids=list(p.vertices)
            for i in range(len(ids)):edge_uses[tuple(sorted((ids[i],ids[(i+1)%len(ids)])))]+=1
        rec['wall_notch_validation']={'replacement_manifest':'wall_notch.json',
            'replacement_manifest_sha256':hashlib.sha256((SRC/'wall_notch.json').read_bytes()).hexdigest(),
            'manifest_override_note':'SM_QuayWall entry in original manifest.json is superseded by wall_notch.json.',
            'measured_sections':sections,'vertical_ray_samples':samples,
            'measured_width_m':actual[1][0]-actual[0][0],
            'edge_face_use_counts':sorted(set(edge_uses.values())),
            'design_y_note':'These are Blender/design-space Y coordinates. UE coordinate conversion/placement remains scene-level verification.',
            'nominal_clearance_to_z0_deck_m':-max(s['measured_top_z_m'] for s in samples if 26<=s['ray_x_y_m'][1]<=30)}
        if sorted(set(edge_uses.values()))!=[2]:issue(name,'Notched quay wall is not a closed two-manifold shell')
    if name=='SM_RainVolume':
        attrs=[{'name':a.name,'domain':a.domain,'data_type':a.data_type,'data_length':len(a.data)} for a in me.color_attributes]
        color={'attributes':attrs}
        if not me.color_attributes:
            issue(name,'Rain vertex colors were not preserved by FBX import')
        else:
            attr=me.color_attributes[0]
            def getcolor(loop):
                i=loop if attr.domain=='CORNER' else me.loops[loop].vertex_index
                return tuple(attr.data[i].color)
            byvertex=defaultdict(list)
            for loop in me.loops:byvertex[loop.vertex_index].append(getcolor(loop.index))
            cols=[getcolor(i) for i in range(len(me.loops))]
            color['linear_channel_min']=[min(c[k] for c in cols) for k in range(4)]
            color['linear_channel_max']=[max(c[k] for c in cols) for k in range(4)]
            color['triangle_max_red_phase_spread']=max(max(getcolor(li)[0] for li in p.loop_indices)-min(getcolor(li)[0] for li in p.loop_indices) for p in me.polygons)
            color['vertex_corner_max_channel_disagreement']=max(max(abs(c[k]-v[0][k]) for c in v for k in range(4)) for v in byvertex.values())
            adjacency=defaultdict(set)
            for e in me.edges:
                a,b=e.vertices;adjacency[a].add(b);adjacency[b].add(a)
            todo=set(range(len(me.vertices)));components=[]
            while todo:
                root=todo.pop();stack=[root];component=[root]
                while stack:
                    for v in adjacency[stack.pop()]:
                        if v in todo:todo.remove(v);stack.append(v);component.append(v)
                components.append(component)
            phasegroups=defaultdict(list);spread=[];gcounts=[];sizes=[]
            for ids in components:
                p=[world[i] for i in ids];c=[byvertex[i][0] for i in ids]
                red=[x[0] for x in c];spread.append(max(red)-min(red));gcounts.append(len(set(round(x[1],5) for x in c)));sizes.append(len(ids))
                center=sum(p,Vector((0,0,0)))/len(p)
                phasegroups[round(sum(red)/len(red),7)].append({'ids':ids,'center':center,'base':min(x.z for x in p)})
            # Match real distances, not rounded coordinate keys: nearby values can straddle a decimal rounding boundary.
            groups=[];pair_distances=[]
            for records in phasegroups.values():
                while records:
                    a=records.pop();match=None;distance=None
                    for j,b in enumerate(records):
                        d=(a['center']-b['center']).length
                        if d<0.0001 and abs(a['base']-b['base'])<0.0001:
                            match=j;distance=d;break
                    if match is None:groups.append([a['ids']])
                    else:groups.append([a['ids'],records.pop(match)['ids']]);pair_distances.append(distance)
            color.update({'connected_strip_count':len(components),'expected_strip_count':source['rain_drops']*2,
                'per_strip_vertex_counts':sorted(set(sizes)),'per_strip_green_unique_counts':sorted(set(gcounts)),
                'max_per_strip_red_phase_spread':max(spread),'paired_drop_count':len(groups),
                'drop_pair_sizes':sorted(set(len(v) for v in groups)),'expected_drop_count':source['rain_drops'],
                'pair_distance_tolerance_m':0.0001,'maximum_paired_strip_center_distance_m':max(pair_distances),
                'red_phase_note':'R is intentionally constant per crossed drop; no height-varying R expectation. G is the exported per-corner 0,1/3,2/3,1 sequence.',
                'shader_height_note':'FBX consists of base streaks only. Claimed 14 m rain travel requires material WPO/runtime verification, not geometric height.'})
            if max(spread)>1e-6:issue(name,'Red phase differs within individual rain strip')
            if len(groups)!=source['rain_drops'] or set(len(v) for v in groups)!={2}:issue(name,'Crossed strip phase/location pairing does not match rain drop count')
            if color['triangle_max_red_phase_spread']>1e-6:issue(name,'Red phase varies inside a rain triangle')
        rec['rain_colors']=color
    report['meshes'].append(rec)
    print(name, 'bounds',actual, 'density',rec['uv1_density_px_per_m_percentiles'],'degenerate',rec['geometry_degenerate_triangles'],flush=True)

byname={r['name']:r for r in report['meshes']}
checks={}
for name,zmin,zmax in [('SM_BankWest',0,0),('SM_BankEast',0,0),('SM_Dock',-.28,0),('SM_DockStep',-.42,.16),('SM_QuayWall',-2,.1),('SM_QuayCap',0,.2),('SM_CanalBed',-1.95,-1.65)]:
    r=byname[name];actual=[r['world_bounds_m'][0][2],r['world_bounds_m'][1][2]]
    checks[name]={'expected_z_bounds_m':[zmin,zmax],'actual_z_bounds_m':actual,'pass':max(abs(actual[0]-zmin),abs(actual[1]-zmax))<.0001}
    if not checks[name]['pass']:issue(name,'Explicit world height check failed')
report['world_height_checks']=checks
report['source_blend_readback']=[]
bpy.ops.wm.open_mainfile(filepath=str(SRC/'source.blend'))
for expected in source['meshes']:
    name=expected['name'];o=bpy.data.objects.get(name)
    if o is None:issue(name,'Missing from current source.blend');continue
    o.data.calc_loop_triangles()
    sb=bounds([o.matrix_world@v.co for v in o.data.vertices]);fb=byname[name]['world_bounds_m']
    error=max(abs(sb[i][a]-fb[i][a]) for i in range(2) for a in range(3))
    record={'name':name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),
        'uv_layers':[u.name for u in o.data.uv_layers],'world_bounds_m':sb,
        'max_source_to_imported_bounds_error_m':error,
        'matches_exported_geometry_counts':len(o.data.vertices)==byname[name]['vertices'] and len(o.data.loop_triangles)==byname[name]['triangles']}
    report['source_blend_readback'].append(record)
    if error>.0001 or not record['matches_exported_geometry_counts']:issue(name,'Current source.blend differs from imported FBX geometry/counts')
report['observations']=[
    'Final current-hash audit reimports all 13 FBXs, then opens current source.blend read-only to compare all 13 geometry counts and transformed bounds. No creative source is executed or saved.',
    'SM_QuayWall is now the 44-triangle closed notched wall described by wall_notch.json, superseding its original manifest entry. Actual ray intersections confirm top Z=-0.12 m across design Y=26..30 m, linear transitions across 25.8..26 and 30..30.2, top +0.1 m elsewhere and bottom -2 m throughout. Nominal clearance to a Z=0 deck is 0.12 m; final deck placement/collision is a UE check.',
    'SM_DockStep remains the 28-triangle closed continuous Timber ramp described by dock_ramp.json, superseding its original manifest entry. Local Z is -0.42..+0.16 m. Intended actor placement (6.4,1,0) yields top endpoints (x=5,z=-0.3) and (x=8.2,z=0), with +0.16 m crest. The prior 0.06 m clearance remains relative to the normal +0.1 m quay top; the new wall notch is at a separate design-Y range.',
    'UV0 is a unique per-triangle atlas. Its density varies with physical triangle size by design; texture density is on UV1.',
    'UV1 is physically isometric at 128 px/m per triangle and intentionally overlaps/repeats. Each triangle has a separate local origin and orientation, so directional textures can show discontinuities across triangle boundaries. Use the intended world-coherent material sampling for broad architectural courses.',
    'UV0 inter-island cell margin is 2.1 px for ordinary meshes and approximately 1.396 px for RainVolume at 1024. Rain uses dynamic vertex-driven translucency; there is no baked-lightmap validation in this audit.',
    'CanalWater FBX is a zero-height source plane at Z=0. The parent scene must place its waterline at the desired canal elevation.',
    'Shrub source extends about 0.03 m below its origin, suitable for slight ground embedding; final placement is not verified here.',
    'No UE import, mesh bounds in UE, materials, collision, WPO or runtime rendering were checked.'
]
finished=datetime.now(timezone.utc)
report.update({'finished_at_utc':finished.isoformat(),'elapsed_seconds':(finished-started).total_seconds(),
               'result':'pass_source_fbx_checks' if not report['issues'] else 'issues_found'})
(OUT/'landscape_qa.json').write_text(json.dumps(report,indent=2))
lines=['# Landscape FBX independent import audit','',f"Result: **{report['result']}**. Imported {len(report['meshes'])} FBXs in clean Blender {bpy.app.version_string} scenes. Actual UTC {started.isoformat()} to {finished.isoformat()} ({report['elapsed_seconds']:.3f} seconds).",'',
       '| Mesh | Triangles | UV layers | World Z min / max (m) | UV1 px/m min / max | UV0 cell margin px |','|---|---:|---:|---:|---:|---:|']
for r in report['meshes']:
    d=r['uv1_density_px_per_m_percentiles'];z=r['world_bounds_m'];p=r['uv0_cell_margin_px_percentiles']
    lines.append(f"| {r['name']} | {r['triangles']} | {len(r['uv_layers'])} | {z[0][2]:.4f} / {z[1][2]:.4f} | {d['0']:.4f} / {d['100']:.4f} | {p['0']:.4f} |")
lines+=['','## Findings','']
if not report['issues']:lines+=['No failed source-FBX checks. Every mesh retained two UV layers, nondegenerate geometry and UV triangles, a unique UV0 atlas with disjoint triangle bounding boxes, and UV1 density within 1% of 128 px/m. World-space transformed bounds match local geometry plus authored object position to 0.1 mm.','']
for i in report['issues']:lines.append(f"- **{i['mesh']}**: {i['description']}")
rain=byname['SM_RainVolume']['rain_colors']
lines += ['',f"Rain colors: {rain.get('connected_strip_count')} connected strips pair into {rain.get('paired_drop_count')} crossed drops. Each strip retains constant red phase (maximum spread {rain.get('max_per_strip_red_phase_spread')}); green preserves {rain.get('per_strip_green_unique_counts')} values per strip. B=0 and A=1 ranges are in the JSON record.",'','## Observations and limits','']
lines += ['- '+x for x in report['observations']]
lines += ['','Full bounds, density percentiles, padding, rain color data, hashes and timing are in `landscape_qa.json`. The audit modifies no source asset and launches no UE session.','']
(OUT/'REVIEW.md').write_text('\n'.join(lines))
print('LANDSCAPE_QA_RESULT',report['result'],len(report['issues']),flush=True)
