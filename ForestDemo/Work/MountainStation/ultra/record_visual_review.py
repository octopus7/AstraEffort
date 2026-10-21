from pathlib import Path
import datetime,json,hashlib,struct
root=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra')
names=['overview','top_down','platform','tracks']
hashes={}
for name in names:
    raw=(root/'Screenshots'/f'{name}.png').read_bytes()
    assert raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',raw[16:24])==(1920,1080)
    hashes[name]=hashlib.sha256(raw).hexdigest()
assert len(set(hashes.values()))==4
record={'inspected_by_author':True,'inspected_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inspection_method':'All four final PNGs opened with view_image and examined by the author.','sha256':hashes,'observations':{'overview':'Full site is framed; station, curved platform/rail, hills, conifers and loop path are visible.','top_down':'Actual overhead view frames the complete 100m square; station/rail/path layout is legible.','platform':'Teal siding, windows, canopy, benches, luggage, planters and lamps are visible; 01 and ALDER PASS text read correctly.','tracks':'Rails and sleepers lead into a masonry arch with readable 1908; the short tunnel interior terminates in a deliberately dark backing.'},'limitations':['The common overview camera presents the tunnel obliquely; the tracks detail supplies the frontal view.','Some paths have angular seams and the distant terrain is sparsely detailed.','The tunnel and canopy shadows are deep; interiors are visual shells.'],'comparison_images_have_no_editor_overlay':True,'generated_scene_imagery':False}
(root/'visual_inspection.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
