import unreal,traceback
try:
 p='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/verify_movement.py'
 exec(compile(open(p,encoding='utf-8').read(),p,'exec'),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/movement_verify_error.txt','w').write(traceback.format_exc())
 unreal.SystemLibrary.quit_editor()
