import unreal, traceback
try:
    path='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/runtime_ue.py'
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_medium')
    exec(compile(open(path,encoding='utf-8').read(),path,'exec'),globals())
except Exception:
    open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/runtime_error.txt','w').write(traceback.format_exc())
    unreal.SystemLibrary.quit_editor()
