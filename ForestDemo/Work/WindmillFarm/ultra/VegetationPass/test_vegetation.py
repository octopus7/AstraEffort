import unittest,json
from pathlib import Path
P=Path(__file__).resolve().parent
class VegetationEvidence(unittest.TestCase):
    def test_separate_field_and_instancing_saved(self):
        d=json.loads((P/'validation.json').read_text())
        self.assertTrue(d['all_passed'])
        for key in ('corn_separate_field','meadow_population','saved_foliage_counts','wind_materials','vegetation_vertex_colors','paths_clear'):
            self.assertTrue(d['checks'][key],key)
    def test_both_wind_evidence_pairs(self):
        d=json.loads((P/'render_analysis.json').read_text())
        for group in ('corn','meadow'):
            self.assertGreater(d['motion'][group]['changed_pixels_threshold12'],250)
            self.assertGreater(d['motion'][group]['delta_seconds'],1)
        self.assertTrue(d['all_1920x1080'])
        self.assertTrue(d['all_nonblank'])
if __name__=='__main__':unittest.main()
