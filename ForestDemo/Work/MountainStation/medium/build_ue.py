import unreal as u, os, json, datetime, traceback, time
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
ROOT='/Game/MountainStation/medium'
MAP='/Game/Maps/MountainStation_medium'
E=u.get_editor_subsystem(u.EditorActorSubsystem)
L=u.get_editor_subsystem(u.LevelEditorSubsystem)
L.new_level('/Engine/Maps/Templates/Template_Default') if False else None
# New empty map is non-World-Partition.
if u.EditorAssetLibrary.does_asset_exist(MAP): L.load_level(MAP)
else: L.new_level(MAP)
for actor in E.get_all_level_actors(): E.destroy_actor(actor)
tools=u.AssetToolsHelpers.get_asset_tools()
palette=json.load(open(W+'/art_manifest.json'))['palette']
materials={}
for name,rgb in palette.items():
 m=u.load_asset(ROOT+'/Materials/M_'+name) if u.EditorAssetLibrary.does_asset_exist(ROOT+'/Materials/M_'+name) else tools.create_asset('M_'+name,ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
 u.MaterialEditingLibrary.delete_all_material_expressions(m)
 c=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector,-300,0)
 c.set_editor_property('constant',u.LinearColor(*rgb,1))
 u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 r=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant,-300,200); r.set_editor_property('r',.78)
 u.MaterialEditingLibrary.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
 m.set_editor_property('two_sided',True)
 u.MaterialEditingLibrary.recompile_material(m); materials[name]=m
task=u.AssetImportTask(); task.filename=W+'/AlderPass.fbx'; task.destination_path=ROOT+'/Meshes'; task.destination_name='SM_AlderPass'; task.automated=True; task.replace_existing=True; task.save=True
opts=u.FbxImportUI(); opts.import_mesh=True; opts.import_materials=False; opts.import_textures=False; opts.import_as_skeletal=False
opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.auto_generate_collision=False
task.options=opts; tools.import_asset_tasks([task])
paths=list(task.imported_object_paths)
mesh=next(u.load_asset(p) for p in paths if isinstance(u.load_asset(p),u.StaticMesh))
for i,slot in enumerate(mesh.get_editor_property('static_materials')):
 n=str(slot.get_editor_property('imported_material_slot_name'))
 if n in materials: mesh.set_material(i,materials[n])
 else: print('UNMATCHED MATERIAL '+n)
mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
mesh.get_editor_property('body_setup').set_editor_property('double_sided_geometry',True)
sms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
for section in range(mesh.get_num_sections(0)): sms.enable_section_collision(mesh,True,0,section)
sms.set_lod_build_settings(mesh,0,sms.get_lod_build_settings(mesh,0))
actor=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0)); actor.set_actor_label('Alder Pass | authored terrain architecture railway props')
actor.static_mesh_component.set_static_mesh(mesh); actor.static_mesh_component.set_collision_profile_name('BlockAll')
sun=E.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,2000),u.Rotator(pitch=-48,yaw=-32,roll=0)); sun.set_actor_label('Afternoon sun')
sun.light_component.set_mobility(u.ComponentMobility.MOVABLE); sun.light_component.set_editor_property('intensity',4.0)
sun.light_component.set_editor_property('light_color',u.Color(255,241,220,255))
sky=E.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,1200)); sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property('intensity',1.2)
sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
cube=u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap.DaylightAmbientCubemap')
if cube: sky.light_component.set_editor_property('cubemap',cube)
atmo=E.spawn_actor_from_class(u.SkyAtmosphere,u.Vector(0,0,-500))
sun.light_component.set_editor_property('atmosphere_sun_light',True)
backmat=u.load_asset(ROOT+'/Materials/M_Backdrop') if u.EditorAssetLibrary.does_asset_exist(ROOT+'/Materials/M_Backdrop') else tools.create_asset('M_Backdrop',ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
u.MaterialEditingLibrary.delete_all_material_expressions(backmat)
backmat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT); backmat.set_editor_property('two_sided',True)
bc=u.MaterialEditingLibrary.create_material_expression(backmat,u.MaterialExpressionConstant3Vector,-200,0); bc.set_editor_property('constant',u.LinearColor(.12,.17,.20,1))
u.MaterialEditingLibrary.connect_material_property(bc,'',u.MaterialProperty.MP_EMISSIVE_COLOR); u.MaterialEditingLibrary.recompile_material(backmat)
back=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0)); back.set_actor_label('Quiet blue horizon')
back.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere')); back.static_mesh_component.set_material(0,backmat)
back.set_actor_scale3d(u.Vector(2000,2000,2000)); back.static_mesh_component.set_collision_profile_name('NoCollision'); back.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION); back.set_actor_enable_collision(False); back.static_mesh_component.set_editor_property('cast_shadow',False)
start=E.spawn_actor_from_class(u.PlayerStart,u.Vector(-1900,-1150,120),u.Rotator(pitch=0,yaw=90,roll=0)); start.set_actor_label('Walk in via accessible west ramp')
cls=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger'); logger=E.spawn_actor_from_class(cls,u.Vector(0,0,0))
logger.set_actor_label('Baseline Hello retained')
cam=E.spawn_actor_from_class(u.CameraActor,u.Vector(12000,-12000,16000),u.MathLibrary.find_look_at_rotation(u.Vector(12000,-12000,16000),u.Vector(0,0,0)))
cam.set_actor_label('Overview composition'); cam.camera_component.set_editor_property('projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC); cam.camera_component.set_editor_property('ortho_width',20000)
u.EditorAssetLibrary.save_directory(ROOT,only_if_is_dirty=False,recursive=True)
L.save_current_level()
validation_started=time.perf_counter()
L.load_level(MAP)
reg=u.AssetRegistryHelpers.get_asset_registry(); reg.scan_paths_synchronous([ROOT,'/Game/Maps'],force_rescan=True)
opt=u.AssetRegistryDependencyOptions(True,True,False,False,False)
todo=[MAP]; seen=set(); bad=[]; deps={}
while todo:
 p=todo.pop()
 if p in seen: continue
 seen.add(p); children=[str(x) for x in reg.get_dependencies(p,opt)]; deps[p]=children
 for ch in children:
  if ch.startswith('/Game/'):
   if not(ch.startswith(ROOT+'/') or ch==MAP): bad.append(ch)
   else: todo.append(ch)
actors=E.get_all_level_actors()
bounds=actor.get_actor_bounds(False) if False else [list(mesh.get_bounding_box().min.to_tuple()),list(mesh.get_bounding_box().max.to_tuple())]
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map_reload':True,'map':MAP,'dependencies':deps,'visited_packages':len(seen),'foreign_game_dependencies':sorted(set(bad)),'actor_classes':[a.get_class().get_name() for a in actors],'mesh_bounds_cm':bounds,'collision':'CTF_USE_COMPLEX_AS_SIMPLE / BlockAll','player_start_cm':[-1900,-1150,120],'world_partition':False,'dynamic_lighting':True,'hello_class':'/Script/ForestDemo.ScreenDebugLogger'}
world=u.EditorLevelLibrary.get_editor_world()
traces={}
for name,x,y,z in [('entry',-1900,-1150,300),('ramp_mid',-1900,-600,300),('platform',-2200,400,300),('track_bed',1800,881,200)]:
 hit=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,z),u.Vector(x,y,-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],u.DrawDebugTrace.NONE)
 traces[name]={'blocking_hit':bool(hit and hit.to_tuple()[0]),'result':str(hit.to_tuple()) if hit else None}
report['ground_traces']=traces
report['validation_seconds']=time.perf_counter()-validation_started
json.dump(report,open(W+'/validation.json','w'),indent=2)
assert not bad,bad
print('MOUNTAIN_MEDIUM_BUILD_VALIDATED')

