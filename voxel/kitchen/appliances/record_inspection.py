"""Record direct image-tool observations made during this production session."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OBSERVATIONS = {
    'double_door_fridge': 'Both front doors are separated, the two sage pulls are visibly distinct, and the toe plinth and feet read clearly. Full silhouette is in frame; half size preserves all key parts.',
    'range_oven': 'Four burners with cross pan rests, four controls, oven window and raised grip are recognizable. All four burners remain distinct in half size; no framing clipping observed.',
    'microwave': 'Window, vertical grip, rotary control and right-side vent slots are visible. Half size keeps the vent openings and control separation. No clipping observed.',
    'dishwasher': 'The lowered door, wash chamber, two open rack fronts and plates read as an open dishwasher. Racks and chamber remain open at half size. Upper cup openings are not fully visible from this camera and are separately probed in VOX.',
    'range_hood': 'The corrected canopy has a continuous stepped side shell without the original unintended slit. Open chimney, sage lip and front buttons remain visible at both sizes. Underside filter is hidden from this camera and separately probed in VOX.',
    'rice_cooker': 'Closed rounded cooker, front controls, lid band and upright carrying handle are distinct. The handle through-gap survives half size. Stepped curved surfaces are intentional native voxel boundaries.',
    'electric_kettle': 'Open spout mouth, tall loop handle, water gauge and power base are visible. Spout opening and handle loop survive half size; the chunky stepped silhouette is intentional. No clipping observed.',
}
TIMES = {
    ('double_door_fridge', 'large'): '2026-10-25T05:31:47+00:00',
    ('double_door_fridge', 'half'): '2026-10-25T05:31:47+00:00',
    ('range_oven', 'large'): '2026-10-25T05:31:47+00:00',
    ('range_oven', 'half'): '2026-10-25T05:32:43+00:00',
    ('microwave', 'large'): '2026-10-25T05:32:43+00:00',
    ('microwave', 'half'): '2026-10-25T05:32:43+00:00',
    ('dishwasher', 'large'): '2026-10-25T05:32:43+00:00',
    ('dishwasher', 'half'): '2026-10-25T05:32:43+00:00',
    ('range_hood', 'large'): '2026-10-25T05:34:34+00:00',
    ('range_hood', 'half'): '2026-10-25T05:34:34+00:00',
    ('rice_cooker', 'large'): '2026-10-25T05:34:22+00:00',
    ('rice_cooker', 'half'): '2026-10-25T05:34:22+00:00',
    ('electric_kettle', 'large'): '2026-10-25T05:34:22+00:00',
    ('electric_kettle', 'half'): '2026-10-25T05:34:22+00:00',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


records = []
for (asset, variant), stamp in TIMES.items():
    image = ROOT / 'assets' / asset / variant / 'preview.png'
    records.append({'asset': asset, 'variant': variant, 'image': image.relative_to(ROOT).as_posix(),
                    'sha256': sha(image), 'inspected': True, 'inspected_at_utc': stamp,
                    'method': 'Direct functions.view_image inspection of the actual 768px PNG',
                    'observations': OBSERVATIONS[asset], 'blocking_defects': []})
result = {'all_final_previews_directly_inspected': True, 'gui_checks_claimed': False,
          'images': records,
          'contact_sheet': {'image': 'overview_half.png', 'sha256': sha(ROOT / 'overview_half.png'),
                            'inspected_at_utc': '2026-10-25T05:34:54+00:00',
                            'observations': 'All seven half previews and labels are present. Cards, dimensions, cell sizes and footer are readable; no cut-off text or missing image observed.'},
          'one_corrected_visual_defect': 'See visual_fix.json and hood regression logs. The final hood pair was inspected again after rerendering.'}
(ROOT / 'image_inspection.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('Recorded 14 direct final-preview inspections and the contact sheet inspection.')
