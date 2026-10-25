import unreal as u,json,traceback,sys,math
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
PROJECT=Path('D:/github/AstraEffort/ForestDemo/Saved/Workers/WindmillFarm/ultra/Project')
BASE='/Game/WindmillFarm/ultra';MAP='/Game/Maps/WindmillFarm_ultra'
sys.path.insert(0,str(ROOT))
from landscape_design import height,PATHS,FIELDS,MILL,BARN,SHED,path_distance,in_field
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
meshes=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
assets=u.AssetToolsHelpers.get_asset_tools()
def utc():return datetime.now(timezone.utc).isoformat()
def save_json(name,obj):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,default=str))
def vec(v):return u.Vector(*v)
def spawn(cls,label,location=(0,0,0),rotation=(0,0,0)):
    a=actors.spawn_actor_from_class(cls,vec(location),u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]));a.set_actor_label(label);return a
def static(name,label,x=0,y=0,z=None,yaw=0,scale=1,collide=True):
    if z is None:z=height(x,y)
    if not label.startswith(('Grass_','Crop_','FieldFence_')):u.log('ASSEMBLE '+label+' using '+name)
    # FBX handedness conversion preserves X/Z and negates Blender Y.
    a=spawn(u.StaticMeshActor,label,(x*100,-y*100,z*100),(0,-yaw,0));c=a.static_mesh_component
    c.set_static_mesh(u.load_asset(BASE+'/Meshes/'+name));a.set_actor_scale3d(vec((scale,)*3 if isinstance(scale,(float,int)) else scale))
    c.set_mobility(u.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll' if collide else 'NoCollision')
    if not collide:c.set_can_ever_affect_navigation(False) if hasattr(c,'set_can_ever_affect_navigation') else None
    return a
def fail(exc,stage):
    save_json(stage+'_error.json',{'utc':utc(),'exception':str(exc),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc())

CAMERAS={
 'overview':{'location':[7800,10500,7200],'target':[0,-200,100],'fov':48.0},
 'top_down':{'location':[0,0,15000],'target':[0,0,0],'ortho_width':18500.0},
 'windmill':{'location':[1700,2500,1350],'target':[-600,-1300,730],'fov':46.0},
 'farm_detail':{'location':[4300,2300,1350],'target':[2200,-800,210],'fov':50.0},
 'prop_contact':{'location':[3500,-2800,650],'target':[2350,-1950,110],'fov':48.0}}
