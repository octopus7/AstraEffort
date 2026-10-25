"""Record observations made with the image-viewing tool; this does not render images."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parent
NOTES={
    'stand_mixer':{
        'large':'Full mixer fits the frame. Cream-front sage head, column, open metal bowl, right bowl-handle hole and working gap around the whisk are visible. Controls and lever remain separate.',
        'half':'Same framing and silhouette. Bowl cavity and right handle opening remain visible. Whisk wires merge into a coarser attachment, consistent with the stated small-detail simplification.',
    },
    'espresso_machine':{
        'large':'Cream gauge/control fascia, sage shell, cup bay, hollow cup, steam wand, portafilter grip and slotted tray are legible. Upper warming rail and side opaque reservoir are fully within frame.',
        'half':'Main controls, upper rail, cup bay and tray bars survive reduction. The cup handle is small in this projection; the native loop is independently probed. Portafilter and wand remain distinct.',
    },
    'toaster':{
        'large':'Two long dark slots are clear, with one raised slice. Empty front slot, lift lever, browning dial, two front buttons and crumb tray are visible. Rounded cream silhouette reads as a toaster.',
        'half':'The front slot remains visibly open and the bread, lever and dial remain recognizable. Corner steps become broader. No clipping or unintended closure observed.',
    },
    'blender':{
        'large':'Opaque blue-gray tapered jug, lid/knob, front graduation dashes, tall cream handle loop and sage motor base read clearly. The glass appearance matches the intentionally opaque palette.',
        'half':'Jug taper, open handle, lid and motor control remain distinct. Large stepped bands replace fine contour steps without changing the recognizable silhouette.',
    },
    'stock_pot':{
        'large':'Final corrected preview: open lined bowl and cream handle loops remain clear; the vessel wall is restored where the grip cutouts meet it. Small dark interior attachment lugs are visible. No crop.',
        'half':'Final corrected preview: the visible side wall below the right handle is continuous, while both grip loops and the deep bowl remain open. Broader wall steps are expected native reduction.',
    },
    'frying_pan':{
        'large':'Open nonstick interior, metal rim, attached compact grip with oak inset and hanging hole are visible. The whole skillet fits the frame and remains separate from its temporary studio floor.',
        'half':'Bowl floor and open cavity remain clear; hanging hole and neck attachment survive. Compact grip and stepped rim are readable at the common camera.',
    },
    'cutting_board_knife':{
        'large':'Oak board, juice groove, open hanging tab, pointed steel blade and riveted grip are visible. The blade rests on the board, with no model clipping. Grain accents are restrained.',
        'half':'Knife blade/handle, broad board seams, juice channel and hanging hole survive. Some fine decorative grain marks disappear in the reduction; functional parts remain readable.',
    },
}
records=[]
for slug,variants in NOTES.items():
    for variant,note in variants.items():
        path=ROOT/'assets'/slug/variant/'preview.png'
        records.append({'asset':slug,'variant':variant,'path':path.relative_to(ROOT).as_posix(),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'inspected':True,
                        'tool':'view_image','observations':note,'unresolved_defects':[]})
result={'complete':True,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'method':'Each of the fourteen final PNG files was opened individually with view_image; both corrected pot PNGs were opened again after their rerender.',
        'contact_sheet_inspected':True,
        'contact_sheet_observations':'All seven actual half previews are shown with correct English labels and native grid/occupancy captions. Header, cards and footer are legible and unclipped.',
        'images':records,
        'resolved_findings':[{'asset':'stock_pot','finding':'Handle opening carve overlapped vessel wall, creating small square side punctures.','resolution':'Preserved original pot shell during handle carving, added two saved-data wall-presence probes, regenerated and rerendered both sizes, then re-inspected.','before_regression_result':'Failed: stock_pot/large left_wall_closed_below_handle palette index 0','after_native_validation':'66 saved-native feature probes passed'}],
        'limitations':['One standardized three-quarter camera per variant.','Fine whisk and grain details simplify at half resolution; open functional spaces are checked in native data.','No GUI inspection is claimed.']}
(ROOT/'visual_inspection.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('VISUAL_INSPECTION_RECORDED',len(records))
