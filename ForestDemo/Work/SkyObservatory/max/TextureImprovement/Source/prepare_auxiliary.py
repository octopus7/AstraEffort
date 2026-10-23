from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/TextureImprovement')
p=ROOT/'Source/build_texture_pass.py';s=p.read_text(encoding='utf-8');marker='\ntry:\n started=time.time();'
if marker in s:
 head,tail=s.split('\ntry:\n started=time.time();',1)
 block='try:\n started=time.time();'+tail
 s=head+'\ndef run_build():\n'+''.join(' '+line+'\n' for line in block.splitlines())+"\nif __name__=='__main__':run_build()\n"
 p.write_text(s,encoding='utf-8')
p=ROOT/'Source/prepare_capture.py';s=p.read_text(encoding='utf-8');s=s.replace("m['wall_interval_seconds']/=1000;","m['wall_interval_seconds']=m['wall_interval_seconds']/1000 if m['wall_interval_seconds']>1000 else m['wall_interval_seconds'];");p.write_text(s,encoding='utf-8')
print('AUXILIARY_MODULE_PREPARED')
