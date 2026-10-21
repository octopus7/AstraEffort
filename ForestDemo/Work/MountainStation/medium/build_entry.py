import unreal, traceback
try:
    base='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/'
    path=base+'build_ue.py'
    exec(compile(open(path,encoding='utf-8').read(),path,'exec'),globals())
    path=base+'capture_ue.py'
    exec(compile(open(path,encoding='utf-8').read(),path,'exec'),globals())
except Exception:
    open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/build_error.txt','w').write(traceback.format_exc())
    unreal.SystemLibrary.quit_editor()
