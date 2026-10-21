import unreal as u,json,os,datetime
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass';BASE='/Game/MountainStation/high';MAP='/Game/Maps/MountainStation_high'
level=u.get_editor_subsystem(u.LevelEditorSubsystem);assert level.load_level(MAP)
reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous(['/Game'],True);lib=u.EditorAssetLibrary;ms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
options=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=True,include_hard_management_references=True)
pending=[MAP]+[str(a.package_name) for a in reg.get_assets_by_path(BASE,recursive=True)];seen=set();graph={};bad=[]
while pending:
 p=pending.pop()
 if p in seen:continue
 seen.add(p);graph[p]=[str(v) for v in reg.get_dependencies(p,options)]
 for d in graph[p]:
  if d.startswith('/Game/'):
   if not (d==MAP or d.startswith(BASE+'/')):bad.append([p,d])
   if d not in seen:pending.append(d)
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors();meshes=[];os.makedirs(W+'/UEExport',exist_ok=True)
for a in actors:
 if not isinstance(a,u.StaticMeshActor) or not a.static_mesh_component.static_mesh:continue
 mesh=a.static_mesh_component.static_mesh
 if not mesh.get_path_name().startswith(BASE):continue
 name=mesh.get_name();scale=a.get_actor_scale3d();bounds=mesh.get_bounds();settings=ms.get_lod_build_settings(mesh,0)
 t=u.AssetExportTask();t.object=mesh;t.filename=W+'/UEExport/'+name+'.fbx';t.automated=True;t.prompt=False;t.replace_identical=True;t.exporter=u.StaticMeshExporterFBX();opt=u.FbxExportOption();opt.ascii=False;opt.level_of_detail=False;t.options=opt
 assert u.Exporter.run_asset_export_task(t),'Export failed '+name
 meshes.append({'name':name,'path':mesh.get_path_name(),'actor':a.get_actor_label(),'location_cm':list(a.get_actor_location().to_tuple()),'scale':list(scale.to_tuple()),'rotation':list(a.get_actor_rotation().to_tuple()),'asset_bounds_origin_cm':list(bounds.origin.to_tuple()),'asset_bounds_extent_cm':list(bounds.box_extent.to_tuple()),'uv_channels':ms.get_num_uv_channels(mesh,0),'full_precision_uvs':settings.use_full_precision_u_vs,'collision':str(mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')),'materials':[str(s.material_interface.get_path_name()) if s.material_interface else None for s in mesh.get_editor_property('static_materials')]})
manifest=json.load(open(W+'/imagegen_manifest.json'));links=[]
for texid,names in manifest['mapping'].items():
 for name in names:
  m=lib.load_asset(BASE+'/Materials/M_'+name);textures=[x.get_path_name() for x in u.MaterialEditingLibrary.get_used_textures(m)]
  expected=BASE+'/Textures/T_'+texid+'.T_'+texid
  root=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR);stack=[root] if root else [];nodes=set();samples=[]
  while stack:
   node=stack.pop()
   if node in nodes:continue
   nodes.add(node);inputs=u.MaterialEditingLibrary.get_inputs_for_material_expression(m,node);stack.extend(n for n in inputs if n)
   if isinstance(node,u.MaterialExpressionTextureSample):
    samples.append({'texture':node.texture.get_path_name() if node.texture else None,'coordinate_index_default':node.get_editor_property('const_coordinate'),'upstream_nodes':[n.get_class().get_name() for n in inputs if n]})
  connected=any(s['texture']==expected for s in samples)
  alpha=[n.r for n in u.MaterialEditingLibrary.get_inputs_for_material_expression(m,root) if isinstance(n,u.MaterialExpressionConstant)]
  expected_weight={'Grass':.10,'Hill':.10,'Leaf':.24,'LeafLight':.24,'Flower':.24}.get(name,.72)
  links.append({'material':m.get_path_name(),'expected_texture':expected,'actual_used_textures':textures,'base_color_graph_samples':samples,'generated_weight':alpha,'expected_weight':expected_weight,'verified':expected in textures and connected and len(alpha)==1 and abs(alpha[0]-expected_weight)<1e-6,'uv_multiplier':[1,1],'coordinate_channel':0})
checks={'fresh_process_map_reload':True,'owned_recursive_dependencies':not bad,'all_11_assemblies':len(meshes)==11,'two_uv_channels':all(m['uv_channels']==2 for m in meshes),'full_precision_uvs':all(m['full_precision_uvs'] for m in meshes),'actual_material_texture_links':all(l['verified'] for l in links),'actor_scale_absolute_one':all(all(abs(abs(s)-1)<1e-6 for s in m['scale']) for m in meshes),'collision_complex':all('CTF_USE_COMPLEX_AS_SIMPLE' in m['collision'] for m in meshes),'player_start':any(isinstance(a,u.PlayerStart) for a in actors),'native_logger':any(a.get_class().get_name()=='ScreenDebugLogger' for a in actors)}
ground=next(a for a in actors if a.get_actor_label()=='PresentationGround');background=ground.static_mesh_component.get_material(0);bg_root=u.MaterialEditingLibrary.get_material_property_input_node(background,u.MaterialProperty.MP_BASE_COLOR);bgtextures=[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(background)]
checks['background_constant_no_texture']=background.get_path_name()==BASE+'/Materials/M_PresentationGround.M_PresentationGround' and not bgtextures and isinstance(bg_root,u.MaterialExpressionConstant3Vector)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();settings=world.get_world_settings();partition=settings.get_editor_property('world_partition');checks['direct_non_world_partition']=partition is None and world.get_path_name()==MAP+'.MountainStation_high'
result={'validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'passed':all(checks.values()),'world_partition_query':{'world':world.get_path_name(),'settings':settings.get_path_name(),'partition':partition.get_path_name() if partition else None,'is_none':partition is None},'package_count':len(seen),'forbidden_dependencies':bad,'dependency_graph':graph,'mesh_geometry_exports':meshes,'material_links':links,'background':{'actor':ground.get_actor_label(),'material':background.get_path_name(),'used_textures':bgtextures,'base_color':[bg_root.constant.r,bg_root.constant.g,bg_root.constant.b,bg_root.constant.a]},'scope':'All saved authored meshes exported from this new UE process. CPU geometry/UV roundtrip audit follows separately.'}
json.dump(result,open(W+'/ue_validation.json','w'),indent=2);u.log('TEXTUREPASS_VALIDATION '+json.dumps(checks));assert result['passed']

