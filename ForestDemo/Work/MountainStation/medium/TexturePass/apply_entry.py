import unreal,traceback
try:
 p='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/apply_textures.py'
 exec(compile(open(p,encoding='utf-8').read(),p,'exec'),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/apply_error.txt','w').write(traceback.format_exc())
finally:unreal.SystemLibrary.quit_editor()
