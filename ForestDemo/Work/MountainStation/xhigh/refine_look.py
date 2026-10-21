import unreal as u,json
from pathlib import Path
work=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh');root='/Game/MountainStation/xhigh'
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
task=u.AssetImportTask();task.filename=str(work/'SourceArt/Tunnel.fbx');task.destination_path=root+'/Meshes';task.destination_name='SM_Tunnel';task.automated=True;task.replace_existing=True;task.save=True
opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
data=opt.static_mesh_import_data;data.combine_meshes=True;data.auto_generate_collision=False;data.generate_lightmap_u_vs=False;data.convert_scene=True;data.convert_scene_unit=True;task.options=opt
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);mesh=u.load_asset(root+'/Meshes/SM_Tunnel')
for i,slot in enumerate(mesh.static_materials):mesh.set_material(i,u.load_asset(root+'/Materials/M_'+str(slot.material_slot_name).split('.')[0]))
body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True);u.EditorAssetLibrary.save_loaded_asset(mesh)
u.EditorLevelLibrary.load_level('/Game/Maps/MountainStation_xhigh');sub=u.get_editor_subsystem(u.EditorActorSubsystem);actors=sub.get_all_level_actors()
sun=next(a for a in actors if a.get_actor_label()=='Sun_Afternoon');sun.modify();sun.set_actor_rotation(u.Rotator(pitch=-45,yaw=135,roll=0),False);sun.light_component.set_intensity(4.0);sun.light_component.set_editor_property('light_source_angle',2.0)
fill=next((a for a in actors if a.get_actor_label()=='Sky_BroadFill'),None) or sub.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,7000),u.Rotator(pitch=-35,yaw=-45,roll=0))
fill.set_actor_rotation(u.Rotator(pitch=-35,yaw=-45,roll=0),False)
fill.set_actor_label('Sky_BroadFill');fill.light_component.set_mobility(u.ComponentMobility.MOVABLE);fill.light_component.set_intensity(1.1);fill.light_component.set_light_color(u.LinearColor(.79,.88,1,1));fill.light_component.set_cast_shadows(False)
sky=next(a for a in actors if isinstance(a,u.SkyLight));sky.light_component.set_intensity(1.4);sky.light_component.recapture_sky()
u.EditorLevelLibrary.save_current_level()
(work/'Evidence/lighting_refinement.json').write_text(json.dumps({'sun_intensity':4.0,'sun_rotation_pitch_yaw_roll':[-45,135,0],'fill_intensity':1.1,'fill_shadows':False,'sky_intensity':1.4,'sky_recapture_requested':True,'reason':'Actual first UE render had underlit station facade and insufficient shadow fill.'},indent=2))
