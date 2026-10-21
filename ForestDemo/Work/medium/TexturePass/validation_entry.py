import unreal as u,traceback
try:exec(open('D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass/validate_capture.py').read(),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass/validation_error.txt','w').write(traceback.format_exc());u.SystemLibrary.quit_editor()
