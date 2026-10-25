import unreal,sys,json,traceback
from pathlib import Path
P=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra');sys.path.insert(0,str(P))
import materials,assemble,capture
try:
    assert assemble.LEV.load_level(assemble.MAP)
    reg=unreal.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous([assemble.ASSET],True)
    fixed=[]
    for data in reg.get_assets_by_path(assemble.ASSET+'/Materials',False):
        m=data.get_asset();visited=set();stack=[]
        for prop in (unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialProperty.MP_ROUGHNESS,unreal.MaterialProperty.MP_NORMAL,unreal.MaterialProperty.MP_EMISSIVE_COLOR,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET):
            n=unreal.MaterialEditingLibrary.get_material_property_input_node(m,prop)
            if n:stack.append(n)
        while stack:
            n=stack.pop()
            if n.get_path_name() in visited:continue
            visited.add(n.get_path_name())
            stack.extend(x for x in unreal.MaterialEditingLibrary.get_inputs_for_material_expression(m,n) if x)
            if isinstance(n,unreal.MaterialExpressionTextureSample):
                tex=n.get_editor_property('texture')
                if tex and tex.get_name().endswith('_Roughness'):
                    n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE);fixed.append(tex.get_name())
            if isinstance(n,unreal.MaterialExpressionCustom):
                code=n.get_editor_property('code')
                if 'float quay=' in code:n.set_editor_property('code',materials.PATH_MASK)
                elif 'float ring=' in code:n.set_editor_property('code',code.replace('(1-age)*.19','(1-age)*.28'))
        if m.get_name()=='M_OvercastSky':m.set_editor_property('is_sky',True)
        unreal.MaterialEditingLibrary.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
    actors={a.get_actor_label():a for a in assemble.ACT.get_all_level_actors()}
    sun=actors['OvercastSun'].get_component_by_class(unreal.DirectionalLightComponent);sun.set_editor_property('intensity',1.5);sun.set_editor_property('light_color',unreal.Color(r=223,g=230,b=238,a=255))
    sky=actors['OvercastSkyLight'].get_component_by_class(unreal.SkyLightComponent);sky.set_editor_property('intensity',2.6)
    fill=assemble.actor(unreal.DirectionalLight,'OvercastFill');fill.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=145,roll=0),False);fc=fill.get_component_by_class(unreal.DirectionalLightComponent);fc.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE);fc.set_editor_property('intensity',.7);fc.set_editor_property('cast_shadows',False);fc.set_editor_property('light_color',unreal.Color(r=219,g=228,b=238,a=255))
    for key,a in actors.items():
        if key.startswith('LampGlow_'):
            c=a.get_component_by_class(unreal.PointLightComponent);c.set_editor_property('light_color',unreal.Color(r=255,g=202,b=133,a=255));c.set_editor_property('intensity',65)
        if key.startswith('QuayCap_1_') and abs(a.get_actor_location().y+100)<320:assemble.ACT.destroy_actor(a)
    options=unreal.FbxImportUI();options.set_editor_property('import_mesh',True);options.set_editor_property('import_materials',False);options.set_editor_property('import_textures',False);options.set_editor_property('import_as_skeletal',False);options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.static_mesh_import_data.set_editor_property('combine_meshes',True);options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs',False);options.static_mesh_import_data.set_editor_property('auto_generate_collision',False);options.static_mesh_import_data.set_editor_property('transform_vertex_to_absolute',True)
    step=assemble.task(P/'Art/Landscape/FBX/SM_DockStep.fbx',assemble.ASSET+'/Meshes',options);step.set_material(0,unreal.load_asset(assemble.ASSET+'/Materials/M_Timber'));step.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);unreal.EditorAssetLibrary.save_loaded_asset(step)
    actors['DockStep'].set_actor_location(assemble.xyz(6.4,1,0),False,False)
    assemble.LEV.save_current_level();unreal.EditorAssetLibrary.save_directory(assemble.ASSET,only_if_is_dirty=False,recursive=True)
    (P/'Execution/polish_changes.json').write_text(json.dumps({'roughness_samplers_fixed':fixed,'sky_material_is_sky':True,'door_approaches':True,'dock_ramp_imported':True,'light':'warm lamps; sky2.6 + sun1.5 + fill0.7'},indent=2))
    capture.start('polish',True)
except Exception:
    (P/'Execution/polish_error.txt').write_text(traceback.format_exc());raise
