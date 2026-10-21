import unreal as u,traceback
try:
 exec(compile(open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/audit_ue.py',encoding='utf-8-sig').read(),'audit_ue.py','exec'),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/audit_error.txt','w').write(traceback.format_exc())
 u.SystemLibrary.quit_editor()
