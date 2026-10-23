"""Tie already completed UE02 renders to the exact saved asset bytes."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/SnowyOnsen/max/PrivateOnsen')
W=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cap=W/'Screenshots/capture_manifest.json';cm=json.loads(cap.read_text());earliest=min(datetime.fromisoformat(r['captured_at_utc']) for r in cm['captures']);rows=[]
for p in sorted((P/'Content/SnowyOnsen/max').rglob('*.uasset'))+[P/'Content/Maps/SnowyOnsen_max.umap']:
 modified=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc);assert modified<earliest,(str(p),modified,earliest)
 rows.append({'private':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'last_write_utc':modified.isoformat()})
assert len(rows)==46
data={'at_utc':datetime.now(timezone.utc).isoformat(),'capture_attempt':2,'capture_manifest_sha256':sha(cap),'all_asset_writes_precede_first_capture':True,'first_capture_utc':earliest.isoformat(),'no_asset_mutations_since_ue02':'Only read-only validation/capture helpers changed; material and UV authoring ended in UE02.','files':rows}
(W/'Validation/captured_asset_snapshot.json').write_text(json.dumps(data,indent=2),encoding='utf8');print('Captured asset snapshot:',len(rows),flush=True)
