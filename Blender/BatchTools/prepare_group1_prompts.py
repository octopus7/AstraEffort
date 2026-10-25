from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
state=json.loads((ROOT/'Blender/SET_BATCH_STATE.json').read_text(encoding='utf-8'))
palettes={'Set03':'warm ivory, muted sage green, graphite mechanisms, small operational orange accents','Set04':'warm ivory, muted slate blue, graphite mechanisms, restrained ochre accents','Set05':'warm off-white, deep muted teal, graphite mechanisms, restrained weathered ochre accents'}
subjects={
'street_sweeper':'A compact four-wheel municipal street sweeper. Rounded short cab with broad glazed windshield, a rear cylindrical collection hopper, two visible low circular side brushes on stout arms, and an underbody suction mouth. Useful realistic mechanical construction, thick soft body panels, robust tires. No faces or cartoon eyes.',
'pipe_inspection_robot':'A low articulated pipe-inspection robot made from three short rounded capsule modules linked by stout exposed universal joints, with six small rubber wheels, a single functional forward camera and lamp pod, a rear tether connector and compact cable reel. Its segmented silhouette should clearly show how it bends through service pipes. Industrial tool, not a character.',
'road_maintenance_depot':'A compact road-maintenance garage building with a softened barrel roof, one broad genuinely open vehicle service bay, a smaller glazed side office with its own door, a recessed tool alcove and purposeful roof ventilation. Clear thick structural columns and a shallow actual building foundation; no vehicle, surrounding road or landscape.',
'compact_pump_station':'A small water pump station: low rounded-corner utility building with a curved shallow roof, paired visible volute pump housings under an open service canopy, thick curved pipes joining two side outlets, a valve handwheel and a compact control cabinet. Keep the pumps and plumbing visually understandable; no water scene or terrain.',
'twin_rotor_cargo_drone':'An original unmanned twin-rotor freight drone. Two large protected circular rotor ducts on a stout transverse beam, a rounded central equipment fuselage, a single removable-looking cargo crate in a belly cradle, short landing skids and a small forward navigation sensor. Blunt thick rotor blades and readable load attachment. No cockpit, pilot, weapons or face.',
'airport_cargo_tug':'A squat four-wheel airport freight tug with a rounded enclosed cab, broad dark glazing, short low hood, heavy rear towing coupler, compact warning beacon, thick bumper and sturdy small tires. Original distinct utility silhouette, visible steps and vents; no attached cart or extra vehicles.',
'circular_drone_hangar':'A low circular drone-maintenance hangar with a softly domed segmented roof and a broad open front sector. A thick ring wall, visible radial roof ribs, recessed interior service pad, side maintenance door and small roof exhaust. Empty interior, no drone or detached props, no surrounding airport terrain.',
'low_control_building':'A low two-storey airport logistics control building, with a rounded rectangular base, wide glazed upper control room, restrained shallow roof overhang, a small blunt radar/navigation unit, entry steps and functional utility annex. Keep it clearly low and broad, not a tall control tower; no people or surrounding scenery.',
'catamaran_workboat':'A compact catamaran utility workboat with two clearly separated rounded hulls joined by a broad deck, a small central glazed pilothouse, open rear working deck, stout compact deck crane, winch and safety rails. Functional twin-hull construction fully visible in a dry studio; no water, crew or scenery.',
'underwater_service_robot':'A compact unmanned underwater maintenance ROV: rounded rectangular protective cage, four side thruster pods and two vertical thrusters, central buoyancy housing, one functional camera module, two short articulated front manipulators with blunt grippers, and a rear tether connector. Purposeful industrial robot, not a face or animal.',
'docking_lift_platform':'An independent marine docking lift facility with four stout support towers, paired lifting beams and cables, a clearly empty boat cradle lowered between narrow side service walkways, visible winch housings and low safety rails. Softened industrial forms; no boat, water, seabed or landscape slab.',
'marine_equipment_workshop':'A compact marine-equipment workshop with a rounded barrel roof, two tall open maintenance doors, visible thick portal structure, a small side office with glazing, functional wall ventilation and a modest roof-mounted hoist rail. Empty bays, readable equipment-building purpose, shallow actual foundation only, no surrounding harbor scenery.'
}
common='Use case: stylized-concept.\nAsset type: one original design reference image for one editable rounded 3D game model (ordinary smooth/beveled mesh, NOT voxels).\nStyle: calm, mature-friendly game art; softened rounded silhouette and corners; preserve recognizable functional structure. Not childish, not toy ornamentation.\nComposition: one fully visible isolated object, orthographic front three-quarter view, generous margins, light neutral studio background, soft studio lighting. No turntable, common diorama base, text, labels, logo, watermark, people, hearts, clouds, smileys, character faces or sharp decorative spikes. Keep thick functional details readable and geometrically plausible.\n'
for name in ('Set03','Set04','Set05'):
    model_dir=ROOT/'Blender'/name;ref_dir=ROOT/'REF'/name
    model_dir.mkdir(parents=True,exist_ok=True);ref_dir.mkdir(parents=True,exist_ok=True)
    for folder in (model_dir,ref_dir):
        (folder/'.gitattributes').write_text('** -text\n',encoding='utf-8',newline='\n')
    (model_dir/'.gitignore').write_text('__pycache__/\n*.pyc\n*.blend[0-9]\n*.zip\n',encoding='utf-8',newline='\n')
    task=f'# {name}: {state["sets"][name]["theme"]}\n\nRead ../SET_WORKER_BRIEF.md and ../SET_BATCH_PLAN.md. This set owns only this directory. Main supplies four sequential references in ../../REF/{name}. Review is deferred by user instruction.\n\n'
    for a in state['sets'][name]['assets']:
        prompt=common+'Subject: '+subjects[a['slug']]+'\nColor palette: '+palettes[name]+'.\nMaterials: painted metal, rubber, muted glass and appropriate masonry/roof materials, with simple clean PBR surfaces and restrained seams.\n'
        p=ref_dir/(a['slug']+'.prompt.txt');assert not p.exists(),str(p)
        p.write_text(prompt,encoding='utf-8',newline='\n')
        task+='- `'+a['slug']+'`: '+a['label']+'\n'
    (model_dir/'TASK.md').write_text(task,encoding='utf-8',newline='\n')
print('Prepared 12 separate prompts and three set task roots; no images generated yet.')
