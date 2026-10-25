import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class DeliveryContract(unittest.TestCase):
    def test_saved_map_exists(self):
        p = ROOT.parents[2] / 'Saved/Workers/WindmillFarm/ultra/Project/Content/Maps/WindmillFarm_ultra.umap'
        self.assertTrue(p.is_file(), 'New private WindmillFarm map has not been authored yet')

    def test_actual_captures_and_manifest_exist(self):
        for name in ('overview','top_down','windmill','farm_detail'):
            self.assertTrue((ROOT/'Screenshots'/f'{name}.png').is_file(), name)
        self.assertTrue((ROOT/'Screenshots/capture_manifest.json').is_file())

    def test_fresh_validation_proves_scope_and_runtime(self):
        p=ROOT/'validation.json'
        self.assertTrue(p.is_file(), 'Fresh Unreal validation has not run')
        d=json.loads(p.read_text())
        for key in ('saved_map_reload','owned_dependencies','non_world_partition','no_external_packages',
                    'footprint_100m','materials_and_uvs','pie_possession','ground_collision','building_collision',
                    'prop_contact_and_clearance','pawn_sweep_blocks','pawn_can_move','pie_ended'):
            self.assertTrue(d['checks'][key], key)
        self.assertTrue(d['all_passed'])

if __name__ == '__main__': unittest.main()
