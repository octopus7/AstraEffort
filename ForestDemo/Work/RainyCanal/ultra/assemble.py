import unreal,json,math,random
from pathlib import Path
from datetime import datetime,timezone
from design import BUILDINGS,BRIDGES,PUDDLES,path_distance,building_clear,WATER_Z
import materials
ROOT=Path(__file__).resolve().parent
ASSET='/Game/RainyCanal/ultra'
MAP='/Game/Maps/RainyCanal_ultra'
ACT=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEV=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
SM=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
random.seed(171023)
def task(path,dest,options=None):
    t=unreal.AssetImportTask();t.set_editor_property('filename',str(path));t.set_editor_property('destination_path',dest);t.set_editor_property('destination_name',path.stem);t.set_editor_property('automated',True);t.set_editor_property('replace_existing',True);t.set_editor_property('save',True)
    if options:t.set_editor_property('options',options)
    TOOLS.import_asset_tasks([t]);paths=t.get_editor_property('imported_object_paths');assert paths,(path,'import failed');return unreal.load_asset(paths[0])
def xyz(x,y,z):return unreal.Vector(x*100,-y*100,z*100)
def actor(cls,label,x=0,y=0,z=0,yaw=0):
    a=ACT.spawn_actor_from_class(cls,xyz(x,y,z),unreal.Rotator(pitch=0,yaw=-yaw,roll=0));a.set_actor_label(label);return a
def spawn(mesh,label,x=0,y=0,z=0,yaw=0,scale=(1,1,1),collision=True):
    a=actor(unreal.StaticMeshActor,label,x,y,z,yaw);c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_editor_property('mobility',unreal.ComponentMobility.STATIC);a.set_actor_scale3d(unreal.Vector(*scale));c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    if not collision:c.set_editor_property('cast_shadow',False)
    return a
def build():
    assert '/Saved/Workers/RainyCanal/ultra/Project/' in unreal.Paths.get_project_file_path().replace('\\','/')
    textures={}
    for f in sorted((ROOT/'Art/Textures').glob('T_*.png')):
        tex=task(f,ASSET+'/Textures');name=f.stem
        if name.endswith('_Normal'):
            tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif name.endswith('_Roughness'):
            tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_GRAYSCALE)
        else:tex.set_editor_property('srgb',True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex);textures[name]=tex
    assert len(textures)==30,len(textures)
    mats=materials.build(textures)
    meshes={};meshrows=[]
    files=sorted((ROOT/'Art').glob('*/FBX/*.fbx'))+sorted((ROOT/'Art/Architecture').glob('*.fbx'))
    assert len(files)>=24,('missing sources',len(files))
    for f in files:
        options=unreal.FbxImportUI();options.set_editor_property('import_mesh',True);options.set_editor_property('import_materials',False);options.set_editor_property('import_textures',False);options.set_editor_property('import_as_skeletal',False);options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
        data=options.static_mesh_import_data;data.set_editor_property('combine_meshes',True);data.set_editor_property('generate_lightmap_u_vs',False);data.set_editor_property('auto_generate_collision',False);data.set_editor_property('vertex_color_import_option',unreal.VertexColorImportOption.REPLACE);data.set_editor_property('transform_vertex_to_absolute',True)
        mesh=task(f,ASSET+'/Meshes',options)
        slots=mesh.get_editor_property('static_materials')
        for i,s in enumerate(slots):
            slot=str(s.get_editor_property('material_slot_name'));assert slot in mats,(f.name,slot)
            mesh.set_material(i,mats[slot])
        if f.stem not in ('SM_CanalWater','SM_Puddle','SM_RainVolume','SM_GrassFringe','SM_Shrub'):
            body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        if f.stem=='SM_RainVolume':
            mesh.set_editor_property('positive_bounds_extension',unreal.Vector(100,100,1450));mesh.set_editor_property('negative_bounds_extension',unreal.Vector(100,100,10))
        unreal.EditorAssetLibrary.save_loaded_asset(mesh);meshes[f.stem]=mesh
        meshrows.append({'mesh':f.stem,'materials':[str(s.material_slot_name) for s in slots],'uv_channels':SM.get_num_uv_channels(mesh,0),'bounds':str(mesh.get_bounding_box())})
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        assert LEV.load_level(MAP)
        for old in ACT.get_all_level_actors():
            if not isinstance(old,(unreal.WorldSettings,unreal.Brush)):ACT.destroy_actor(old)
    else:assert LEV.new_level(MAP,False)
    for name in ['SM_BankWest','SM_BankEast','SM_CanalBed']:spawn(meshes[name],name)
    water=spawn(meshes['SM_CanalWater'],'CanalWater',z=WATER_Z,collision=False)
    for x in (-6.05,6.05):spawn(meshes['SM_QuayWall'],f'QuayWall_{x}',x=x)
    for side in (-1,1):
        for j in range(50):
            y=-49+j*2
            if any(abs(y-by)<2 for _,_,by in BRIDGES) or (side==1 and abs(y-1)<3.2):continue
            spawn(meshes['SM_QuayCap'],f'QuayCap_{side}_{j}',x=side*6.05,y=y)
    for name,x,y in BRIDGES:spawn(meshes[name],name,x,y)
    for i,(name,x,y,yaw) in enumerate(BUILDINGS):spawn(meshes[name],f'Building_{i}_{name}',x,y,0,yaw)
    for i,(x,y,sx,sy) in enumerate(PUDDLES):spawn(meshes['SM_Puddle'],f'Puddle_{i}',x,y,.015,yaw=random.uniform(-15,15),scale=(sx,sy,1),collision=False)
    rain=spawn(meshes['SM_RainVolume'],'RainVolume',collision=False);rain.static_mesh_component.set_editor_property('translucency_sort_priority',10)
    # Railings leave both bridge landings and a dock opening unobstructed.
    railing_count=0
    for side in (-1,1):
        for y in range(-47,49,4):
            if any(abs(y-by)<3.8 for _,_,by in BRIDGES) or (side==1 and abs(y-1)<4):continue
            spawn(meshes['SM_RailingSegment'],f'Railing_{side}_{y}',side*6.4,y,.12,90);railing_count+=1
    # Dock deck is at -0.30m and connects across the quay wall with the final timber ramp.
    spawn(meshes['SM_Dock'],'Dock',4.4,1,-.3)
    spawn(meshes['SM_DockStep'],'DockStep',6.4,1,0)
    spawn(meshes['SM_Boat'],'MooredBoat',1.5,1,WATER_Z,90,collision=False)
    for i,(x,y) in enumerate([(6.2,-1.2),(6.2,3.2),(-6.7,7),(-6.7,20),(6.7,-24)]):spawn(meshes['SM_MooringBollard'],f'Bollard_{i}',x,y,.1)
    for side in (-1,1):
        for j,y in enumerate((-40,-25,-3,15,39)):
            x=side*8.0;spawn(meshes['SM_CanalLamp'],f'CanalLamp_{side}_{j}',x,y,.02)
            lamp=actor(unreal.PointLight,f'LampGlow_{side}_{j}',x,y,3.19);c=lamp.point_light_component;c.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE);c.set_editor_property('intensity',65);c.set_editor_property('attenuation_radius',600);c.set_editor_property('light_color',unreal.Color(r=255,g=202,b=133,a=255));c.set_editor_property('cast_shadows',False)
        for j,y in enumerate((-31,5,33)):
            spawn(meshes['SM_Bench'],f'Bench_{side}_{j}',side*13,y,0,90 if side<0 else -90)
            spawn(meshes['SM_Planter'],f'Planter_{side}_{j}',side*13,y+2.8,0)
    treepoints=[(-42,-38),(-37,-27),(-41,-5),(-37,7),(-43,20),(-39,39),(39,-40),(42,-25),(38,-3),(42,8),(37,20),(42,41),(-29,46),(29,46),(-29,-46),(29,-46)]
    for i,(x,y) in enumerate(treepoints):
        s=random.uniform(.93,1.35);spawn(meshes['SM_CanalTree'],f'Tree_{i}',x,y,0,random.uniform(0,360),(s,s,s))
    shrubs=grass=0
    for i in range(700):
        x=random.uniform(-48,48);y=random.uniform(-48,48)
        if abs(x)<15.1 or not building_clear(x,y,1.6):continue
        d=path_distance(x,y)
        if .2<d<1.7:
            s=random.uniform(.65,1.2);spawn(meshes['SM_GrassFringe'],f'GrassFringe_{grass}',x,y,.005,random.uniform(0,360),(s,s,s),False);grass+=1
        elif d>2.5 and random.random()<.22:
            s=random.uniform(.8,1.3);spawn(meshes['SM_Shrub'],f'Shrub_{shrubs}',x,y,0,random.uniform(0,360),(s,s,s),False);shrubs+=1
    sun=actor(unreal.DirectionalLight,'OvercastSun');sun.set_actor_rotation(unreal.Rotator(pitch=-48,yaw=-35,roll=0),False);dc=sun.get_component_by_class(unreal.DirectionalLightComponent);dc.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE);dc.set_editor_property('intensity',1.5);dc.set_editor_property('light_source_angle',12.0);dc.set_editor_property('light_color',unreal.Color(r=223,g=230,b=238,a=255))
    fill=actor(unreal.DirectionalLight,'OvercastFill');fill.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=145,roll=0),False);fc=fill.get_component_by_class(unreal.DirectionalLightComponent);fc.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE);fc.set_editor_property('intensity',.3);fc.set_editor_property('cast_shadows',False);fc.set_editor_property('light_color',unreal.Color(r=219,g=228,b=238,a=255))
    sky_mat=materials.create('OvercastSky',two=True,unlit=True);sky_mat.set_editor_property('is_sky',True);materials.prop(materials.color(sky_mat,(.19,.235,.26)),unreal.MaterialProperty.MP_EMISSIVE_COLOR);materials.save(sky_mat)
    sphere=spawn(unreal.load_asset('/Engine/BasicShapes/Sphere'),'OvercastSkySphere',scale=(450,450,450),collision=False);sphere.static_mesh_component.set_material(0,sky_mat)
    sky=actor(unreal.SkyLight,'OvercastSkyLight');sc=sky.get_component_by_class(unreal.SkyLightComponent);sc.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE);sc.set_editor_property('intensity',1.2);sc.set_editor_property('real_time_capture',True);sc.set_editor_property('lower_hemisphere_is_black',False)
    fog=actor(unreal.ExponentialHeightFog,'RainHaze',z=-6);fc=fog.get_component_by_class(unreal.ExponentialHeightFogComponent);fc.set_editor_property('fog_density',.0025);fc.set_editor_property('fog_height_falloff',.18);fc.set_fog_inscattering_color(unreal.LinearColor(.27,.33,.36,1))
    pp=actor(unreal.PostProcessVolume,'OvercastExposure');pp.set_editor_property('unbound',True);settings=pp.get_editor_property('settings');settings.set_editor_property('override_auto_exposure_min_brightness',True);settings.set_editor_property('override_auto_exposure_max_brightness',True);settings.set_editor_property('auto_exposure_min_brightness',1.0);settings.set_editor_property('auto_exposure_max_brightness',1.0);pp.set_editor_property('settings',settings)
    settings.set_editor_property('override_ambient_occlusion_intensity',True);settings.set_editor_property('ambient_occlusion_intensity',.85);settings.set_editor_property('override_ambient_occlusion_radius',True);settings.set_editor_property('ambient_occlusion_radius',100);pp.set_editor_property('settings',settings)
    actor(unreal.PlayerStart,'CanalPlayerStart',-10,-21,1.2,90)
    assert LEV.save_current_level()
    unreal.EditorAssetLibrary.save_directory(ASSET,only_if_is_dirty=False,recursive=True)
    info={'utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'meshes':meshrows,'counts':{'buildings':len(BUILDINGS),'bridges':len(BRIDGES),'puddles':len(PUDDLES),'lamps':10,'trees':len(treepoints),'grass_fringe':grass,'shrubs':shrubs,'railings':railing_count},'design_buildings':BUILDINGS,'design_bridges':BRIDGES,'water_z_m':WATER_Z,'actor_count':len(ACT.get_all_level_actors()),'source':'All RainyCanal originals; Engine sphere only for overcast sky'}
    (ROOT/'assembly.json').write_text(json.dumps(info,indent=2));return info
