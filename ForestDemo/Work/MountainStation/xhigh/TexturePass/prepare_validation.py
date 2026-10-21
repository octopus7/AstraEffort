from pathlib import Path
W=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass')
for name in ['validate_scene.py','capture_scene.py','runtime_validate.py']:
 s=(W.parent/name).read_text().replace("Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh')","Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass')")
 if name=='capture_scene.py':
  a=s.index("u.EditorLevelLibrary.load_level('/Game/Maps/MountainStation_xhigh')");b=s.index('report=validate()',a);s=s[:a]+s[b:]
  s=s.replace("if not report['success']:u.log_warning('Validation findings retained for repair: '+str(report['errors']))","assert report['success'], report['errors']")
  s=s.replace("manifest['render_target_format']=","manifest['first_delivery_camera_reference']='../FirstDelivery/Screenshots/capture_manifest.json'\nmanifest['render_target_format']=")
 if name=='runtime_validate.py':
  s=s.replace("v=hit.to_tuple();return {'blocking':bool(v[0]),'initial_overlap':bool(v[1]),'location_cm':vec(v[4]),'actor':v[9].get_name() if v[9] else None}","""v=hit.to_tuple();actor=next((x for x in v if isinstance(x,u.Actor)),None);comp=next((x for x in v if isinstance(x,u.PrimitiveComponent)),None)
 mesh=comp.static_mesh if isinstance(comp,u.StaticMeshComponent) else None
 return {'blocking':bool(v[0]),'initial_overlap':bool(v[1]),'location_cm':vec(v[4]),'actor':actor.get_path_name() if actor else None,'actor_label':actor.get_actor_label() if actor else None,'component':comp.get_path_name() if comp else None,'mesh':mesh.get_path_name() if mesh else None}""")
  s=s.replace("'supervisor_supplement_started_at_utc':'2026-10-21T12:46:44Z',","'texture_pass_started_at_utc':'2026-10-21T14:47:03+00:00',")
  s=s.replace("sweep=pawn.set_actor_location(u.Vector(x,y,-150),True,False);d=hit_data(sweep);","sweep_start=pawn.get_actor_location();sweep=pawn.set_actor_location(u.Vector(x,y,-150),True,False);d=hit_data(sweep);d['movement_start_cm']=vec(sweep_start);d['positive_distance_cm']=(pawn.get_actor_location()-sweep_start).length();")
  s=s.replace("d['same_ground_actor_as_trace']=d.get('actor')==data.get('actor');","d['same_ground_actor_as_trace']=d.get('actor')==data.get('actor');d['same_component_mesh_as_trace']=d.get('component')==data.get('component') and d.get('mesh')==data.get('mesh');")
  s=s.replace("x['blocking'] and not x['initial_overlap'] and x['same_ground_actor_as_trace']","x['blocking'] and not x['initial_overlap'] and x['positive_distance_cm']>1 and x['same_ground_actor_as_trace'] and x['same_component_mesh_as_trace'] and bool(x['component']) and bool(x['mesh'])")
 if name=='runtime_validate.py':
  s=s.replace("[('approach',-3800,-300,20,45),('ramp_middle'","[('approach',-3800,-300,20,45),('terrain',-4000,-1800,15,80),('ramp_middle'")
  s=s.replace("   result['checks']['runtime_floor_heights']","   expected_meshes={'approach':'SM_Paths','terrain':'SM_Terrain','ramp_middle':'SM_Platform','platform':'SM_Platform'}\n   result['checks']['exact_expected_ground_meshes']=all(x['mesh'].endswith('/'+expected_meshes[x['name']]+'.'+expected_meshes[x['name']]) for x in result['blocking_pawn_sweeps'])\n   result['checks']['runtime_floor_heights']")
 (W/name).write_text(s)
print('TexturePass validation helpers prepared from own original scripts.')
