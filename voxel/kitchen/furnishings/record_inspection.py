"""Record observations made by actual image-tool inspection; not an image test."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
OBSERVATIONS={
 'sink_cabinet':{
  'large':'Deep empty basin and stepped metal rim read clearly. Faucet hangs over the bowl. Both projecting door pulls are readable; framing is unclipped.',
  'half':'Basin, faucet clearance and U pulls remain open. Cabinet silhouette and sage/cream distinction remain clear; rounding is visibly coarser.'},
 'kitchen_island':{
  'large':'Oak worktop, four drawer/door fronts and side shelf distinguish the island. Corrected towel-rail hooks meet the side posts; hanging cloth and dish stack are legible.',
  'half':'Storage bays and rail remain open and supported. Main identity is preserved. Thin oak surface seams disappear, an accepted decorative simplification.'},
 'dish_cabinet':{
  'large':'Open hutch shelves and two plate stands are clear. Corrected bowl rests on its shelf. The upper-right mug is partly occluded by the common camera view; no framing crop.',
  'half':'Tall hutch silhouette, open shelves and lower cupboard remain recognizable. Plate/bowl stepping is coarser; upper-right mug remains partly occluded.'},
 'kitchen_cart':{
  'large':'Three visible caster wheels imply the four-wheel cart; native data contains all four. Slatted shelves, towel stack, drawer and raised transport handle are clear.',
  'half':'Casters, two shelf bays and drawer pull stay readable. Small oak inlays simplify, while open storage and transport-handle clearance remain visible.'},
 'dish_drying_rack':{
  'large':'Three separated plates, curved divider loops, hollow utensil cup and tray handle are visible. Added lower crossbar supports plates without filling slots.',
  'half':'Three plates remain separated. Cup cavity, rack spaces and tray handle opening remain readable; plate contours step at the expected lower resolution.'},
 'knife_block':{
  'large':'Three different-height knife handles and metal blades read clearly above the slanted oak block. Unused front slot is visibly hollow; inserted blades now reach hidden slot floors.',
  'half':'Knife silhouettes remain separate and the unused front slot stays open. The sloped block intentionally shows larger native voxel steps.'},
}
records=[]
for slug,variants in OBSERVATIONS.items():
    for variant,note in variants.items():
        p=ROOT/'assets'/slug/variant/'preview.png'
        records.append({'asset':slug,'variant':variant,'image':p.relative_to(ROOT).as_posix(),
            'image_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'passed':True,'observations':note})
result={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'inspection_method':'All 12 delivered images were individually opened with tools.view_image at 768px; corrected variants were reopened after rerender.',
        'inspected_image_count':12,'images':records,'contact_sheet_inspected':True,
        'contact_sheet_observations':'Actual six half previews assembled into a labeled 3x2 sheet. Title and all labels are legible; no image or label clipping.',
        'findings_requiring_further_changes':[]}
(ROOT/'visual_inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Recorded 12 actual image inspections and inspected contact sheet.')
