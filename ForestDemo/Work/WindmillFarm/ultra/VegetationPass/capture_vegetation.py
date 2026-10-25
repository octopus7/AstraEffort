import sys,json
from pathlib import Path
PASS=Path(__file__).resolve().parent;sys.path.insert(0,str(PASS.parent));sys.path.insert(0,str(PASS))
from ue_common import *
import ue_capture_pipeline as base
from assemble_vegetation import field_distance,entrance_distance
base.CAMERAS=dict(base.CAMERAS)
base.CAMERAS.update({'corn':{'location':[3800,-1900,550],'target':[3100,-3000,110],'fov':50.0},
                     'meadow':{'location':[-1700,-3400,300],'target':[-3000,-3000,70],'fov':55.0}})
original_validate=base.validate_static

def validate():
    world,checks,detail=original_validate();assembly=json.loads((PASS/'assembly.json').read_text())
    counts={};colors={};wind={}
    for a in actors.get_all_level_actors():
        for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
            sm=c.static_mesh
            if sm and sm.get_name() in assembly['counts']:counts[sm.get_name()]=counts.get(sm.get_name(),0)+c.get_instance_count()
    for name in assembly['counts']:
        sm=u.load_asset(BASE+'/Meshes/'+name);colors[name]=meshes.has_vertex_colors(sm)
        for slot in sm.get_editor_property('static_materials'):
            m=slot.material_interface;node=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
            connected=u.MaterialEditingLibrary.get_inputs_for_material_expression(m,node) if node else []
            wind[m.get_name()]=bool(node and isinstance(node,u.MaterialExpressionCustom) and 'saturate(V.r)' in node.get_editor_property('code') and len(connected)==3 and any(isinstance(n,u.MaterialExpressionVertexColor) for n in connected))
    records=assembly['placements'];corn=[r for r in records if r['mesh'].startswith('SM_Corn')];meadow=[r for r in records if r['mesh'].startswith('SM_Meadow')]
    checks['corn_separate_field']=len(corn)>=200 and all(field_distance(*r['design_xy'])<-.5 for r in corn)
    checks['meadow_population']=len(meadow)>=700
    checks['saved_foliage_counts']=counts==assembly['counts']
    checks['wind_materials']=len(wind)==7 and all(wind.values())
    checks['vegetation_vertex_colors']=len(colors)==6 and all(colors.values())
    checks['paths_clear']=all(path_distance(*r['design_xy'])>=.8 and not in_field(*r['design_xy'],1.5) and entrance_distance(*r['design_xy'])>=.9 for r in meadow)
    envelopes={}
    for name in counts:
        scales=[r['scale'] for r in records if r['mesh']==name];sm=u.load_asset(BASE+'/Meshes/'+name)
        padding=sm.get_editor_property('positive_bounds_extension').x*min(scales)
        envelopes[name]={'min_world_padding_cm':padding,'max_wind_x_cm':21.46 if name.startswith('SM_Meadow') else 17.06}
    checks['wind_bounds_cover_motion']=all(v['min_world_padding_cm']>=v['max_wind_x_cm'] for v in envelopes.values())
    detail['vegetation']={'saved_counts':counts,'expected_counts':assembly['counts'],'wind_material_nodes':wind,'imported_mesh_vertex_colors':colors,'corn_field':assembly['corn_field'],'corn_rows':assembly['corn_rows'],'corn_count':len(corn),'meadow_count':len(meadow)}
    detail['vegetation']['wind_bounds']=envelopes
    return world,checks,detail
base.validate_static=validate

class VegetationPipeline(base.Pipeline):
    def __init__(self,runtime_only=False):
        super().__init__('VegetationPass/Screenshots',True,runtime_only)
        self.names+=['corn_motion_t0','corn_motion_t1','meadow_motion_t0','meadow_motion_t1']
        self.manifest['vegetation_wind']={'method':'Ground-anchored vertex-color WPO','amplitude_cm':{'corn':17,'meadow':22},'same_camera_pairs':['corn_motion_t0/corn_motion_t1','meadow_motion_t0/meadow_motion_t1'],'physical_simulation':False}
    def set_camera(self,name):
        alias='corn' if name.startswith('corn_motion') else 'meadow' if name.startswith('meadow_motion') else name
        super().set_camera(alias)
    def finish(self):
        save_json('VegetationPass/validation.json',{'utc':utc(),'checks':self.checks,'all_passed':all(self.checks.values()),'detail':self.detail})
        super().finish()

def start(runtime_only=False):
    global PIPELINE
    PIPELINE=VegetationPipeline(runtime_only)
