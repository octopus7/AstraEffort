using UnrealBuildTool;
public class ForestUltraTrees : ModuleRules
{
    public ForestUltraTrees(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new[] { "Renderer", "RenderCore", "RHI", "Projects" });
    }
}
