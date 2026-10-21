"""Read final Blender geometry and refresh metadata without altering source exports."""
import bpy,json,datetime,math
from pathlib import Path
root=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra')
bpy.ops.wm.open_mainfile(filepath=str(root/'SourceArt/AlderPass.blend'))
data=json.loads((root/'art_manifest.json').read_text())
for entry in data['meshes']:
    obj=bpy.data.objects[entry['name']]
    entry.update(vertices=len(obj.data.vertices),polygons=len(obj.data.polygons),materials=[m.name for m in obj.data.materials])
data.update(metadata_refreshed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authoritative_source='SourceArt/AlderPass.blend',ramp_plan_run_cm=math.hypot(1300,300))
(root/'art_manifest.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
summary={'theme':'MountainStation','effort':'ultra','source':'Direct authoring in independent background Blender','mesh_groups':len(data['meshes']),'source_vertices':sum(e['vertices'] for e in data['meshes']),'source_polygons':sum(e['polygons'] for e in data['meshes']),'site_cm':[10000,10000],'ramp_plan_run_cm':math.hypot(1300,300),'ramp_rise_cm':112,'ramp_slope_degrees':math.degrees(math.atan2(112,math.hypot(1300,300))),'artistic_references':[],'notes':['No generated images or borrowed scene assets.','The final .blend and FBX files are authoritative. Historical revision scripts are not idempotent; do not replay them.','Metadata refreshed from the final .blend; geometry and FBX exports were not modified.']}
(root/'source_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
