import unreal as u,json
l=u.get_editor_subsystem(u.LevelEditorSubsystem);l.load_level('/Game/Maps/medium')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
for a in actors:
 if isinstance(a,u.PostProcessVolume):
  s=a.settings
  s.set_editor_property('override_auto_exposure_method',True);s.set_editor_property('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL)
  s.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True);s.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
  s.set_editor_property('override_auto_exposure_bias',True);s.set_editor_property('auto_exposure_bias',0.0)
  a.settings=s
 if isinstance(a,u.DirectionalLight):
  a.set_actor_rotation(u.Rotator(pitch=-48,yaw=-32,roll=0),False);a.light_component.set_editor_property('intensity',6.0)
  u.log('MEDIUM SUN '+str(a.get_actor_rotation()))
l.save_current_level()
gm=u.load_asset('/Game/Forest/medium/Materials/M_Ground')
vc=u.MaterialEditingLibrary.create_material_expression(gm,u.MaterialExpressionVertexColor,-200,0)
assert u.MaterialEditingLibrary.connect_material_property(vc,'',u.MaterialProperty.MP_BASE_COLOR)
u.MaterialEditingLibrary.recompile_material(gm);u.EditorAssetLibrary.save_asset('/Game/Forest/medium/Materials/M_Ground')
es=u.get_editor_subsystem(u.EditorActorSubsystem)
fill=es.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,6000),u.Rotator(pitch=-35,yaw=145,roll=0));fill.set_actor_label('Soft opposing fill');fill.light_component.set_mobility(u.ComponentMobility.MOVABLE);fill.light_component.set_editor_property('intensity',1.8);fill.light_component.set_editor_property('cast_shadows',False)
l.save_current_level()

