"""Mechanical, provenance-tracked port of the approved tree and renderer."""
import json,hashlib,shutil,datetime
from pathlib import Path
SOURCE=Path(r'D:/github/extraction_shooter/TunaSweeper')
OUT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
PROJECT=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/ultra/SelfImprovement/ForestDemo')
PLUGIN=PROJECT/'Plugins/ForestUltraTrees';MODULE=PLUGIN/'Source/ForestUltraTrees'
for d in ['Public','Private']: (MODULE/d).mkdir(parents=True,exist_ok=True)
(PLUGIN/'Shaders').mkdir(exist_ok=True)
replacement=[('TunaSweeperAnimeTreeActor','ForestUltraAnimeTreeActor'),('TUNASWEEPER_API','FORESTULTRATREES_API'),('CanopyRimSubsystem','ForestUltraCanopyRimSubsystem'),('CanopyRimViewExtension','ForestUltraCanopyRimViewExtension'),('FCanopyMaskCS','FForestUltraCanopyMaskCS'),('FCanopyCompositePS','FForestUltraCanopyCompositePS'),('CANOPYRIM_API','FORESTULTRATREES_API'),('r.CanopyRim','r.ForestUltra.CanopyRim'),('"/CanopyRim/CanopyRim.usf"','"/ForestUltraCanopyRim/CanopyRim.usf"'),('"Environment/ForestUltraAnimeTreeActor.h"','"ForestUltraAnimeTreeActor.h"')]
pairs=[
 ('Source/TunaSweeper/Public/Environment/TunaSweeperAnimeTreeActor.h',MODULE/'Public/ForestUltraAnimeTreeActor.h'),
 ('Source/TunaSweeper/Private/Environment/TunaSweeperAnimeTreeActor.cpp',MODULE/'Private/ForestUltraAnimeTreeActor.cpp'),
 ('Source/CanopyRim/Public/CanopyRimSubsystem.h',MODULE/'Public/ForestUltraCanopyRimSubsystem.h'),
 ('Source/CanopyRim/Private/CanopyRimSubsystem.cpp',MODULE/'Private/ForestUltraCanopyRimSubsystem.cpp'),
 ('Source/CanopyRim/Private/CanopyRimViewExtension.h',MODULE/'Private/ForestUltraCanopyRimViewExtension.h'),
 ('Source/CanopyRim/Private/CanopyRimViewExtension.cpp',MODULE/'Private/ForestUltraCanopyRimViewExtension.cpp')]
changes=[]
for source,dest in pairs:
 p=SOURCE/source;code=p.read_text(encoding='utf-8-sig')
 for old,new in replacement:code=code.replace(old,new)
 dest.write_text(code,encoding='utf-8')
 changes.append({'source':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'destination':str(dest),'port_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'changes':'Mechanical class/module/include/shader/CVar namespacing only. Algorithms and defaults retained.'})
shader=SOURCE/'Shaders/CanopyRim/CanopyRim.usf';shutil.copy2(shader,PLUGIN/'Shaders/CanopyRim.usf')
(MODULE/'ForestUltraTrees.Build.cs').write_text('''using UnrealBuildTool;
public class ForestUltraTrees : ModuleRules
{
    public ForestUltraTrees(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new[] { "Renderer", "RenderCore", "RHI", "Projects" });
    }
}
''')
(MODULE/'Private/ForestUltraTreesModule.cpp').write_text('''#include "Modules/ModuleManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "ShaderCore.h"

class FForestUltraTreesModule : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
        const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("ForestUltraTrees"));
        check(Plugin.IsValid());
        AddShaderSourceDirectoryMapping(TEXT("/ForestUltraCanopyRim"), FPaths::Combine(Plugin->GetBaseDir(), TEXT("Shaders")));
    }
};
IMPLEMENT_MODULE(FForestUltraTreesModule, ForestUltraTrees)
''')
(PLUGIN/'ForestUltraTrees.uplugin').write_text(json.dumps({'FileVersion':3,'Version':1,'VersionName':'1.0','FriendlyName':'Forest ultra anime tree support','Description':'Feature-preserving namespaced port of the approved TunaSweeper anime tree and shared canopy rim renderer.','Category':'Rendering','CanContainContent':False,'EnabledByDefault':True,'Modules':[{'Name':'ForestUltraTrees','Type':'Runtime','LoadingPhase':'PostConfigInit'}]},indent=2))
config=PROJECT/'Config/DefaultEngine.ini'
text=config.read_text(encoding='utf-8-sig')
text+='\n[/Script/Engine.RendererSettings]\nr.CustomDepth=3\n\n[CoreRedirects]\n+ClassRedirects=(OldName="/Script/TunaSweeper.TunaSweeperAnimeTreeActor",NewName="/Script/ForestUltraTrees.ForestUltraAnimeTreeActor")\n'
config.write_text(text)
(OUT/'native_port_manifest.json').write_text(json.dumps({'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plugin':str(PLUGIN),'source_files':changes,'shader_sha256':hashlib.sha256(shader.read_bytes()).hexdigest(),'necessary_adaptations':['Runtime plugin combines tree actor and renderer modules; native API macro renamed.','Shader mapping uses plugin-relative Shaders instead of source ProjectDir.','Console variable prefix r.ForestUltra.CanopyRim avoids name collisions.','Temporary private ClassRedirect loads source native parent; removed after asset re-save.','r.CustomDepth=3 enables required custom depth/stencil buffer.'],'behavior_changes':[]},indent=2))
print(str(PLUGIN))
