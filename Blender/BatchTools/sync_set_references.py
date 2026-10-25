"""Add references beside their sets, preserving both originals and model files."""
from pathlib import Path
import argparse,re,shutil,json
p=argparse.ArgumentParser();p.add_argument('sets',nargs='+');args=p.parse_args()
ROOT=Path(__file__).resolve().parents[2];result={}
for name in args.sets:
    assert re.fullmatch(r'Set\d{2}',name)
    source=ROOT/'REF'/name;set_root=ROOT/'Blender'/name
    assert source.is_dir() and set_root.is_dir()
    target=set_root/'REF';target.mkdir(exist_ok=True)
    count=0
    for original in source.iterdir():
        if not original.is_file() or not (original.suffix in ('.png','.txt','.json') or original.name=='.gitattributes'):continue
        copy=target/original.name
        if copy.exists() and original.name!='generation_manifest.json':
            assert copy.read_bytes()==original.read_bytes(),f'Conflicting local reference: {copy}'
        else:shutil.copy2(original,copy)
        count+=1
    result[name]=count
print(json.dumps({'reference_files_mirrored':result,'originals_preserved':True},indent=2))
