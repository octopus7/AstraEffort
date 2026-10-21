using UnrealBuildTool;

public class ForestDemoTarget : TargetRules
{
    public ForestDemoTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
        ExtraModuleNames.Add("ForestDemo");
    }
}
