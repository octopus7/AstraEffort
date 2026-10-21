import unreal as u, json, datetime, traceback
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/TexturePass')
eas=u.get_editor_subsystem(u.EditorAssetSubsystem);ml=u.MaterialEditingLibrary;levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
report={}
try:
 levels.load_level('/Game/Maps/ultra')
 build=json.loads((ROOT/'build_result.json').read_text())
 for name,meta in build['materials'].items():
  mat=eas.load_asset('/Game/Forest/ultra/Materials/M_'+name)
  if 'texture' in meta:
   base=ml.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR)
   base.set_editor_property('code','float l=dot(C,float3(0.2126,0.7152,0.0722));return Tint*(0.94+0.28*l);')
   meta['base_color']='Generated albedo luminance modulates palette: Tint*(0.94+0.28*luminance). Contrast restrained after actual render review.'
  elif name in ['Sea','Lake']:
   base=ml.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR);code=base.get_editor_property('code')
   if name=='Sea':code=code.replace('float3(.12,.35,.36)','float3(.045,.28,.32)')
   else:code=code.replace('float3(.12,.32,.27)','float3(.035,.24,.21)').replace('float3(.20,.42,.34)','float3(.08,.32,.27)')
   base.set_editor_property('code',code)
   ml.get_material_property_input_node(mat,u.MaterialProperty.MP_EMISSIVE_COLOR).set_editor_property('const_b',.75)
   ml.get_material_property_input_node(mat,u.MaterialProperty.MP_OPACITY).set_editor_property('r',.82 if name=='Sea' else .76)
   ml.get_material_property_input_node(mat,u.MaterialProperty.MP_SPECULAR).set_editor_property('r',.12)
  elif name=='Foam':
   mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
   mat.set_editor_property('translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE)
   mask=ml.get_material_property_input_node(mat,u.MaterialProperty.MP_OPACITY_MASK)
   mask.set_editor_property('code','float shift=10*sin(T*.7+P.x*.004);float coast=3200-220*sin(P.x*.00075)-150*cos(P.x*.0013+.5);float edge=0;[unroll] for(int i=0;i<3;i++){float center=coast+200+i*165-20*sin(P.x*.006+i)+shift;float halfwidth=(i==0)?6:3.25;edge=max(edge,1-smoothstep(.25,1,abs(P.y-center)/halfwidth));}float b=.5+.5*sin(P.x*.029+sin(P.x*.071+T*.8)*2-T*1.25);return edge*(.12+.72*smoothstep(.15,.9,b));')
   assert ml.connect_material_property(mask,'',u.MaterialProperty.MP_OPACITY)
   wpo=ml.get_material_property_input_node(mat,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
   wpo.set_editor_property('code','float shift=10*sin(T*.7+P.x*.004);float y=P.y+shift;float z=-34+2.5*sin(P.x*.007-y*.008)+3.2*sin(y*.013-T*1.8+sin(P.x*.004))+1.4*sin(P.x*.011+y*.008-T*.9);return float3(0,shift,z+2-P.z);')
  elif name=='Terrain':
   node=ml.get_material_property_input_node(mat,u.MaterialProperty.MP_EMISSIVE_COLOR)
   node.set_editor_property('code',node.get_editor_property('code').replace('float3(.30,.43,.29)','float3(.16,.25,.17)'))
  ml.recompile_material(mat);eas.save_loaded_asset(mat)
  report[name]={'expressions':ml.get_num_material_expressions(mat)}
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh.get_name()=='SM_Surf':a.static_mesh_component.set_cast_shadow(False)
 levels.save_current_level()
 build['material_refinement_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ROOT/'build_result.json').write_text(json.dumps(build,indent=2))
 (ROOT/'material_refinement.json').write_text(json.dumps({'finished_at_utc':build['material_refinement_at_utc'],'reason':'Actual first texture-pass renders showed excessive triangle texture contrast and gray water; restrained texture contrast, strengthened teal water, subdued caustics, disabled foam shadows. Geometry, UVs, layout and collision unchanged.','materials':report,'success':True},indent=2))
except Exception:(ROOT/'refinement_error.txt').write_text(traceback.format_exc());raise
finally:u.SystemLibrary.quit_editor()
