"""Targeted UV correction of the central frame, then fresh atlas/export/render."""
import bpy,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];START=time.time()
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('RB_')]
frame=bpy.data.objects['RB_Frame'];scene=bpy.context.scene
scene.tool_settings.use_uv_select_sync=True
bpy.ops.object.select_all(action='DESELECT');frame.select_set(True);bpy.context.view_layer.objects.active=frame
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.1344640138,island_margin=0,area_weight=0,correct_aspect=True,scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.average_islands_scale()
bpy.ops.uv.pack_islands('EXEC_DEFAULT',rotate=True,scale=True,merge_overlap=False,margin_method='FRACTION',margin=.002,shape_method='CONVEX')
bpy.ops.object.mode_set(mode='OBJECT')
exec(compile((ROOT/'source'/'diagnose_uv.py').read_text(encoding='utf-8'),str(ROOT/'source'/'diagnose_uv.py'),'exec'),{'__file__':str(ROOT/'source'/'diagnose_uv.py')})
diagnosis=json.loads((ROOT/'validation'/'uv_diagnosis.json').read_text())
assert not diagnosis['overlap_faces'], 'UV diagnostic still detects overlap'
mats=sorted({m for o in meshes for m in o.data.materials if m},key=lambda m:m.name)
atlas=bpy.data.images['RabbitBike_BaseColor_4096']
for m in mats:
    n=m.node_tree.nodes;bs=n.get('Principled BSDF');em=n.new('ShaderNodeEmission');em.name='Temporary_Final_Bake'
    source=n.get('Generated_Source')
    if source:
        mixers=[v for v in n if v.bl_idname=='ShaderNodeMixRGB']
        socket=mixers[0].outputs['Color'] if mixers else source.outputs['Color']
        m.node_tree.links.new(socket,em.inputs['Color'])
    else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
    m.node_tree.links.new(em.outputs[0],n.get('Material Output').inputs['Surface'])
    for node in n:node.select=False
    n['Final_Unique_Atlas'].select=True;n.active=n['Final_Unique_Atlas']
scene.cycles.samples=1;bpy.ops.object.bake(type='EMIT',use_clear=True,margin=8)
atlas.filepath_raw=str(ROOT/'textures'/'RabbitBike_BaseColor_4096.png');atlas.file_format='PNG';atlas.save()
if atlas.packed_file:atlas.unpack(method='REMOVE')
atlas.reload();atlas.pack()
for m in mats:
    n=m.node_tree.nodes;m.node_tree.links.new(n.get('Principled BSDF').outputs['BSDF'],n.get('Material Output').inputs['Surface']);n.remove(n['Temporary_Final_Bake'])
bpy.ops.export_scene.gltf(filepath=str(ROOT/'RabbitBike.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
scene.cycles.samples=48
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'RabbitBike.blend'))
manifest=json.loads((ROOT/'validation'/'build_manifest.json').read_text())
manifest['source_uv_repetition_before_unique_bake']={'ivory':4,'orange':4,'rubber_and_saddle':8}
manifest['rubber_generated_color_mix']=.12
manifest['uv']='Unique global 0-1; analytical tires and thin shell lofts; projected central frame/individual components; area-normalized charts'
manifest['final_frame_uv_repair_seconds']=time.time()-START
(ROOT/'validation'/'build_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
scene.render.filepath=str(ROOT/'renders'/'hero.png');bpy.ops.render.render(write_still=True)
print('FINALIZE_DONE',flush=True)
