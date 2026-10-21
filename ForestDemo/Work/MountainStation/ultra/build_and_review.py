import unreal, traceback, json
root=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
try:
    exec(compile(open(root+'/build_unreal.py').read(),root+'/build_unreal.py','exec'),globals())
    exec(compile(open(root+'/run_review.py').read(),root+'/run_review.py','exec'),globals())
except Exception:
    with open(root+'/build_review_error.json','w') as f:json.dump({'traceback':traceback.format_exc()},f,indent=2)
    unreal.SystemLibrary.quit_editor()
