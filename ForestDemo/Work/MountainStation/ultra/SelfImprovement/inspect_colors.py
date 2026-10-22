import bpy,json,datetime
from pathlib import Path
from io_scene_fbx import parse_fbx
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceArt/AlderPass_FinalTextured.blend'))
me=bpy.data.objects['SM_Footpath'].data
colors=[{'name':c.name,'domain':c.domain,'count':len(c.data),'min_r':min(x.color[0] for x in c.data),'max_r':max(x.color[0] for x in c.data)} for c in me.color_attributes]
root,version=parse_fbx.parse(str(R/'SourceArt/FinalFBX2/SM_Footpath.fbx'));layers=[]
def visit(n):
    if n.id==b'Layer':print('FBX_LAYER',n.props,[(c.id,c.props,[(d.id,d.props) for d in c.elems]) for c in n.elems])
    if n.id==b'LayerElementColor':
        row={}
        for c in n.elems:
            if c.id==b'Colors':
                vals=c.props[0];row['count']=len(vals)//4;row['min_r']=min(vals[0::4]);row['max_r']=max(vals[0::4])
            elif c.id==b'Name':row['name']=str(c.props)
        layers.append(row)
    for child in n.elems:visit(child)
visit(root)
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'blend_colors':colors,'fbx_color_layers':layers};(R/'color_source_diagnostics.json').write_text(json.dumps(out,indent=2));print(out)
