import unreal,sys,traceback
from pathlib import Path
P=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra');sys.path.insert(0,str(P));import assemble,materials,capture
try:
    assert assemble.LEV.load_level(assemble.MAP)
    actors={a.get_actor_label():a for a in assemble.ACT.get_all_level_actors()}
    actors['OvercastSkyLight'].get_component_by_class(unreal.SkyLightComponent).set_editor_property('intensity',1.2)
    actors['OvercastFill'].get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',.3)
    actors['RainHaze'].get_component_by_class(unreal.ExponentialHeightFogComponent).set_editor_property('fog_density',.0025)
    pp=actors['OvercastExposure'];settings=pp.get_editor_property('settings');settings.set_editor_property('override_ambient_occlusion_intensity',True);settings.set_editor_property('ambient_occlusion_intensity',.85);settings.set_editor_property('override_ambient_occlusion_radius',True);settings.set_editor_property('ambient_occlusion_radius',100);pp.set_editor_property('settings',settings)
    for slot in ('Stone','Timber'):
        m=unreal.load_asset(assemble.ASSET+'/Materials/M_'+slot);p=materials.node(m,unreal.MaterialExpressionWorldPosition);n=materials.node(m,unreal.MaterialExpressionVertexNormalWS)
        uv=materials.custom(m,'float3 a=abs(N);if(a.z>.65)return P.xy/800.;if(a.x>a.y)return float2(P.y,P.z)/800.;return float2(P.x,P.z)/800.;',{'P':p,'N':n},unreal.CustomMaterialOutputType.CMOT_FLOAT2)
        for prop in (unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialProperty.MP_ROUGHNESS,unreal.MaterialProperty.MP_NORMAL):
            sample=unreal.MaterialEditingLibrary.get_material_property_input_node(m,prop);materials.link(uv,'',sample,'UVs')
        materials.save(m)
    assemble.LEV.save_current_level();unreal.EditorAssetLibrary.save_directory(assemble.ASSET,only_if_is_dirty=False,recursive=True)
    capture.start('final',True,True)
except Exception:
    (P/'Execution/final_error.txt').write_text(traceback.format_exc());raise
