import unreal as u,json,datetime,math,bisect,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');A='/Game/MountainStation/ultra'
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def percentile(a):
    a=sorted(a);return {str(q):a[round((len(a)-1)*q/100)] if a else None for q in [0,1,5,50,95,99,100]}
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def intersection_area(subject,clip):
    out=list(subject)
    if cross(*clip)<0:clip=list(reversed(clip))
    for a,b in zip(clip,clip[1:]+clip[:1]):
        inp=out;out=[]
        if not inp:return 0.
        for p,q in zip(inp,inp[1:]+inp[:1]):
            dp=cross(a,b,p);dq=cross(a,b,q)
            if dp>=-1e-9:out.append(p)
            if (dp<0)!=(dq<0):
                t=dp/(dp-dq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(out,out[1:]+out[:1])))*.5 if len(out)>2 else 0.
def validate_uv():
    result={'started_at_utc':stamp(),'scope':'Every LOD0 triangle of all owned placed static meshes, actual component transforms in centimetres, actual imported UV0 and material texture dimensions/scales','uv_import_basis':'UE FbxStaticMeshImport.cpp line 758 flips V for DirectX; convert back with (u,1-v) only for layout correspondence. Density is flip-invariant.','meshes':[],'passed':False}
    layouts=json.loads((R/'uv_layouts.json').read_text());build=json.loads((R/'build_evidence.json').read_text());sources={m['mesh']:m for m in json.loads((R/'source_uv_validation.json').read_text())['meshes']}
    materials={m['material']:m for m in build['materials']};editor=u.get_editor_subsystem(u.EditorActorSubsystem);ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);ml=u.MaterialEditingLibrary
    actors=[a for a in editor.get_all_level_actors() if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_path_name().startswith(A+'/Meshes/')]
    assert len(actors)==48
    for actor in actors:
        component=actor.static_mesh_component;sm=component.static_mesh;name=sm.get_name();layout=layouts[name];source=sources[name];side=layout['side_px'];pad=layout['padding_each_side_px'];charts=layout['charts'];rows=layout['rows'];ys=[row['y'] for row in rows]
        record={'mesh':sm.get_path_name(),'actor':actor.get_path_name(),'component':component.get_path_name(),'actor_scale':list(actor.get_actor_scale3d().to_tuple()),'lod0_sections':sm.get_num_sections(0),'full_precision_uvs':ss.get_lod_build_settings(sm,0).use_full_precision_u_vs,'virtual_atlas_side_px':side,'sections':[]}
        assert record['full_precision_uvs'];result['meshes'].append(record)
        row_xs=[[charts[i][1] for i in row['charts']] for row in rows]
        density=[];resolved=[];worldarea=0.;uvarea_sum=0.;triangle_count=0;invalid=0;minpad=1e9;small=0;degenerate=0;outside5=0;area_outside5=0.;chart_tris={};sections=[];invalid_examples=[]
        for si in range(sm.get_num_sections(0)):
            slot=ss.get_lod_material_slot(sm,0,si);material=component.get_material(slot)
            section={'index':si,'slot':slot,'material':material.get_path_name(),'collision_enabled':ss.is_section_collision_enabled(sm,0,si)};record['sections'].append(section)
            if material.get_path_name() in materials:
                expected=materials[material.get_path_name()];tex=ml.get_material_instance_texture_parameter_value(material,'DetailTexture');scale=ml.get_material_instance_vector_parameter_value(material,'UVScale')
                assert material.get_editor_property('parent').get_path_name()==expected['parent']
                dims=[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()]
                assert dims==expected['source_dimensions'] and tex.get_path_name()==expected['texture']
                assert abs(scale.r*dims[0]-side)<.02 and abs(scale.g*dims[1]-side)<.02
                section.update(texture=tex.get_path_name(),texture_dimensions=dims,uv_scale=[scale.r,scale.g],effective_pixel_axes=[scale.r*dims[0],scale.g*dims[1]],actual_image_sampler=True)
            else:
                allowed={s['material'] for mesh in build['meshes'] if mesh['name']==name for s in mesh['slots'] if 'texture_exemption' in s}
                assert material.get_path_name() in allowed,('Unexpected untextured material',name,material.get_path_name())
                section.update(actual_image_sampler=False,exception='Explicit original solid/special-material exception')
            data=u.ProceduralMeshLibrary.get_section_from_static_mesh(sm,0,si);verts,indices,uvs=data[0],data[1],data[3]
            world=[u.MathLibrary.transform_location(component.get_world_transform(),p)/100 for p in verts]
            section['triangle_count']=len(indices)//3
            for j in range(0,len(indices),3):
                ii=[indices[j+k] for k in range(3)];p=[world[k] for k in ii];t=[(uvs[k].x*side,(1-uvs[k].y)*side) for k in ii]
                a=(p[1]-p[0]).cross(p[2]-p[0]).length()*.5;ua=abs(cross(*t))*.5;worldarea+=a;uvarea_sum+=ua;triangle_count+=1
                if a>1e-12:
                    d=math.sqrt(ua/a);density.append(d)
                    if ua>=1:resolved.append(d)
                    else:small+=1
                    if abs(d-128)>6.4:outside5+=1;area_outside5+=a
                else:degenerate+=1
                cx=sum(v[0] for v in t)/3;cy=sum(v[1] for v in t)/3;ri=bisect.bisect_right(ys,cy)-1
                if ri<0:invalid+=1;continue
                row=rows[ri];ci=bisect.bisect_right(row_xs[ri],cx)-1
                if ci<0:invalid+=1;continue
                chartid=row['charts'][ci];c=charts[chartid];x,y,w,h=c[1:5]
                if any(px<x+pad-.05 or px>x+pad+c[5]+.05 or py<y+pad-.05 or py>y+pad+c[6]+.05 for px,py in t):
                    invalid+=1
                    if len(invalid_examples)<12:invalid_examples.append({'section':si,'triangle':j//3,'uv_pixels':t,'assigned_chart':c,'row':ri})
                    continue
                minpad=min(minpad,min(min(px-x,x+w-px,py-y,y+h-py) for px,py in t));chart_tris.setdefault(chartid,[]).append(t)
        overlap_large=overlap_small=0;maxoverlap=0.
        for items in chart_tris.values():
            for i in range(len(items)):
                for j in range(i):
                    ar=intersection_area(items[i],items[j]);maxoverlap=max(maxoverlap,ar)
                    if ar>.05:overlap_large+=1
                    elif ar>1e-4:overlap_small+=1
        record.update(triangles_checked=triangle_count,world_surface_area_m2=worldarea,source_world_area_m2=source['world_surface_area_m2'],source_triangles=source['source_triangles'],triangle_density_percentiles=percentile(density),resolved_triangle_density_percentiles=percentile(resolved),triangles_under_one_base_texel_area=small,degenerate_triangles=degenerate,triangles_outside_5_percent=outside5,area_fraction_outside_5_percent=area_outside5/worldarea if worldarea else 0,uv_chart_containment_failures=invalid,minimum_measured_padding_px=minpad,inter_chart_overlap_pairs=0 if invalid==0 else None,intra_chart_overlaps_above_0_05px2=overlap_large,subpixel_intersection_pairs=overlap_small,maximum_intersection_px2=maxoverlap,charts_used=len(chart_tris),source_charts=len(charts))
        record['invalid_examples']=invalid_examples
        (R/'uv_validation.json').write_text(json.dumps(result,indent=2))
        assert invalid==0,(name,'chart containment',invalid)
        assert minpad>=pad-.06,(name,'padding',minpad)
        assert overlap_large==0,(name,'UV overlap',overlap_large,maxoverlap)
        assert abs(worldarea-source['world_surface_area_m2'])/max(worldarea,1e-9)<.005,(name,'world area changed')
        # Terrain's existing nonplanar quads are area-normalized per polygon.
        # Source and UE both retain 32 extreme-slope triangles outside +/-5%.
        # Report this geometry-preserving exception; do not claim exact per-triangle density.
        limit=.002 if name=='SM_Terrain' else .001
        record['density_outlier_area_limit']=limit
        record['density_exception']='Nonplanar terrain quads: up to 0.2% area outside +/-5%; source and imported triangle extremes reported.' if name=='SM_Terrain' else None
        assert area_outside5/max(worldarea,1e-9)<limit,(name,'material density not preserved',record)
        (R/'uv_validation.json').write_text(json.dumps(result,indent=2));u.log('TEXTURE_UV_CHECKED '+name)
    before=json.loads((R/'scene_before_self.json').read_text())['actors'];current=[]
    for a in editor.get_all_level_actors():current.append({'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':list(a.get_actor_location().to_tuple()),'rotation':list(a.get_actor_rotation().to_tuple()),'scale':list(a.get_actor_scale3d().to_tuple())})
    allowed_new={'Pedestrian crossing','Tunnel entrance fill','Tunnel inner fill'}
    preserved=[a for a in current if a['label'] not in allowed_new]
    assert sorted(before,key=lambda a:a['label'])==sorted(preserved,key=lambda a:a['label']),'Unapproved actor placement changed'
    assert {a['label'] for a in current}- {a['label'] for a in before}==allowed_new
    master=u.load_asset(A+'/Materials/TexturePass/M_SurfaceDetail')
    result['material_graph']={'base_color_node':ml.get_material_property_input_node(master,u.MaterialProperty.MP_BASE_COLOR).get_class().get_path_name(),'roughness_node':ml.get_material_property_input_node(master,u.MaterialProperty.MP_ROUGHNESS).get_class().get_path_name(),'parent':master.get_path_name(),'texture_parameters':list(map(str,ml.get_texture_parameter_names(master)))}
    soft=u.load_asset(A+'/Materials/SelfImprovement/M_SoftPath')
    def pins(node):return dict(zip(map(str,ml.get_material_expression_input_names(node)),ml.get_inputs_for_material_expression(soft,node)))
    color=ml.get_material_property_input_node(soft,u.MaterialProperty.MP_BASE_COLOR);assert isinstance(color,u.MaterialExpressionMultiply)
    blend=pins(color)['A'];assert isinstance(blend,u.MaterialExpressionLinearInterpolate)
    inputs=pins(blend);vc=inputs['Alpha'];assert isinstance(vc,u.MaterialExpressionVertexColor)
    assert ml.get_input_node_output_name_for_material_expression(blend,vc)=='R'
    assert str(inputs['A'].get_editor_property('parameter_name'))=='EdgeTint' and str(inputs['B'].get_editor_property('parameter_name'))=='Tint'
    result['soft_path_graph']={'parent':soft.get_path_name(),'base_color':'Multiply','tint_blend':'LinearInterpolate(EdgeTint,Tint,VertexColor.R)','verified_saved_connections':True}
    result.update(original_actor_transforms_unchanged=True,finished_at_utc=stamp(),passed=True)
    (R/'uv_validation.json').write_text(json.dumps(result,indent=2));return result
