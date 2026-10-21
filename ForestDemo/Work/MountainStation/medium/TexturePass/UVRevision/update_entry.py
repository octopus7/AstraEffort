import unreal,traceback
try:
 exec(compile(open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision/update_meshes.py',encoding='utf-8-sig').read(),'update_meshes.py','exec'),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision/apply_error.txt','w').write(traceback.format_exc())
finally:unreal.SystemLibrary.quit_editor()

