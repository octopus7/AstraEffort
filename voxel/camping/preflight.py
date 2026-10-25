"""Validate planned native feature clearances before the one export build."""
from pathlib import Path
import json
import numpy as np
from build import make_assets, PALETTE
from functional_probes import check
from voxelkit import reduce_half

root = Path(__file__).resolve().parent
records = []
for asset in make_assets():
    assert max(asset.grid.shape) == 128 and all(n % 2 == 0 for n in asset.grid.shape)
    for variant, grid in [('large', asset.grid), ('half', reduce_half(asset.grid))]:
        checks = check(asset.slug, variant, grid)
        records.append({'asset': asset.slug, 'variant': variant, 'shape': grid.shape, 'occupied_cells': int(np.count_nonzero(grid.data)), 'functional_checks': len(checks)})
print(json.dumps(records, indent=2))
(root / 'source_preflight.json').write_text(json.dumps({'passed': True, 'records': records}, indent=2), encoding='utf-8')
(root / 'palette.json').write_text(json.dumps({'theme': 'camping', 'source': 'Original palette authored for the camping reference only', 'empty_index': 0, 'colors_rgba': [list(p) + ([255] if len(p) == 3 else []) for p in PALETTE]}, indent=2), encoding='utf-8')
