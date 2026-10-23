import bpy,numpy as np,json,time
from pathlib import Path
from datetime import datetime,timezone
r=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max');t=time.time()
im=bpy.data.images.load(str(r/'Source'/'T_Steam.png'));w,h=im.size
p=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(p);p=p.reshape(h,w,4)
u=np.arange(w,dtype=np.float32)/(w-1);p[:,:,3]*=np.maximum(0,np.sin(np.pi*u))[None,:]**1.3
p[:,0,3]=0;p[:,-1,3]=0;p[0,:,3]=0;p[-1,:,3]=0
im.pixels.foreach_set(p.ravel());im.filepath_raw=str(r/'Source'/'T_Steam.png');im.file_format='PNG';im.save()
(r/'Validation'/'steam_texture_refinement.json').write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'seconds':time.time()-t,'change':'Force all alpha boundaries to zero and apply horizontal sine feather, eliminating faint card edges','alpha_edges_all_zero':True},indent=2),encoding='utf8')
