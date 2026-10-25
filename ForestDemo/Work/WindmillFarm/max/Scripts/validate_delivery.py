"""Checks actual source/UE/capture deliverables; does not inspect other assignments."""
from pathlib import Path
import argparse, json, sys

ROOT = Path(__file__).resolve().parents[1]

def source_checks():
    failures = []
    manifest_path = ROOT / 'Source/scene_manifest.json'
    if not manifest_path.is_file():
        return ['Missing source scene manifest and exported farm assets.']
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    required = {'Terrain', 'WindmillTower', 'WindmillRotor', 'Farmhouse', 'Barn', 'Wheat', 'Paths', 'Fences', 'Orchard', 'Props'}
    seen = set()
    for asset in data['meshes']:
        seen.add(asset['category'])
        path = ROOT / 'Source/Models' / (asset['name'] + '.fbx')
        if not path.is_file() or path.stat().st_size < 1000:
            failures.append('Missing/empty FBX: ' + asset['name'])
        if asset['vertices'] < 3 or asset['polygons'] < 1 or asset['uv_loops'] != asset['loops']:
            failures.append('Empty geometry or incomplete UVs: ' + asset['name'])
        if not asset['materials']:
            failures.append('No materials: ' + asset['name'])
        if asset['category'] != 'WindmillRotor':
            for i in (0, 1):
                if asset['bounds_min'][i] < -50.05 or asset['bounds_max'][i] > 50.05:
                    failures.append('Geometry outside 100m site: ' + asset['name'])
    if required - seen:
        failures.append('Missing scene categories: ' + ','.join(sorted(required - seen)))
    if data.get('site_dimensions_m') != [100, 100]:
        failures.append('Incorrect site dimensions')
    for texture in data['textures']:
        if not (ROOT / 'Source/Textures' / texture).is_file():
            failures.append('Missing texture: ' + texture)
    fbx_proof=ROOT/'Evidence/fbx_validation.json'
    if not fbx_proof.is_file() or not json.loads(fbx_proof.read_text(encoding='utf-8')).get('passed'):
        failures.append('Actual transformed FBX geometry validation has not passed')
    return failures

def final_checks():
    failures = source_checks()
    proof = ROOT / 'Evidence/saved_scene_validation.json'
    if not proof.is_file():
        failures.append('No saved-scene validation')
    else:
        data = json.loads(proof.read_text(encoding='utf-8'))
        if not data.get('passed'):
            failures.append('Saved-scene validation did not pass')
        if data.get('forbidden_game_dependencies'):
            failures.append('Forbidden /Game dependencies')
    for name in ('overview', 'top_down', 'windmill', 'farm'):
        p = ROOT / 'Screenshots' / (name + '.png')
        if not p.is_file() or p.stat().st_size < 10000:
            failures.append('Missing/empty real capture: ' + name)
    if not (ROOT / 'Screenshots/capture_manifest.json').is_file():
        failures.append('No capture manifest')
    return failures

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['source', 'final'], default='source')
    args = parser.parse_args()
    problems = source_checks() if args.phase == 'source' else final_checks()
    print(json.dumps({'phase': args.phase, 'passed': not problems, 'failures': problems}, indent=2))
    sys.exit(1 if problems else 0)
