import unreal as u,json,datetime,hashlib,traceback
from pathlib import Path
OUT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement');MAP=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/ultra/SelfImprovement/ForestDemo/Content/Maps/ultra.umap')
report={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actors':[],'errors':[]}
try:
 application=json.loads((OUT/'palette_application.json').read_text());assert application['success'];settings=application['settings'];report['settings']=settings
 report['map_sha256']=hashlib.sha256(MAP.read_bytes()).hexdigest();assert report['map_sha256']==application['map_sha256_after']
 actors=u.get_editor_subsystem(u.EditorActorSubsystem);trees=[a for a in actors.get_all_level_actors() if isinstance(a,u.ForestUltraAnimeTreeActor)];assert len(trees)==63
 for a in trees:
  row={'actor':a.get_name(),'properties':{},'mids':[],'passed':True}
  for key,expected in {**settings,'wind_strength':.75,'leaf_card_scale':.8,'leaf_density':.45,'gradient_width':400,'gradient_exponent':1}.items():
   value=a.get_editor_property(key);actual=[value.r,value.g,value.b,value.a] if isinstance(expected,list) else value;row['properties'][key]=actual
   row['passed'] &= all(abs(x-y)<1e-5 for x,y in zip(actual,expected)) if isinstance(expected,list) else abs(actual-expected)<1e-5
  clumps=a.get_leaf_clumps();shadows=[c for c in a.get_components_by_class(u.StaticMeshComponent) if 'AnimeTreeShadow' in [str(x) for x in c.component_tags]];row['component_counts']={'clumps':len(clumps),'shadow_proxies':len(shadows)};row['passed'] &= len(clumps)==len(shadows)==10
  for c in clumps:
   mid=c.get_material(0);mr={'component':c.get_name(),'scalars':{},'colors':{}}
   for key,expected in [('GradientStrength',1),('ClumpShadingStrength',.38),('WindStrength',.75),('LeafCardScale',.8),('LeafDensity',.45)]:
    actual=mid.get_scalar_parameter_value(key);mr['scalars'][key]=actual;row['passed'] &= abs(actual-expected)<1e-5
   for key,prop in [('GradientDarkColor','gradient_dark_color'),('GradientLightColor','gradient_light_color')]:
    value=mid.get_vector_parameter_value(key);actual=[value.r,value.g,value.b,value.a];mr['colors'][key]=actual;row['passed'] &= all(abs(x-y)<1e-5 for x,y in zip(actual,settings[prop]))
   row['passed'] &= c.get_editor_property('render_custom_depth') and c.get_editor_property('custom_depth_stencil_value')>=16
   row['mids'].append(mr)
  report['actors'].append(row)
 assert all(r['passed'] for r in report['actors']),'Saved actor/MID parameter mismatch'
 report['success']=True
except Exception:report['success']=False;report['errors'].append(traceback.format_exc())
(OUT/'final_palette_validation.json').write_text(json.dumps(report,indent=2))
validation=json.loads((OUT/'validation.json').read_text());validation['checks']['final_palette_saved_reload_and_630_mids']={'passed':report['success'],'detail':{'actor_count':len(report['actors']),'file':'final_palette_validation.json','map_sha256':report.get('map_sha256')}};validation['success']=all(c['passed'] for c in validation['checks'].values());(OUT/'validation.json').write_text(json.dumps(validation,indent=2));u.log('ULTRA_FINAL_PALETTE '+str(report['success']))
