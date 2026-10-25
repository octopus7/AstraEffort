from ue_common import *
import random

def run():
    assert 'Saved/Workers/WindmillFarm/ultra/Project' in u.Paths.project_dir().replace('\\','/')
    if u.EditorAssetLibrary.does_asset_exist(MAP):
        assert levels.load_level(MAP)
        for a in actors.get_all_level_actors():
            if not isinstance(a,u.WorldSettings):actors.destroy_actor(a)
    else:assert levels.new_level(MAP,False)
    world=u.UnrealEditorSubsystem().get_editor_world() if False else u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    ws=world.get_world_settings();ws.set_editor_property('force_no_precomputed_lighting',True);ws.set_editor_property('default_game_mode',u.GameModeBase)
    static('SM_Ground','FarmGround',z=0);static('SM_EarthEdge','EarthEdge',z=0)
    static('SM_MillTower','WindmillTower',*MILL)
    static('SM_MillRotor','WindmillSails',MILL[0],MILL[1]-3.95,height(*MILL)+9.2,collide=False)
    if u.EditorAssetLibrary.does_asset_exist(BASE+'/Meshes/SM_MillSteps'):static('SM_MillSteps','MillEntranceSteps',*MILL)
    static('SM_Barn','FarmBarn',*BARN)
    static('SM_Shed','ToolShed',*SHED,yaw=-90)
    static('SM_Cart','ProduceCart',15,2,yaw=-24)
    static('SM_ToolCluster','ToolsByBarn',19.0,11.6,yaw=8)
    static('SM_Barrel','RainBarrel',28.7,13.4)
    static('SM_Barrel','MillGrainBarrel',-9.8,11.0)
    lower_a=static('SM_HayBale','StackedHayA',18.0,22.0)
    lower_b=static('SM_HayBale','StackedHayB',19.25,22.0)
    bale_bounds=u.load_asset(BASE+'/Meshes/SM_HayBale').get_bounding_box()
    supported_z=max(a.get_actor_location().z+bale_bounds.max.z for a in (lower_a,lower_b))
    static('SM_HayBale','StackedHayTop',18.625,22.0,z=(supported_z-bale_bounds.min.z)/100)
    random.seed(4503)
    tree_positions=[(-43,32),(-31,36),(-19,39),(-6,38),(8,38),(21,38),(35,35),(44,27),
                    (-44,15),(-42,-1),(-45,-21),(-41,-41),(40,-35),(43,-18),(43,10),
                    (3,26),(11,28),(20,27),(-25,20),(-33,25)]
    for i,(x,y) in enumerate(tree_positions):static('SM_OrchardTree'+str(i%3+1),'OrchardTree_%02d'%i,x,y,yaw=random.uniform(0,360),scale=random.uniform(.85,1.2))
    # Fences around crop edges with deliberately open approaches.
    count=0
    for fi,f in enumerate(FIELDS):
        cx,cy=f['center'];sx,sy=f['size'];xmin,xmax=cx-sx/2-.8,cx+sx/2+.8;ymin,ymax=cy-sy/2-.8,cy+sy/2+.8
        for side,y in [('south',ymin),('north',ymax)]:
            n=round((xmax-xmin)/3)
            for k in range(n):
                x=xmin+1.5+k*3
                if side=='north' and abs(x-cx)<2.2:continue
                static('SM_FenceSegment','FieldFence_%03d'%count,x,y,yaw=random.uniform(-2,2));count+=1
        for x in (xmin,xmax):
            for k in range(round((ymax-ymin)/3)):
                y=ymin+1.5+k*3
                if path_distance(x,y)<.4:continue
                static('SM_FenceSegment','FieldFence_%03d'%count,x,y,yaw=90+random.uniform(-2,2));count+=1
        # Plants occupy inner beds, leaving a working margin inside each fence.
        for ix in range(int(sx-2)):
            for iy in range(int((sy-2)/1.1)):
                x=cx-sx/2+1.2+ix;y=cy-sy/2+1.2+iy*1.1
                name='SM_WheatPatch' if f['kind']=='wheat' else 'SM_CropClump'
                static(name,'Crop_%d_%02d_%02d'%(fi,ix,iy),x,y,yaw=random.uniform(-10,10),scale=random.uniform(.84,1.10),collide=False)
    # Sparse irregular grass at path margins, meadow patches and field borders.
    placed=0
    for attempt in range(5500):
        x,y=random.uniform(-48,48),random.uniform(-48,48)
        dist=path_distance(x,y)
        if dist<.05 or in_field(x,y,1.1):continue
        if math.hypot(x-MILL[0],y-MILL[1])<4.5:continue
        if abs(x-BARN[0])<6 and abs(y-BARN[1])<4.8:continue
        if abs(x-SHED[0])<4 and abs(y-SHED[1])<4:continue
        if dist>2 and random.random()>.17:continue
        static('SM_GrassTuft','Grass_%04d'%placed,x,y,yaw=random.uniform(0,360),scale=random.uniform(.65,1.8),collide=False);placed+=1
        if placed>=650:break
    for i,(x,y) in enumerate([(-37,-37),(-16,-37),(-37,0),(-15,0),(15,-34),(34,-10),(37,18),(-14,22),(-31,43)]):
        static('SM_FieldRock','BoundaryRocks_%02d'%i,x,y,yaw=random.random()*360,scale=random.uniform(.65,1.5))
    # Soft dynamic illumination with a restrained warm sun and neutral sky fill.
    light=spawn(u.DirectionalLight,'AfternoonSun',(0,0,1600),(-42,-32,0));lc=light.light_component;lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(3.2);lc.set_light_color(u.LinearColor(1,.92,.78,1));lc.set_editor_property('dynamic_shadow_distance_movable_light',20000.0)
    sky=spawn(u.SkyLight,'DaylightFill',(0,0,1000));sc=sky.light_component;sc.set_mobility(u.ComponentMobility.MOVABLE);sc.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sc.set_cubemap(u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'));sc.set_intensity(1.1);sc.set_editor_property('lower_hemisphere_is_black',False);sc.recapture_sky()
    sphere=spawn(u.StaticMeshActor,'SkyBackdrop',(0,0,0));sphere.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere'));sphere.static_mesh_component.set_material(0,u.load_asset(BASE+'/Materials/M_Sky'));sphere.set_actor_scale3d(vec((1000,1000,1000)));sphere.static_mesh_component.set_collision_profile_name('NoCollision');sphere.static_mesh_component.set_cast_shadow(False)
    pp=spawn(u.PostProcessVolume,'FarmColorAndExposure');pp.set_editor_property('unbound',True);s=pp.get_editor_property('settings')
    for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',0.0),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_vignette_intensity',True),('vignette_intensity',.10),('override_bloom_intensity',True),('bloom_intensity',.05),('override_ambient_occlusion_intensity',True),('ambient_occlusion_intensity',.7),('override_ambient_occlusion_radius',True),('ambient_occlusion_radius',110.)]:s.set_editor_property(k,v)
    pp.set_editor_property('settings',s)
    spawn(u.PlayerStart,'FarmArrival',(-400,1500,150),(0,-90,0))
    assert levels.save_current_level()
    u.EditorAssetLibrary.save_directory(BASE,only_if_is_dirty=False,recursive=True)
    save_json('assembly.json',{'utc':utc(),'map':MAP,'actor_count':len(actors.get_all_level_actors()),'grass_clumps':placed,'field_fences':count,'trees':len(tree_positions),'footprint_m':[100,100],'lighting':'movable sun and skylight, no baked lightmaps','controls':'Engine DefaultPawn movement, mouse look; no custom shared code'})
    u.log('WINDFARM_ASSEMBLY_COMPLETE')

if __name__=='__main__':
    try:run()
    except Exception as e:fail(e,'assembly');raise
