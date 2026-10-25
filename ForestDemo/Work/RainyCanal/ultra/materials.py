"""RainyCanal's original material graphs; editor-only creation."""
import unreal
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ASSET='/Game/RainyCanal/ultra'
LIB=unreal.MaterialEditingLibrary
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()

def node(mat,cls,**props):
    obj=LIB.create_material_expression(mat,cls,0,0)
    for key,value in props.items():obj.set_editor_property(key,value)
    return obj
def link(a,output,b,input):
    assert LIB.connect_material_expressions(a,output,b,input),(a,output,b,input)
def prop(n,p,output=''):
    assert LIB.connect_material_property(n,output,p),(n,p,output)
def custom(mat,code,inputs,kind=unreal.CustomMaterialOutputType.CMOT_FLOAT3):
    ins=[]
    for k in inputs:
        i=unreal.CustomInput();i.set_editor_property('input_name',k);ins.append(i)
    n=node(mat,unreal.MaterialExpressionCustom,code=code,output_type=kind,inputs=ins)
    for k,v in inputs.items():link(v,'',n,k)
    return n
def scalar(mat,v):return node(mat,unreal.MaterialExpressionConstant,r=v)
def color(mat,v):return node(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*v,1))
def texture(mat,tex,coords,normal=False):
    n=node(mat,unreal.MaterialExpressionTextureSample,texture=tex,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else (unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if tex.get_editor_property('srgb') else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE if tex.get_editor_property('compression_settings')==unreal.TextureCompressionSettings.TC_GRAYSCALE else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR))
    link(coords,'',n,'UVs');return n
def create(name,two=False,unlit=False,translucent=False):
    path=ASSET+'/Materials/M_'+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):unreal.EditorAssetLibrary.delete_asset(path)
    m=TOOLS.create_asset('M_'+name,ASSET+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    m.set_editor_property('two_sided',two)
    if unlit:m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    if translucent:m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    return m
def save(m):
    LIB.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m);return m

PATH_MASK='''float2 q=float2(P.x,-P.y)*.01;
float quay=abs(abs(q.x)-10.5)-4.5;
float lane=min(abs(q.y+15)-3.5,abs(q.y-28)-3.0);
float outer=abs(abs(q.x)-32)-2.1;
float doorY=min(min(abs(q.y+35),abs(q.y+10)),min(abs(q.y-13),abs(q.y-37)));
float doorstep=max(abs(abs(q.x)-16.5)-2.0,doorY-1.25);
float d=min(min(quay,doorstep),min(lane,outer));
float noise=.12*sin(q.x*8+sin(q.y*6))+.07*sin(q.y*13+q.x*5);
return 1-smoothstep(-.17,.22,d+noise);'''

def build(textures):
    mats={}
    for slot in ['Stone','Cobble','PlasterCream','PlasterSage','PlasterRose','Timber','RoofSlate','RoofClay','Metal','Leaf']:
        m=create(slot,two=slot=='Leaf');coord=node(m,unreal.MaterialExpressionTextureCoordinate,coordinate_index=1)
        if slot in ('Stone','Timber'):
            wp=node(m,unreal.MaterialExpressionWorldPosition);vn=node(m,unreal.MaterialExpressionVertexNormalWS)
            coord=custom(m,'float3 a=abs(N);if(a.z>.65)return P.xy/800.;if(a.x>a.y)return float2(P.y,P.z)/800.;return float2(P.x,P.z)/800.;',{'P':wp,'N':vn},unreal.CustomMaterialOutputType.CMOT_FLOAT2)
        for suffix,target,normal in [('BaseColor',unreal.MaterialProperty.MP_BASE_COLOR,False),('Roughness',unreal.MaterialProperty.MP_ROUGHNESS,False),('Normal',unreal.MaterialProperty.MP_NORMAL,True)]:
            n=texture(m,textures[f'T_{slot}_{suffix}'],coord,normal)
            prop(n,target,'RGB' if suffix!='Roughness' else 'R')
        prop(scalar(m,.7 if slot=='Metal' else 0),unreal.MaterialProperty.MP_METALLIC)
        prop(scalar(m,.45),unreal.MaterialProperty.MP_SPECULAR)
        mats[slot]=save(m)
    m=create('WindowGlass');prop(color(m,(.28,.18,.072)),unreal.MaterialProperty.MP_BASE_COLOR);prop(color(m,(.48,.255,.075)),unreal.MaterialProperty.MP_EMISSIVE_COLOR);prop(scalar(m,.18),unreal.MaterialProperty.MP_ROUGHNESS);mats['WindowGlass']=save(m)
    m=create('Ground');pos=node(m,unreal.MaterialExpressionWorldPosition)
    coord=custom(m,'return P.xy/800.0;',{'P':pos},unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    mask=custom(m,PATH_MASK,{'P':pos},unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    c=texture(m,textures['T_Cobble_BaseColor'],coord);rough=texture(m,textures['T_Cobble_Roughness'],coord);normal=texture(m,textures['T_Cobble_Normal'],coord,True)
    # TextureSample default output is RGB; use explicitly where scalar mixing is needed.
    col=custom(m,'float v=.94+.05*sin(P.x*.023)*sin(P.y*.017);return lerp(float3(.105,.165,.105)*v,C,M);',{'P':pos,'C':c,'M':mask});prop(col,unreal.MaterialProperty.MP_BASE_COLOR)
    rn=custom(m,'return lerp(.85,R.r,M);',{'R':rough,'M':mask},unreal.CustomMaterialOutputType.CMOT_FLOAT1);prop(rn,unreal.MaterialProperty.MP_ROUGHNESS)
    norm=custom(m,'return normalize(lerp(float3(0,0,1),N,M));',{'N':normal,'M':mask});prop(norm,unreal.MaterialProperty.MP_NORMAL);mats['Ground']=save(m)
    for name,puddle in [('CanalWater',False),('PuddleWater',True)]:
        m=create(name,two=True);p=node(m,unreal.MaterialExpressionWorldPosition);t=node(m,unreal.MaterialExpressionTime)
        # Ring normals repeat spatially with independently phased cells and two wave frequencies.
        code='''float2 cell=floor(P.xy/145.0);float2 local=frac(P.xy/145.0)*145.0;
float h=frac(sin(dot(cell,float2(127.1,311.7)))*43758.5453);
float h2=frac(sin(dot(cell,float2(269.5,183.3)))*23421.631);
float2 dv=local-float2(30+h*85,30+h2*85);float d=length(dv)+.001;
float age=frac(T*.72+h);float radius=age*62;
float ring=cos((d-radius)*.45)*exp(-abs(d-radius)*.17)*(1-age)*.28;
float2 slopes=dv/d*ring;
slopes+=float2(sin(P.x*.028+T*.9+sin(P.y*.018)),cos(P.y*.031-T*.7+sin(P.x*.02)))*.035;
return normalize(float3(slopes,1));'''
        n=custom(m,code,{'P':p,'T':t});prop(n,unreal.MaterialProperty.MP_NORMAL)
        prop(color(m,(.042,.069,.073) if puddle else (.028,.082,.095)),unreal.MaterialProperty.MP_BASE_COLOR)
        prop(scalar(m,.15 if puddle else .22),unreal.MaterialProperty.MP_ROUGHNESS);prop(scalar(m,.18),unreal.MaterialProperty.MP_METALLIC);prop(scalar(m,.8),unreal.MaterialProperty.MP_SPECULAR)
        if not puddle:
            edge=custom(m,'float b=1-smoothstep(556,591,abs(P.x));return float3(.018,.029,.028)*(1-b)*(.65+.35*sin(P.y*.09+T));',{'P':p,'T':t});prop(edge,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mats[name]=save(m)
    m=create('Rain',two=True,unlit=True,translucent=True)
    p=node(m,unreal.MaterialExpressionWorldPosition);t=node(m,unreal.MaterialExpressionTime);v=node(m,unreal.MaterialExpressionVertexColor)
    wpo=custom(m,'float a=frac(V.r-T*.72);return float3((a-.5)*65,(a-.5)*22,a*1400);',{'P':p,'T':t,'V':v})
    prop(wpo,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET);prop(color(m,(.46,.58,.62)),unreal.MaterialProperty.MP_EMISSIVE_COLOR);prop(scalar(m,.24),unreal.MaterialProperty.MP_OPACITY)
    mats['Rain']=save(m)
    return mats
