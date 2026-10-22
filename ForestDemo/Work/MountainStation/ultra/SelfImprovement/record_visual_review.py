import datetime,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
manifest=json.loads((R/'Screenshots/after_final/capture_manifest.json').read_text());assert manifest['passed']
notes={
'overview':'Station, platform, freight shed and terrain composition remain; path no longer has the large missing patches; sleepers and the timber crossing read clearly.',
'top_down':'Original layout retained, locally realigned path crosses the rail at the new timber deck; loop path and rounded end remain visible.',
'platform':'Architecture, windows, benches, lamps and platform retain their previous composition. New track sleepers and crossing visible in the distance.',
'tracks':'Sleeper height and rail profile are visible. Final 35/25 lm tunnel fills reveal a little rib structure; the first 900/650 lm capture was too bright and is superseded. A small ceiling light pool and dark tunnel depth remain.',
'path_junction':'Large terrain holes visible in baseline are removed. Edge color blends into the meadow; steep triangulated facets, some floating-looking edge shadows, grid silhouette and existing rocks remain limitations.',
'crossing':'Timber boards visibly bridge the railway with rail grooves and approaching path. Exposed sleeper sides are visible. Close path borders retain a stepped grid outline.'}
record={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'method':'Primary agent inspected all six actual before_fixed PNGs and all six actual after_final PNGs using view_image; no generated scene evidence.','views':notes,'after_png_sha256':{x['name']:x['sha256'] for x in manifest['captures']},'capture_process_exit_code':-1073741819,'exit_limitation':'All six PNGs, successful manifest, and post-capture package hash confirmation were written before engine shutdown. The process later returned Windows access violation after LogExit/closed-log messages. Clean process exit is not claimed. Prior final scene validation review09 exited 0.'}
(R/'visual_review.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
