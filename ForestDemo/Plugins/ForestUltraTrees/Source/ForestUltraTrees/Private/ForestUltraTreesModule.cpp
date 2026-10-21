#include "Modules/ModuleManager.h"
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
