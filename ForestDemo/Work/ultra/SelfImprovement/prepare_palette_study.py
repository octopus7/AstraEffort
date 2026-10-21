from pathlib import Path
import json
root=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
palettes={
 'sage':{'gradient_dark_color':[.50,.64,.80,1],'gradient_light_color':[.62,.74,.90,1],'gradient_strength':1.0,'clump_shading_strength':.42,'rim_strength':.25,'rim_color':[.45,.65,.50,1],'rim_width_pixels':20.0,'rim_brightness':.9},
 'moss':{'gradient_dark_color':[.42,.61,.82,1],'gradient_light_color':[.55,.70,.90,1],'gradient_strength':1.0,'clump_shading_strength':.38,'rim_strength':.22,'rim_color':[.38,.61,.51,1],'rim_width_pixels':18.0,'rim_brightness':1.0}
}
(root/'palette_candidates.json').write_text(json.dumps(palettes,indent=2))
s=(root/'capture_after.py').read_text().replace("OUT=ROOT/'Screenshots/After'","OUT=ROOT/'Screenshots/PaletteStudy'")
begin=s.index('views=[');end=s.index("manifest={'map'",begin)
s=s[:begin]+'''before=json.loads((ROOT/'Screenshots/Before/capture_manifest.json').read_text())
palettes=json.loads((ROOT/'palette_candidates.json').read_text())
trees=[a for a in actors.get_all_level_actors() if isinstance(a,u.ForestUltraAnimeTreeActor)]
views=[]
for palette in palettes:
 for name in ['tree_detail','overview']:
  view=dict(next(v for v in before['views'] if v['name']==name));view['name']=palette+'_'+name;view['palette']=palette;views.append(view)
''' + s[end:]
begin=s.index(" name=view['name'];cmd(");end=s.index(' loc=u.Vector',begin)
s=s[:begin]+''' cmd('r.ForestUltra.CanopyRim 1');cmd('r.ForestUltra.CanopyRim.Debug 0')
 settings=palettes[view['palette']]
 for a in trees:
  for key,value in settings.items():a.set_editor_property(key,u.LinearColor(*value) if isinstance(value,list) else value)
  a.refresh_tree()
 view['applied_palette']=settings
 sample=trees[0];mid=sample.get_leaf_clumps()[0].get_material(0)
 view['verified_mid_scalars']={k:mid.get_scalar_parameter_value(k) for k in ['GradientStrength','ClumpShadingStrength','WindStrength','LeafCardScale','LeafDensity']}
 view['verified_mid_colors']={k:str(mid.get_vector_parameter_value(k)) for k in ['GradientDarkColor','GradientLightColor']}
''' + s[end:]
s=s.replace("warmup=45 if index==0 else (3 if views[index]['name'] in ['water_t1','tree_wind_t1'] else 8)","warmup=25 if index==0 else 8")
s=s.replace("   if True:\n    import runpy\n    runpy.run_path(str(ROOT/'validate_runtime.py'))\n   else:u.SystemLibrary.quit_editor()","   u.SystemLibrary.quit_editor()")
(root/'palette_study.py').write_text(s)
print('Prepared two parameter-only palette candidates; existing After files untouched.')
