"""Finite correction pass for defects recorded by support_check_initial.json."""
from pathlib import Path
import sys,shutil,json,time
sys.dont_write_bytecode=True
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from preview_pipeline import native_build,render,dump,utc
from validate import validate

started=utc();t=time.perf_counter()
initial=ROOT/'logs'/'initial_capture_manifest.json'
if not initial.exists():shutil.copyfile(ROOT/'capture_manifest.json',initial)
affected=['kitchen_island','dish_cabinet','dish_drying_rack','knife_block']
for slug in affected:native_build(slug)
validate(native_only=True)
for slug in affected:render(slug)
dump(ROOT/'logs'/'support_repair_timing.json',{
    'started_at_utc':started,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-t,
    'affected_models':affected,'rerender_count':8,
    'reason':'Observed disconnected native supports; initial evidence in support_check_initial.json'})
