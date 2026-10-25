import sys,random,math,json
from pathlib import Path
PASS=Path(__file__).resolve().parent;sys.path.insert(0,str(PASS.parent));sys.path.insert(0,str(PASS))
from ue_common import *
from ue_import import import_file,new_material,expr,texture,connect,constant
from design import CORN,CORN_PATH,MEADOW_PATCHES,SEED

def wind_material(slot,tex):
    m=new_material('M_Wind_'+slot);m.set_editor_property('two_sided',True)
    sample=texture(m,tex);connect(m,sample,u.MaterialProperty.MP_BASE_COLOR)
    connect(m,constant(m,.84),u.MaterialProperty.MP_ROUGHNESS);connect(m,constant(m,.15),u.MaterialProperty.MP_SPECULAR)
    custom=expr(m,u.MaterialExpressionCustom,500,350);custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
    custom.set_editor_property('description','Ground-anchored breeze: vertex R height, G leaf flutter. Shared coherent wind phase.')
    ci=[]
    for name in ('P','V','T'):
        item=u.CustomInput();item.set_editor_property('input_name',name);ci.append(item)
    custom.set_editor_property('inputs',ci)
    amplitude=17 if slot.startswith('Corn') else 22
    code=f'''float w=pow(saturate(V.r),1.7); float phase=T*1.13+P.x*0.004+P.y*0.006;
float gust=0.72*sin(phase)+0.28*sin(T*0.61+P.x*0.002-P.y*0.003);
float sway={amplitude}.0*w*gust; float flutter=2.1*w*V.g*sin(T*5.7+P.x*0.019+P.z*0.05);
return float3(sway*0.88+flutter,sway*0.47+flutter*0.36,-abs(sway)*0.055*w);'''
    custom.set_editor_property('code',code)
    for cls,name,out,y in [(u.MaterialExpressionWorldPosition,'P','',100),(u.MaterialExpressionVertexColor,'V','',350),(u.MaterialExpressionTime,'T','',600)]:
        node=expr(m,cls,250,y);assert u.MaterialEditingLibrary.connect_material_expressions(node,out,custom,name),(slot,name)
    connect(m,custom,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    u.MaterialEditingLibrary.set_material_usage(m,u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    u.MaterialEditingLibrary.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
    return m

def import_mesh(p):
    task=u.AssetImportTask();task.set_editor_property('filename',str(p));task.set_editor_property('destination_path',BASE+'/Meshes');task.set_editor_property('automated',True);task.set_editor_property('save',True);task.set_editor_property('replace_existing',True)
    opts=u.FbxImportUI();opts.set_editor_property('import_mesh',True);opts.set_editor_property('import_as_skeletal',False);opts.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);opts.set_editor_property('automated_import_should_detect_type',False);opts.set_editor_property('import_materials',False);opts.set_editor_property('import_textures',False)
    d=opts.get_editor_property('static_mesh_import_data');d.set_editor_property('combine_meshes',True);d.set_editor_property('auto_generate_collision',False);d.set_editor_property('generate_lightmap_u_vs',False);d.set_editor_property('convert_scene',True);d.set_editor_property('convert_scene_unit',True);d.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS);d.set_editor_property('vertex_color_import_option',u.VertexColorImportOption.REPLACE)
    task.set_editor_property('options',opts);assets.import_asset_tasks([task]);paths=task.get_editor_property('imported_object_paths');assert paths
    sm=u.load_asset(paths[0]);padding=40 if p.stem.startswith('SM_Meadow') else 30
    sm.set_editor_property('positive_bounds_extension',vec((padding,padding,5)));sm.set_editor_property('negative_bounds_extension',vec((padding,padding,5)))
    return sm

def field_distance(x,y):
    cx,cy=CORN['center'];sx,sy=CORN['size'];return max(abs(x-cx)-sx/2,abs(y-cy)-sy/2)

def entrance_distance(x,y):
    p,q=CORN_PATH[0][0];w=CORN_PATH[0][1];dx,dy=q[0]-p[0],q[1]-p[1];t=max(0,min(1,((x-p[0])*dx+(y-p[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(x-p[0]-t*dx,y-p[1]-t*dy)-w

def run():
    assert 'Saved/Workers/WindmillFarm/ultra/Project' in u.Paths.project_dir().replace('\\','/')
    assert levels.load_level(MAP);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    textures={}
    for p in sorted((PASS/'Art/Textures').glob('T_*.png')):
        t=import_file(p,BASE+'/Textures');textures[p.stem]=t
    mats={slot:wind_material(slot,textures['T_'+slot+'_BaseColor']) for slot in ('CornLeaf','CornStalk','CornKernel','CornTassel','MeadowLeaf','MeadowStem','MeadowSeed')}
    foliage={};mesh_info=[]
    for folder in ('Corn','Meadow'):
        for p in sorted((PASS/'Art'/folder).glob('SM_*.fbx')):
            sm=import_mesh(p)
            for i,s in enumerate(sm.get_editor_property('static_materials')):
                slot=str(s.material_slot_name).split('.')[0];assert slot in mats,slot;sm.set_material(i,mats[slot])
            u.EditorAssetLibrary.save_loaded_asset(sm)
            name='FT_'+p.stem.removeprefix('SM_');ft=u.load_asset(BASE+'/Foliage/'+name)
            if not ft:ft=assets.create_asset(name,BASE+'/Foliage',u.FoliageType_InstancedStaticMesh,u.FoliageType_InstancedStaticMeshFactory())
            ft.set_editor_property('mesh',sm);ft.set_editor_property('enable_density_scaling',False);ft.set_editor_property('evaluate_world_position_offset',True);ft.set_editor_property('world_position_offset_disable_distance',0)
            body=ft.get_editor_property('body_instance');body.set_editor_property('collision_enabled',u.CollisionEnabled.NO_COLLISION);ft.set_editor_property('body_instance',body)
            u.EditorAssetLibrary.save_loaded_asset(ft);u.InstancedFoliageActor.remove_all_instances(world,ft);foliage[p.stem]=ft
            mesh_info.append({'mesh':p.stem,'uv_channels':meshes.get_num_uv_channels(sm,0),'materials':[str(s.material_slot_name) for s in sm.get_editor_property('static_materials')],'bounds':str(sm.get_bounding_box())})
    assert len(foliage)==6
    # Keep the original orchard population; move the tree occupying the new bed to its far edge.
    for actor in actors.get_all_level_actors():
        label=actor.get_actor_label()
        if label=='OrchardTree_06':actor.set_actor_location(vec((4100,-3900,height(41,39)*100)),False,True)
        if label.startswith('CornFence_'):actors.destroy_actor(actor)
        if label.startswith('Grass_'):
            p=actor.get_actor_location();x,y=p.x/100,-p.y/100
            if field_distance(x,y)<.8 or entrance_distance(x,y)<.8:actors.destroy_actor(actor)
    cx,cy=CORN['center'];sx,sy=CORN['size'];xmin,xmax=cx-sx/2,cx+sx/2;ymin,ymax=cy-sy/2,cy+sy/2
    fences=0
    for y in (ymin-.65,ymax+.65):
        for x in (25.,28.,31.,34.,37.):
            if y<cy and 28.5<x<32:continue
            static('SM_FenceSegment','CornFence_%02d'%fences,x,y);fences+=1
    for x in (xmin-.65,xmax+.65):
        for y in (25.5,28.5,31.5,34.5):static('SM_FenceSegment','CornFence_%02d'%fences,x,y,yaw=90);fences+=1
    rng=random.Random(SEED);placements={k:[] for k in foliage};records=[]
    def add(name,x,y,yaw,scale):
        z=height(x,y);tr=u.Transform(location=vec((x*100,-y*100,z*100)),rotation=u.Rotator(pitch=0,yaw=-yaw,roll=0),scale=vec((scale,scale,scale)))
        placements[name].append(tr);records.append({'mesh':name,'design_xy':[x,y],'height_m':z,'yaw':yaw,'scale':scale})
    # Deliberately ordered corn cultivation with a border and central service aisle.
    rows=0
    for ix in range(16):
        x=xmin+1.0+ix*.85
        if 29.5<x<30.7:continue
        rows+=1
        for iy in range(15):
            y=ymin+1.0+iy*.70
            add('SM_Corn'+('ABC'[(ix+iy)%3]),x+rng.uniform(-.06,.06),y+rng.uniform(-.06,.06),rng.uniform(-18,18)+(ix%2)*180,rng.uniform(.93,1.05))
    # Large uneven patches, graded to sparse fringes. Roads and building approaches stay open.
    attempts=0;accepted=0
    for pi,(cx,cy,rx,ry) in enumerate(MEADOW_PATCHES):
        count=int(math.pi*rx*ry*1.1)
        for _ in range(count):
            attempts+=1;theta=rng.random()*math.tau;r=math.sqrt(rng.random());x=cx+math.cos(theta)*rx*r;y=cy+math.sin(theta)*ry*r
            if abs(x)>48 or abs(y)>48 or path_distance(x,y)<.8 or in_field(x,y,1.5) or field_distance(x,y)<1.3 or entrance_distance(x,y)<.9:continue
            if math.hypot(x-MILL[0],y-MILL[1])<5.4:continue
            if abs(x-BARN[0])<6.6 and abs(y-BARN[1])<5.2:continue
            if abs(x-SHED[0])<4.7 and abs(y-SHED[1])<4.4:continue
            if 16<x<21 and 20<y<24:continue
            edge=(1-r);prob=.52+edge*.48+math.sin(x*1.7+y*1.2)*.13
            if rng.random()>prob:continue
            typ=rng.choices(['SM_MeadowTall','SM_MeadowPlume','SM_MeadowReed'],[.55,.35,.10])[0]
            if r>.83:typ='SM_MeadowPlume'
            add(typ,x,y,rng.uniform(0,360),rng.uniform(.78,1.14)*(1 if r<.84 else .75));accepted+=1
    for name,transforms in placements.items():
        assert transforms,name;u.InstancedFoliageActor.add_instances(world,foliage[name],transforms)
    # Enable material deformation on stored components too; types and transforms persist in this conventional level.
    for actor in actors.get_all_level_actors():
        for comp in actor.get_components_by_class(u.InstancedStaticMeshComponent):
            comp.set_collision_profile_name('NoCollision');comp.set_editor_property('evaluate_world_position_offset',True)
    assert levels.save_current_level();u.EditorAssetLibrary.save_directory(BASE,only_if_is_dirty=False,recursive=True)
    save_json('VegetationPass/assembly.json',{'utc':utc(),'corn_field':CORN,'corn_rows':rows,'corn_count':sum(len(v) for k,v in placements.items() if k.startswith('SM_Corn')),'meadow_count':accepted,'corn_fences':fences,'counts':{k:len(v) for k,v in placements.items()},'mesh_info':mesh_info,'placements':records,'instance_method':'UE foliage instanced static meshes, no separate actor per plant','wind':'Vertex color anchored WPO, common low frequency wind phase and local leaf flutter','tree_relocation':{'label':'OrchardTree_06','design_xyz':[41,39,height(41,39)]}})
    u.log('VEGETATION_ASSEMBLY_COMPLETE')
