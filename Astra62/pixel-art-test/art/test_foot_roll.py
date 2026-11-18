"""Check that the blonde elves' delivered soles bend and meet the walking surface."""

from fractions import Fraction
import json
import math
from pathlib import Path
import sys
import unittest

from PIL import Image


ART = Path(__file__).resolve().parent
ASSETS = ART.parent / "assets"
sys.path.insert(0, str(ART / "blonde-pixel"))
from build_sprites import sprite


def pitch(start, end):
    return math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))


def bend(foot):
    return pitch(foot["heel"], foot["ball"]) - pitch(foot["ball"], foot["toe"])


class FootRollTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        illustration = json.loads((ART / "anime/gait-verification.json").read_text("utf8"))
        cls.native_keys = json.loads((ART / "blonde-pixel/pose-keys.json").read_text("utf8"))
        cls.poses = {"anime": illustration["joint_positions_512"], "pixel": {}}
        cls.sheets = {}
        for style, filename in [("anime", "anime-walk-12-hd.png"), ("pixel", "blonde-pixel-walk-12.png")]:
            with Image.open(ASSETS / filename) as sheet:
                cls.sheets[style] = sheet.convert("RGBA")
        for key, nodes in cls.native_keys.items():
            _, cls.poses["pixel"][key] = sprite(nodes, Fraction(key))

    def test_both_styles_use_the_same_joint_keys(self):
        joints = ("hip", "knee", "ankle", "shoulder", "elbow", "wrist")
        self.assertEqual(self.native_keys.keys(), self.poses["anime"].keys())
        for phase, sides in self.native_keys.items():
            for side, nodes in zip(("near", "far"), sides):
                for joint, node in zip(joints, nodes):
                    source = self.poses["anime"][phase][side][joint]
                    for hd, native in zip(source, node):
                        self.assertAlmostEqual(hd / 8, native, delta=.001)

    def test_sole_changes_shape_relative_to_the_heel(self):
        # A boot rotated as one piece has a constant relative angle, even
        # when both the heel and the tip move a long way across the frame.
        for style, poses in self.poses.items():
            for side, flat, push in [("near", "1/4", "1/2"), ("far", "3/4", "0")]:
                with self.subTest(style=style, side=side):
                    self.assertGreater(bend(poses[push][side]) - bend(poses[flat][side]), 25)

    def test_push_off_in_the_exported_pixels(self):
        # At opposite contacts the trailing foot is clear of the other leg.
        # Read the bottom of the actual ink at the heel and across the toe pad.
        for style, sheet in self.sheets.items():
            size = sheet.height
            floor = round(size * 15 / 16) - 1
            for side, frame in [("near", 6), ("far", 0)]:
                with self.subTest(style=style, side=side):
                    foot = self.poses[style][str(Fraction(frame, 12))][side]
                    alpha = sheet.crop((frame * size, 0, (frame + 1) * size, size)).getchannel("A")

                    def bottom(x):
                        column = alpha.crop((x, 0, x + 1, size)).point(lambda a: 255 if a >= 128 else 0)
                        bounds = column.getbbox()
                        self.assertIsNotNone(bounds)
                        return bounds[3] - 1

                    heel_x = round(foot["heel"][0])
                    ball_x = round(foot["ball"][0])
                    toe_x = round(foot["toe"][0])
                    self.assertGreater(toe_x, ball_x)
                    self.assertGreaterEqual(floor - bottom(heel_x), size * .035)
                    pad = [bottom(x) for x in range(ball_x, toe_x + 1)]
                    self.assertGreaterEqual(sum(abs(floor - y) <= max(1, size / 200) for y in pad),
                                            len(pad) / 2)


if __name__ == "__main__":
    unittest.main()
