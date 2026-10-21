import bpy,json,math
R='D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass';src=json.load(open(R+'/uv_validation.json'));out=[]
for item in src['meshes']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.fbx(filepath=R+'/Source/'+item['name']+'.fbx');o=next(o for o in bpy.context.scene.objects if o.type=='MESH');me=o.data;uv=me.uv_layers.active.data;densities=[];pixelareas=[];worldarea=0.;uvarea=0.
 for p in me.polygons:
  a,b,c=[o.matrix_world@me.vertices[i].co for i in p.vertices];wa=(b-a).cross(c-a).length/2
  a,b,c=[uv[i].uv for i in p.loop_indices];ua=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2
  if wa>1e-10:densities.append(math.sqrt(ua*1254**2/wa));worldarea+=wa;uvarea+=ua;pixelareas.append(ua*1254**2)
 assert min(densities)>15.95 and max(densities)<16.05,(item['name'],min(densities),max(densities))
 out.append({'mesh':item['name'],'triangle_count':len(densities),'world_area_m2':worldarea,'uv_area':uvarea,'export_reimport_density_min':min(densities),'export_reimport_density_max':max(densities),'minimum_triangle_pixel_area':min(pixelareas),'subpixel_triangles':sum(a<1 for a in pixelareas),'bounds_m':[float(v) for v in o.dimensions]})
json.dump({'status':'passed','method':'Independent FBX export/reimport into new Blender scene, world-transformed triangle area versus stored UV area','meshes':out},open(R+'/fbx_roundtrip_validation.json','w'),indent=2)
