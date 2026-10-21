using UnrealBuildTool;

public class ForestDemoEditorTarget : TargetRules
{
    public ForestDemoEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
        ExtraModuleNames.Add("ForestDemo");
    }
}
