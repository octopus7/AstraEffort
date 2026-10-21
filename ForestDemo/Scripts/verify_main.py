"""Read-only verification of the saved main level in an editor commandlet."""
import unreal

level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level_editor.load_level("/Game/Maps/main"), "main failed to load"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
loggers = [a for a in actors if a.get_class().get_name() == "ScreenDebugLogger"]
assert len(loggers) == 1, "Expected exactly one ScreenDebugLogger"
assert any(isinstance(a, unreal.PlayerStart) for a in actors), "Missing PlayerStart"
assert any(isinstance(a, unreal.StaticMeshActor) for a in actors), "Missing template floor"
assert any(isinstance(a, unreal.DirectionalLight) for a in actors), "Missing template lighting"
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(["/Game"], force_rescan=True)
maps = [a.package_name for a in registry.get_assets_by_path("/Game", recursive=True)
        if a.asset_class_path.asset_name == "World"]
assert [str(m) for m in maps] == ["/Game/Maps/main"], f"Unexpected maps: {maps}"
unreal.log("FORESTDEMO VERIFIED: main is the only map; Basic template actors and one logger present")
