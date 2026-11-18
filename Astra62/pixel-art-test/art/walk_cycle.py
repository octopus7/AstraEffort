"""One right-facing stride for both blonde elf studies, in source-art pixels.

X tracks where the ankle of a flat boot would be as the ground passes under
the walker. Rolling over its planted ball also moves the actual ankle forward.
Heel and toe pitches are independent angles to the floor, positive toe-down.
Lift measures the gap under the lowest part of the sole.
"""

from typing import NamedTuple


class FootPose(NamedTuple):
    x: float
    heel_deg: float
    toe_deg: float
    lift: float


# Phase, ankle X, hindfoot pitch, forefoot pitch, sole clearance.
_FOOT = (
    (0.000, 579, -17, -22, 0),  # Heel contact, toes still raised.
    (0.080, 544,  -4,  -8, 0),
    (0.160, 505,   0,   0, 0),
    (0.250, 455,   1,   0, 0),  # Weight over the planted foot.
    (0.360, 398,  12,   0, 0),
    (0.435, 353,  28,   0, 0),
    (0.500, 319,  45,   1, 0),  # Heel raised, weight on the ball and toes.
    (0.550, 299,  52,   5, 0),
    (0.600, 287,  53,  26, 15),
    (0.660, 312,  37,  39, 59),
    (0.715, 351,  21,  31, 86),
    (0.750, 390,   9,  20, 88),  # Swing knee folded, toes clear the floor.
    (0.815, 461,  -3,   5, 69),
    (0.870, 516, -11,  -9, 42),
    (0.925, 558, -17, -19, 21),
    (0.965, 584, -21, -24,  6),
)

# Two weight transfers per stride. Positive Y drops the pelvis after contact.
_BODY = ((0.0, 0), (.085, 11), (.155, 7), (.24, -2), (.32, -9), (.405, -7))


def _periodic_pose(keys, phase, period):
    """Smoothstep through extrema, with a monotone tangent between passing keys."""
    phase %= period
    index = next((i - 1 for i, key in enumerate(keys) if key[0] > phase), len(keys) - 1)
    before, left, right, after = (keys[(index + k) % len(keys)] for k in (-1, 0, 1, 2))
    dt0 = (left[0] - before[0]) % period
    dt = (right[0] - left[0]) % period
    dt1 = (after[0] - right[0]) % period
    t = (phase - left[0]) / dt
    ease = t * t * (3 - 2 * t)

    def tangent(a, b):
        return 2 * a * b / (a + b) if a * b > 0 else 0.0

    values = []
    for a, b, c, d in zip(before[1:], left[1:], right[1:], after[1:]):
        slope = (c - b) / dt
        incoming = tangent((b - a) / dt0, slope)
        outgoing = tangent(slope, (d - c) / dt1)
        values.append(b + (c - b) * ease + dt * t * (1 - t) * ((1 - t) * incoming - t * outgoing))
    return values


def sample_foot(phase):
    return FootPose(*_periodic_pose(_FOOT, phase, 1.0))


def body_drop(phase):
    return _periodic_pose(_BODY, phase, .5)[0]
