import unreal, traceback
try:
    path='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/capture_ue.py'
    exec(compile(open(path,encoding='utf-8').read(),path,'exec'),globals())
except Exception:
    open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/capture_error.txt','w').write(traceback.format_exc())
    unreal.SystemLibrary.quit_editor()
