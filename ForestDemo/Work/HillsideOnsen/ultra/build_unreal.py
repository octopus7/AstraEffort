"""Build ONLY the private HillsideOnsen scene, then render a first review image."""
import unreal as u, json, math, time, traceback
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra')
ROOT='/Game/HillsideOnsen/ultra'
MAP='/Game/Maps/HillsideOnsen_ultra'
M=json.loads((W/'scene_manifest.json').read_text())
AT=u.AssetToolsHelpers.get_asset_tools()
SS=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
AS=u.get_editor_subsystem(u.EditorActorSubsystem)
ML=u.MaterialEditingLibrary
STATE={}

def write(name,data):
    (W/name).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
def node(mat,cls,**props):
    o=ML.create_material_expression(mat,cls)
    for k,v in props.items():o.set_editor_property(k,v)
    return o
def val(mat,v):
    return node(mat,u.MaterialExpressionConstant,r=v)
def vec(mat,v):
    return node(mat,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*v,1))
def con(a,b,pin,output=''):
    names=[str(n) for n in ML.get_material_expression_input_names(b)]
    if pin not in names and len(names)==1:pin=names[0]
    assert ML.connect_material_expressions(a,output,b,pin),f'connect {a.get_name()}->{b.get_name()}:{pin}; available={names}'
def mul(mat,a,b):
    o=node(mat,u.MaterialExpressionMultiply);con(a,o,'A');con(b,o,'B');return o
def plus(mat,a,b):
    o=node(mat,u.MaterialExpressionAdd);con(a,o,'A');con(b,o,'B');return o
def prop(mat,a,p,output=''):
    assert ML.connect_material_property(a,output,p)
def material(name):
    old=u.load_asset(ROOT+'/Materials/'+name)
    if old:
        ML.delete_all_material_expressions(old);return old
    return AT.create_asset(name,ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
def sample(mat,tex,coords=None):
    o=node(mat,u.MaterialExpressionTextureSample,texture=tex)
    o.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR if tex.get_editor_property('srgb') else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    if coords:con(coords,o,'UVs')
    return o
def import_texture(name,path,srgb):
    task=u.AssetImportTask();task.set_editor_property('filename',str(path));task.set_editor_property('destination_path',ROOT+'/Textures')
    task.set_editor_property('destination_name',name);task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True);task.set_editor_property('save',True)
    AT.import_asset_tasks([task]);tex=u.load_asset(ROOT+'/Textures/'+name);assert tex
    tex.set_editor_property('srgb',srgb)
    if 'Steam' in name:
        tex.set_editor_property('address_x',u.TextureAddress.TA_CLAMP);tex.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
    u.EditorAssetLibrary.save_loaded_asset(tex)
    return tex

def make_surface(meta,textures):
    cat=meta['category'];mat=material('M_'+cat)
    mat.set_editor_property('two_sided',cat in ['Fabric','Leaves','LeavesLight','Water','Stream','Steam'])
    if cat=='Steam':
        mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
        uv=node(mat,u.MaterialExpressionTextureCoordinate)
        tex=sample(mat,textures['T_Steam_Opacity'],uv)
        tm=node(mat,u.MaterialExpressionTime);s=node(mat,u.MaterialExpressionSine,period=18.0);con(tm,s,'Input')
        fade=node(mat,u.MaterialExpressionDepthFade,fade_distance_default=60.0)
        opacity=mul(mat,tex,val(mat,.12));# use mask alpha explicitly below
        con(tex,opacity,'A','A')
        pulse=plus(mat,val(mat,.72),mul(mat,s,val(mat,.20)))
        con(mul(mat,opacity,pulse),fade,'Opacity')
        prop(mat,fade,u.MaterialProperty.MP_OPACITY)
        prop(mat,vec(mat,(.69,.76,.72)),u.MaterialProperty.MP_EMISSIVE_COLOR)
        prop(mat,mul(mat,s,vec(mat,(9,3,18))),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    elif cat in ['Water','Stream']:
        uv=node(mat,u.MaterialExpressionTextureCoordinate)
        scale=meta['uv']['atlas_pixels']/512
        uv.set_editor_property('u_tiling',scale);uv.set_editor_property('v_tiling',scale)
        pan=node(mat,u.MaterialExpressionPanner,speed_x=.012,speed_y=-.018);con(uv,pan,'Coordinate')
        tex=sample(mat,textures['T_Water_Ripples'],pan)
        tint=vec(mat,tuple(meta['color']));base=mul(mat,tint,plus(mat,val(mat,.82),mul(mat,tex,val(mat,.25))))
        prop(mat,base,u.MaterialProperty.MP_BASE_COLOR)
        prop(mat,val(mat,.19),u.MaterialProperty.MP_ROUGHNESS);prop(mat,val(mat,.12),u.MaterialProperty.MP_METALLIC)
        prop(mat,val(mat,.65),u.MaterialProperty.MP_SPECULAR)
        tm=node(mat,u.MaterialExpressionTime);wave=node(mat,u.MaterialExpressionSine,period=5.8);con(tm,wave,'Input')
        prop(mat,mul(mat,wave,vec(mat,(0,0,1.5))),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        # Small moving world-space normals from two independently panned detail channels.
        pan2=node(mat,u.MaterialExpressionPanner,speed_x=-.016,speed_y=.009);con(uv,pan2,'Coordinate')
        tex2=sample(mat,textures['T_Water_Ripples'],pan2)
        x=node(mat,u.MaterialExpressionComponentMask,r=True,g=False,b=False,a=False);con(tex,x,'Input')
        y=node(mat,u.MaterialExpressionComponentMask,r=True,g=False,b=False,a=False);con(tex2,y,'Input')
        xx=mul(mat,plus(mat,x,val(mat,-.5)),val(mat,.14));yy=mul(mat,plus(mat,y,val(mat,-.5)),val(mat,.14))
        xy=node(mat,u.MaterialExpressionAppendVector);con(xx,xy,'A');con(yy,xy,'B')
        xyz=node(mat,u.MaterialExpressionAppendVector);con(xy,xyz,'A');con(val(mat,1),xyz,'B')
        mat.set_editor_property('tangent_space_normal',False);prop(mat,xyz,u.MaterialProperty.MP_NORMAL)
    else:
        key='T_'+meta['texture'].capitalize()+'_BaseColor';tex=textures[key]
        uv=node(mat,u.MaterialExpressionTextureCoordinate)
        scale=meta['uv']['uv_to_texture_scale'];uv.set_editor_property('u_tiling',scale);uv.set_editor_property('v_tiling',scale)
        ts=sample(mat,tex,uv)
        lerp=node(mat,u.MaterialExpressionLinearInterpolate,const_alpha=.28)
        con(vec(mat,tuple(meta['color'])),lerp,'A');con(ts,lerp,'B')
        prop(mat,lerp,u.MaterialProperty.MP_BASE_COLOR)
        prop(mat,val(mat,.87 if cat in ['Terrain','Path','Stone','BathStone','Earth'] else .69),u.MaterialProperty.MP_ROUGHNESS)
        if cat=='Metal':prop(mat,val(mat,.65),u.MaterialProperty.MP_METALLIC)
        if cat=='Glass':prop(mat,mul(mat,vec(mat,(.73,.48,.20)),val(mat,.35)),u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

def mesh_import(meta,mat):
    task=u.AssetImportTask();task.set_editor_property('filename',meta['fbx']);task.set_editor_property('destination_path',ROOT+'/Meshes')
    task.set_editor_property('destination_name',meta['name']);task.set_editor_property('automated',True);task.set_editor_property('save',True)
    task.set_editor_property('replace_existing',True);task.set_editor_property('factory',u.FbxFactory())
    opts=u.FbxImportUI();opts.set_editor_property('import_mesh',True);opts.set_editor_property('import_as_skeletal',False)
    opts.set_editor_property('automated_import_should_detect_type',False);opts.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
    opts.set_editor_property('import_materials',False);opts.set_editor_property('import_textures',False)
    data=opts.get_editor_property('static_mesh_import_data');data.set_editor_property('combine_meshes',True)
    data.set_editor_property('convert_scene',False);data.set_editor_property('convert_scene_unit',True)
    data.set_editor_property('generate_lightmap_u_vs',False);data.set_editor_property('auto_generate_collision',False)
    data.set_editor_property('vertex_color_import_option',u.VertexColorImportOption.REPLACE)
    task.set_editor_property('options',opts);AT.import_asset_tasks([task])
    sm=u.load_asset(ROOT+'/Meshes/'+meta['name']);assert sm,meta['name']
    sm.set_material(0,mat)
    settings=SS.get_lod_build_settings(sm,0);settings.set_editor_property('use_full_precision_u_vs',True);settings.set_editor_property('generate_lightmap_u_vs',False)
    SS.set_lod_build_settings(sm,0,settings)
    body=sm.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    for section in range(sm.get_num_sections(0)):SS.enable_section_collision(sm,meta['collision'],0,section)
    u.EditorAssetLibrary.save_loaded_asset(sm)
    return sm

def spawn(cls,label,loc=(0,0,0),rot=(0,0,0)):
    actor=AS.spawn_actor_from_class(cls,u.Vector(*loc),u.Rotator(*rot));assert actor,label;actor.set_actor_label(label);return actor

def main():
    project=u.Paths.get_project_file_path().replace('\\','/')
    assert '/Saved/Workers/HillsideOnsen/ultra/' in project,project
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
    textures={}
    tm=json.loads((W/'texture_manifest.json').read_text())
    for name,data in tm['assets'].items():textures[name]=import_texture(name,data['path'],data['unreal_srgb'])
    evidence=[]
    for meta in M['meshes']:
        mat=make_surface(meta,textures);sm=mesh_import(meta,mat)
        actor=spawn(u.StaticMeshActor,'Onsen_'+meta['category']);comp=actor.static_mesh_component;comp.set_static_mesh(sm)
        actor.set_actor_scale3d(u.Vector(1,-1,1))
        comp.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if meta['collision'] else u.CollisionEnabled.NO_COLLISION)
        comp.set_collision_profile_name('BlockAll' if meta['collision'] else 'NoCollision')
        if meta['category'] in ['Steam','Glass','Water','Stream']:comp.set_cast_shadow(False)
        bounds=actor.get_actor_bounds(False)
        evidence.append({'mesh':meta['name'],'bounds_origin_cm':list(bounds[0].to_tuple()),'bounds_extent_cm':list(bounds[1].to_tuple()),'collision':meta['collision']})
    sun=spawn(u.DirectionalLight,'Late afternoon sun',rot=(-42,-35,0));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sun.light_component.set_intensity(4.5);sun.light_component.set_light_color(u.LinearColor(1,.91,.76,1))
    sun.light_component.set_editor_property('light_source_angle',4.0)
    sky=spawn(u.SkyLight,'Soft sky fill');sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_intensity(1.15)
    sky.light_component.set_editor_property('sky_distance_threshold',10000.0)
    sky.light_component.set_editor_property('real_time_capture',True)
    # Own unlit sky material on a read-only Engine sphere; no cross-theme resources.
    skymat=material('M_Sky');skymat.set_editor_property('two_sided',True);skymat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    skymat.set_editor_property('is_sky',True)
    prop(skymat,vec(skymat,(.36,.49,.57)),u.MaterialProperty.MP_EMISSIVE_COLOR);ML.recompile_material(skymat);u.EditorAssetLibrary.save_loaded_asset(skymat)
    dome=spawn(u.StaticMeshActor,'Muted sky backdrop',(0,0,0));dome.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere.Sphere'))
    dome.set_actor_scale3d(u.Vector(600,600,600));dome.static_mesh_component.set_material(0,skymat);dome.static_mesh_component.set_cast_shadow(False);dome.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    sky.light_component.recapture_sky()
    for obj in M['semantic_objects']:
        if obj['type']=='lamp':
            lamp=spawn(u.PointLight,'Warm lantern',tuple(v*100 for v in obj['position']));lamp.light_component.set_mobility(u.ComponentMobility.MOVABLE)
            lamp.light_component.set_intensity(12);lamp.light_component.set_light_color(u.LinearColor(1,.64,.30,1));lamp.light_component.set_editor_property('attenuation_radius',230)
    start=spawn(u.PlayerStart,'Arrival PlayerStart',(0,-4400,360),rot=(0,155,0))
    pp=spawn(u.PostProcessVolume,'Manual exposure');pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings');settings.set_editor_property('override_auto_exposure_method',True);settings.set_editor_property('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL)
    settings.set_editor_property('override_auto_exposure_bias',True);settings.set_editor_property('auto_exposure_bias',0.0)
    settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True);settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
    settings.set_editor_property('override_motion_blur_amount',True);settings.set_editor_property('motion_blur_amount',0.0)
    pp.set_editor_property('settings',settings)
    assert world.get_world_settings().get_editor_property('world_partition') is None
    assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
    u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    write('build_evidence.json',{'utc':datetime.now(timezone.utc).isoformat(),'project':project,'map':MAP,'meshes':evidence,'non_world_partition':True,'saved':True})
    # Preview: transient capture actor is created only after the saved map is written.
    cap=spawn(u.SceneCapture2D,'Transient preview');comp=cap.get_component_by_class(u.SceneCaptureComponent2D)
    target=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8)
    comp.set_editor_property('texture_target',target);comp.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    comp.set_editor_property('capture_every_frame',True);comp.set_editor_property('always_persist_rendering_state',True)
    comp.set_editor_property('post_process_settings',settings)
    cam=M['camera_views']['overview'];pos=u.Vector(*(x*100 for x in cam['location']));aim=u.Vector(*(x*100 for x in cam['target']))
    cap.set_actor_location(pos,False,False);cap.set_actor_rotation(u.MathLibrary.find_look_at_rotation(pos,aim),False)
    comp.set_editor_property('fov_angle',cam['fov']);comp.capture_scene()
    STATE.update(world=world,cap=cap,comp=comp,target=target,started=time.monotonic())
    def tick(dt):
        try:
            if time.monotonic()-STATE['started']<40:return
            comp.capture_scene();u.RenderingLibrary.export_render_target(world,target,str(W/'Screenshots'),'preview.png')
            write('preview_capture.json',{'utc':datetime.now(timezone.utc).isoformat(),'camera':cam,'size':[1920,1080]})
            u.unregister_slate_post_tick_callback(STATE['handle']);u.SystemLibrary.quit_editor()
        except Exception:
            write('build_error.json',{'traceback':traceback.format_exc()});u.unregister_slate_post_tick_callback(STATE['handle']);u.SystemLibrary.quit_editor()
    STATE['handle']=u.register_slate_post_tick_callback(tick)
    u.EditorPythonScripting.set_keep_python_script_alive(True)

try:main()
except Exception:
    write('build_error.json',{'utc':datetime.now(timezone.utc).isoformat(),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
