"""Assemble independently authored GLBs without duplicating mesh or texture data.

Placements are in the shared meter, Z-up authoring frame. Each imported module
retains its single axis-conversion root; wrappers use glTF Y-up transforms.
"""
from pathlib import Path
import copy, hashlib, json, math, struct, io
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def read_glb(path):
    b=Path(path).read_bytes(); magic,version,length=struct.unpack_from('<4sII',b)
    assert magic==b'glTF' and version==2 and length==len(b)
    j=None;blob=b'';off=12
    while off<len(b):
        n,t=struct.unpack_from('<II',b,off);off+=8;part=b[off:off+n];off+=n
        if t==0x4e4f534a:j=json.loads(part)
        elif t==0x004e4942:blob=part
    return j,blob

class Assembly:
    def __init__(self):
        self.j={'asset':{'version':'2.0','generator':'Riverdale modular assembly'},'scene':0,'scenes':[{'name':'Riverdale Steam Station','nodes':[]}], 'nodes':[], 'meshes':[], 'materials':[], 'textures':[], 'images':[], 'samplers':[], 'accessors':[], 'bufferViews':[]}
        self.blob=bytearray();self.cache={};self.bvcache={};self.imagecache={};self.sampler_cache={};self.texture_cache={};self.material_cache={};self.placements=[]
    def unique(self,key,value,cache):
        h=json.dumps(value,sort_keys=True,separators=(',',':'))
        if h not in cache:cache[h]=len(self.j[key]);self.j[key].append(value)
        return cache[h]
    def load(self,rel):
        if rel in self.cache:return self.cache[rel]
        src,blob=read_glb(ROOT/rel)
        # Delivery copy uses JPEG for opaque color images; normal/ORM stay lossless.
        color_images=set()
        for material in src.get('materials',[]):
            pbr=material.get('pbrMetallicRoughness',{})
            for texture in [pbr.get('baseColorTexture'),material.get('emissiveTexture')]:
                if texture is not None:color_images.add(src['textures'][texture['index']]['source'])
        replacements={}
        for image_index in color_images:
            imeta=src['images'][image_index]
            if 'bufferView' not in imeta:continue
            bv=src['bufferViews'][imeta['bufferView']]
            data=blob[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
            im=Image.open(io.BytesIO(data))
            if im.mode=='RGBA' and im.getchannel('A').getextrema()[0]<255:continue
            dest=io.BytesIO();im.convert('RGB').save(dest,format='JPEG',quality=90,subsampling=0,optimize=True)
            if len(dest.getvalue())<len(data):
                replacements[imeta['bufferView']]=dest.getvalue();imeta['mimeType']='image/jpeg'
        bmap={}
        image_views={im['bufferView'] for im in src.get('images',[]) if 'bufferView' in im}
        for i,bv in enumerate(src.get('bufferViews',[])):
            data=blob[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
            data=replacements.get(i,data)
            meta={k:v for k,v in bv.items() if k not in ['buffer','byteOffset','byteLength','name']}
            h=hashlib.sha256(data+json.dumps(meta,sort_keys=True).encode()).hexdigest()
            # Sharing an attribute bufferView between independent tightly packed
            # accessors requires byteStride in glTF. Only deduplicate image views.
            if i not in image_views:h=f'{rel}:{i}:{h}'
            if h not in self.bvcache:
                while len(self.blob)%4:self.blob.append(0)
                self.bvcache[h]=len(self.j['bufferViews'])
                self.j['bufferViews'].append(dict(meta,buffer=0,byteOffset=len(self.blob),byteLength=len(data)))
                self.blob.extend(data)
            bmap[i]=self.bvcache[h]
        amap={}
        for i,a in enumerate(src.get('accessors',[])):
            a=copy.deepcopy(a)
            if 'bufferView'in a:a['bufferView']=bmap[a['bufferView']]
            if a.get('sparse'):
                for k in ['indices','values']:a['sparse'][k]['bufferView']=bmap[a['sparse'][k]['bufferView']]
            amap[i]=len(self.j['accessors']);self.j['accessors'].append(a)
        imap={}
        for i,v in enumerate(src.get('images',[])):
            v=copy.deepcopy(v);v.pop('name',None)
            if 'bufferView'in v:v['bufferView']=bmap[v['bufferView']]
            assert 'uri' not in v,'Expected embedded image'
            imap[i]=self.unique('images',v,self.imagecache)
        smap={i:self.unique('samplers',v,self.sampler_cache) for i,v in enumerate(src.get('samplers',[]))}
        tmap={}
        for i,v in enumerate(src.get('textures',[])):
            v=copy.deepcopy(v)
            if 'source'in v:v['source']=imap[v['source']]
            if 'sampler'in v:v['sampler']=smap[v['sampler']]
            tmap[i]=self.unique('textures',v,self.texture_cache)
        def remap_textures(v):
            if isinstance(v,dict):
                for k,x in v.items():
                    if k.endswith('Texture') and isinstance(x,dict) and 'index'in x:x['index']=tmap[x['index']]
                    else:remap_textures(x)
            elif isinstance(v,list):
                for x in v:remap_textures(x)
        mmap={}
        for i,v in enumerate(src.get('materials',[])):
            v=copy.deepcopy(v);remap_textures(v)
            mmap[i]=self.unique('materials',v,self.material_cache)
        meshmap={}
        for i,m in enumerate(src.get('meshes',[])):
            m=copy.deepcopy(m)
            for p in m['primitives']:
                p['attributes']={k:amap[v] for k,v in p['attributes'].items()}
                if 'indices'in p:p['indices']=amap[p['indices']]
                if 'material'in p:p['material']=mmap[p['material']]
                for target in p.get('targets',[]):
                    for k,v in target.items():target[k]=amap[v]
            meshmap[i]=len(self.j['meshes']);self.j['meshes'].append(m)
        template=copy.deepcopy(src['nodes'])
        for n in template:
            if 'mesh'in n:n['mesh']=meshmap[n['mesh']]
            assert 'skin' not in n
        roots=src['scenes'][src.get('scene',0)]['nodes']
        for k in ['extensionsUsed','extensionsRequired']:
            if src.get(k):self.j[k]=sorted(set(self.j.get(k,[])+src[k]))
        self.cache[rel]=(template,roots)
        return template,roots
    def place(self,rel,xyz=(0,0,0),yaw=0,name=None,scale=None):
        if not (ROOT/rel).exists():return False
        nodes,roots=self.load(rel);off=len(self.j['nodes'])
        for node in nodes:
            n=copy.deepcopy(node)
            if 'children'in n:n['children']=[c+off for c in n['children']]
            self.j['nodes'].append(n)
        x,y,z=xyz;a=math.radians(yaw)/2
        wrap={'name':name or Path(rel).stem,'translation':[x,z,-y],'rotation':[0,math.sin(a),0,math.cos(a)],'children':[n+off for n in roots]}
        if scale is not None:wrap['scale']=[scale]*3 if isinstance(scale,(float,int)) else [scale[0],scale[2],scale[1]]
        self.j['scenes'][0]['nodes'].append(len(self.j['nodes']));self.j['nodes'].append(wrap)
        self.placements.append({'file':rel,'name':wrap['name'],'position_zup_m':list(xyz),'yaw_degrees':yaw,'scale':scale})
        return True
    def save(self,path):
        while len(self.blob)%4:self.blob.append(0)
        self.j['buffers']=[{'byteLength':len(self.blob)}]
        js=json.dumps(self.j,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
        b=struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(self.blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(self.blob),0x004e4942)+self.blob
        Path(path).write_bytes(b)
        return len(b)

def build():
    a=Assembly();p=a.place
    p('modules/architecture/architecture_assembled.glb',(-38,0,.12),name='Station terminal')
    p('modules/shed/front_arch.glb',(0,0,0),name='Shed entrance')
    for y in range(0,48,8):p('modules/shed/shed_bay.glb',(0,y,0),name=f'Train shed bay {y//8+1}')
    for x in [-12,0,12]:
        for y in range(0,56,8):p('modules/infrastructure/platform_segment.glb',(x,y,0),name=f'Platform {x} / {y}')
        p('modules/infrastructure/platform_ramp.glb',(x,-8,0),name=f'Platform access ramp {x}')
    for x in [-6,6]:
        for y in range(-24,64,8):p('modules/infrastructure/track_segment.glb',(x,y,0),name=f'Track {x} / {y}')
    for x in [-12,-4,4,12]:
        for y in range(0,56,8):p('modules/infrastructure/plaza_tile.glb',(x,y,-.12),name='Station floor')
    for x in range(-58,-9,8):
        for y in [-16,-8]:p('modules/infrastructure/plaza_tile.glb',(x,y,0),name='Terminal forecourt')
    # Canopy on the western platform, beyond the hall facade, makes a sheltered route.
    for y in [8,16,24,32,40]:p('modules/shed/platform_canopy_bay.glb',(-12,y,1),name='Platform canopy')
    p('modules/locomotive/locomotive.glb',(6,-8,.22),name='Steam locomotive 726')
    p('modules/locomotive/tender.glb',(6,2.1,.22),name='Coal tender')
    for i,y in enumerate([7.3,22.6,37.9]):p('modules/carriage/passenger_carriage.glb',(6,y,.22),name=f'Passenger carriage {i+1}')
    p('modules/carriage/passenger_carriage.glb',(-6,29,.22),name='Waiting carriage')
    for x in [-11,1,13]:
        for y in [3,15,27,39,51]:p('modules/props/station_gaslamp.glb',(x,y,1),name='Platform lantern')
    for x in [-58,-46,-34,-22]:p('modules/props/station_gaslamp.glb',(x,-9,.12),name='Forecourt lantern')
    for x,y,yaw in [(-12,5,90),(-12,21,90),(-12,37,90),(0,11,90),(0,27,90),(12,10,-90),(12,26,-90),(-45,-5,0),(-31,-5,0)]:
        p('modules/props/station_bench.glb',(x,y,1 if x>=-14 else .12),yaw,name='Waiting bench')
    for x,y in [(-11,2),(1,8),(13,4)]:p('modules/props/station_clock_sign.glb',(x,y,1),name='Platform clock and sign')
    for x,y,yaw in [(-12,10,0),(0,4,20),(12,19,-15),(-32,-7,85)]:
        p('modules/freight_props/luggage_cart.glb',(x,y,1 if x>=-14 else .12),yaw,name='Luggage cart')
    for i,(x,y) in enumerate([(-11,43),(-12,44),(-13,43),(1,45),(12,47),(-53,-5),(-52,-5)]):
        p('modules/freight_props/crate.glb',(x,y,1 if x>=-14 else .12),i*15,name='Freight crate')
    for x,y in [(-12,46),(0,47),(12,49),(-54,-5)]:p('modules/freight_props/barrel.glb',(x,y,1 if x>=-14 else .12),name='Freight barrel')
    size=a.save(ROOT/'Riverdale_Station_assembled.glb')
    (ROOT/'scene_layout.json').write_text(json.dumps({'units':'meters','author_frame':'X right,Y depth,Z up','instances':a.placements},indent=2))
    unique=sum(sum(a.j['accessors'][pr['indices']]['count']//3 for pr in m['primitives']) for m in a.j['meshes'])
    drawn=sum(sum(a.j['accessors'][pr['indices']]['count']//3 for pr in a.j['meshes'][n['mesh']]['primitives']) for n in a.j['nodes'] if 'mesh'in n)
    report={'placements':len(a.placements),'unique_assets':len(a.cache),'unique_triangles':unique,'drawn_triangles':drawn,'meshes':len(a.j['meshes']),'nodes':len(a.j['nodes']),'materials':len(a.j['materials']),'images':len(a.j['images']),'glb_bytes':size,'sources':list(a.cache)}
    (ROOT/'reports/assembly.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':build()
