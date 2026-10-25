import json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class SceneEvidence(unittest.TestCase):
    def test_saved_scene_and_runtime(self):
        data=json.loads((P/'validation.json').read_text())
        for key in ('saved_map_reload','owned_dependencies','non_world_partition','no_external_packages','footprint_100m','bridge_contacts','building_grounding','material_graphs','pie_possession','ground_collision','bridge_collision','pawn_can_move','pie_ended'):
            self.assertTrue(data['checks'][key],key)
        self.assertTrue(data['all_passed'])
    def test_actual_rain_water_motion(self):
        data=json.loads((P/'render_analysis.json').read_text())
        self.assertTrue(data['all_1920x1080'])
        self.assertTrue(data['all_nonblank'])
        for group in ('canal','rainy_street','water_only','puddle'):
            self.assertGreater(data['motion'][group]['delta_seconds'],1)
            self.assertGreater(data['motion'][group]['changed_pixels_threshold12'],500)
        self.assertTrue(data['motion']['water_only']['rain_hidden'])
        self.assertTrue(data['motion']['puddle']['rain_hidden'])
if __name__=='__main__':unittest.main()
