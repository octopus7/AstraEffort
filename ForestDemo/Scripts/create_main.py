"""Run once with UnrealEditor-Cmd -run=pythonscript -script=<this file>."""
import unreal

level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
map_path = "/Game/Maps/main"

if unreal.EditorAssetLibrary.does_asset_exist(map_path):
    raise RuntimeError("main already exists; refusing to overwrite it")

assert level_editor.new_level_from_template(
    map_path, "/Engine/Maps/Templates/Template_Default"
), "Could not create the Basic template level"

logger_class = unreal.load_class(None, "/Script/ForestDemo.ScreenDebugLogger")
assert logger_class, "ScreenDebugLogger module must be built first"
logger = actors.spawn_actor_from_class(logger_class, unreal.Vector(0, 0, 100))
assert logger, "Could not spawn ScreenDebugLogger"
logger.set_actor_label("ScreenDebugLogger")
assert level_editor.save_current_level(), "Could not save main"
unreal.log("FORESTDEMO: main created from Basic template with ScreenDebugLogger")
