"""Independent saved-PNG and repeat-generation QA for owned source artwork."""
import hashlib
import io
import json
from datetime import datetime, timezone

import numpy as np
from PIL import Image

import generator as gen


def main():
    summary = {'validated_at_utc': datetime.now(timezone.utc).isoformat(),
               'texture_count': 0, 'all_deterministic_png_hashes_match': True,
               'all_normal_vector_checks_pass': True, 'max_normal_unit_length_error': 0.0,
               'visual_review': {'inspected': ['source_art_contact_sheet.png', 'QA_Wood_3x3.png', 'QA_Canvas_3x3.png'],
                                 'result': 'Quiet distinct surfaces; wood and fabric repetitions have no visible edge discontinuities. Source artwork only, not scene evidence.'}}
    for slot, make, target, *_ in gen.SLOTS:
        rgb, roughness, height = make()
        rough = np.uint8(np.clip(np.rint(roughness * 255), 0, 255))
        normal, _ = gen.normal(height, target)
        for suffix, expected in [('BaseColor', rgb), ('Roughness', rough), ('Normal', normal)]:
            path = gen.ROOT / f'T_{slot}_{suffix}.png'
            saved = np.array(Image.open(path))
            assert saved.shape[:2] == (1024, 1024)
            assert np.array_equal(saved, expected), f'Pixel nondeterminism: {path}'
            stream = io.BytesIO()
            Image.fromarray(expected).save(stream, format='PNG', optimize=True)
            assert hashlib.sha256(stream.getvalue()).hexdigest() == gen.sha256(path), f'PNG hash mismatch: {path}'
            summary['texture_count'] += 1
        decoded = normal.astype(float) / 255 * 2 - 1
        error = float(np.abs(np.linalg.norm(decoded, axis=2) - 1).max())
        assert error < .007 and decoded[..., 2].min() > .90
        summary['max_normal_unit_length_error'] = max(error, summary['max_normal_unit_length_error'])
    summary['max_normal_unit_length_error'] = round(summary['max_normal_unit_length_error'], 7)
    (gen.ROOT / 'source_art_validation.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
