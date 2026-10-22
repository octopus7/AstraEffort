"""Read-only PNG capture analysis; writes only Validation/image_quality.json.

Run only after all captures and capture_manifest.json finish being written:
  python -B analyze_captures.py

Uses the Python standard library. It never generates, edits or substitutes scene
images. Temporal deltas are numerical evidence, not certification of animation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time
import zlib


ROOT = Path(__file__).resolve().parent
NAMES = ("overview", "top_down", "village_path", "hot_spring",
         "hot_spring_timed_04s", "hot_spring_timed_08s")
REGIONS = {
    "water": (950, 620, 1200, 680),
    "vapor_over_grass": (850, 420, 1200, 510),
    "static_grass_control": (1500, 420, 1700, 500),
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def inside_root(path):
    path = path.resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Path must remain in assigned Work directory: {path}")
    return path


def decode_png(path):
    """Decode 8-bit grayscale/RGB/GA/RGBA PNG, validating every chunk CRC."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG signature")
    pos, compressed, header, saw_end = 8, bytearray(), None, False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("Truncated PNG chunk")
        size = struct.unpack(">I", data[pos:pos+4])[0]
        if pos + 12 + size > len(data):
            raise ValueError("Truncated PNG payload")
        kind, body = data[pos+4:pos+8], data[pos+8:pos+8+size]
        expected = struct.unpack(">I", data[pos+8+size:pos+12+size])[0]
        if (zlib.crc32(kind+body) & 0xffffffff) != expected:
            raise ValueError(f"PNG CRC mismatch: {kind!r}")
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            compressed.extend(body)
        elif kind == b"IEND":
            saw_end = True
            break
        pos += size + 12
    if not header or not saw_end:
        raise ValueError("Missing IHDR or IEND")
    width, height, depth, color_type, compression, filtering, interlace = header
    if depth != 8 or color_type not in (0, 2, 4, 6):
        raise ValueError(f"Unsupported PNG format: depth={depth}, color={color_type}")
    if compression or filtering or interlace:
        raise ValueError("Unsupported compressed/filter/interlace method")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    stride = width * channels
    raw = zlib.decompress(compressed)
    if len(raw) != height * (stride+1):
        raise ValueError("Unexpected decompressed PNG byte count")
    previous = bytearray(stride)
    rows, filters = [], Counter()
    for y in range(height):
        method = raw[y*(stride+1)]
        filters[method] += 1
        row = bytearray(raw[y*(stride+1)+1:(y+1)*(stride+1)])
        if method not in (0, 1, 2, 3, 4):
            raise ValueError(f"Invalid PNG filter {method}")
        if method:
            for i in range(stride):
                left = row[i-channels] if i >= channels else 0
                above = previous[i]
                corner = previous[i-channels] if i >= channels else 0
                if method == 1:
                    predictor = left
                elif method == 2:
                    predictor = above
                elif method == 3:
                    predictor = (left+above)//2
                else:
                    p = left+above-corner
                    pa, pb, pc = abs(p-left), abs(p-above), abs(p-corner)
                    predictor = left if pa <= pb and pa <= pc else above if pb <= pc else corner
                row[i] = (row[i]+predictor) & 255
        rows.append(row)
        previous = row
    pixels = b"".join(rows)
    return dict(width=width, height=height, channels=channels,
                color_type=color_type, bit_depth=depth, pixels=pixels,
                sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
                crc_valid=True, png_row_filters=dict(filters))


def image_stats(image):
    pixels, channels = image["pixels"], image["channels"]
    count = image["width"] * image["height"]
    rgb_channels = (0, 1, 2) if channels in (3, 4) else (0,)
    statistics = []
    for channel in rgb_channels:
        hist = Counter(pixels[channel::channels])
        mean = sum(value*n for value, n in hist.items()) / count
        variance = sum((value-mean)**2*n for value, n in hist.items()) / count
        entropy = -sum((n/count)*math.log2(n/count) for n in hist.values())
        statistics.append(dict(minimum=min(hist), maximum=max(hist),
                               mean=round(mean, 6), stdev=round(math.sqrt(variance), 6),
                               entropy_bits=round(entropy, 6), distinct_levels=len(hist)))
    # Spatially spread samples supplement channel-range and variance checks.
    sampled = set()
    for y in range(0, image["height"], 17):
        for x in range(0, image["width"], 17):
            offset=(y*image["width"]+x)*channels
            sampled.add(tuple(pixels[offset+c] for c in rgb_channels))
    finite = all(math.isfinite(s[k]) for s in statistics for k in ("mean", "stdev", "entropy_bits"))
    nonblank = (max(s["maximum"]-s["minimum"] for s in statistics) > 8
                and max(s["stdev"] for s in statistics) > 2
                and len(sampled) > 16)
    return dict(rgb_channel_statistics=statistics,
                spatially_sampled_distinct_colors=len(sampled),
                finite=finite, value_range_valid=all(0 <= s["minimum"] <= s["maximum"] <= 255 for s in statistics),
                nonblank=nonblank,
                nonblank_criterion="RGB channel range > 8, channel stdev > 2, and > 16 distinct sampled colors")


def quantile_hist(histogram, fraction):
    target = fraction*(sum(histogram)-1)
    count = 0
    for value, n in enumerate(histogram):
        count += n
        if count > target:
            return value
    return 255


def region_delta(before, after, rectangle):
    x0, y0, x1, y1 = rectangle
    assert (before["width"], before["height"]) == (after["width"], after["height"])
    assert 0 <= x0 < x1 <= before["width"] and 0 <= y0 < y1 <= before["height"]
    assert before["channels"] in (3, 4) and after["channels"] in (3, 4)
    a, b = before["pixels"], after["pixels"]
    ca, cb, width = before["channels"], after["channels"], before["width"]
    hist, channel_sum, signed_sum = [0]*256, 0, 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            ia, ib = (y*width+x)*ca, (y*width+x)*cb
            differences = [b[ib+c]-a[ia+c] for c in range(3)]
            absolute = [abs(d) for d in differences]
            channel_sum += sum(absolute)
            signed_sum += sum(differences)
            hist[max(absolute)] += 1
    count = (x1-x0)*(y1-y0)
    return dict(bounds_px=[x0, y0, x1, y1], pixel_count=count,
                mean_absolute_rgb_delta=round(channel_sum/(count*3), 6),
                mean_signed_rgb_delta=round(signed_sum/(count*3), 6),
                maximum_rgb_delta=max(i for i,n in enumerate(hist) if n),
                pixel_max_delta_p95=quantile_hist(hist, .95),
                pixel_max_delta_p99=quantile_hist(hist, .99),
                pixel_max_delta_p999=quantile_hist(hist, .999),
                fraction_pixels_max_delta_gt1=round(sum(hist[2:])/count, 6),
                fraction_pixels_max_delta_gt3=round(sum(hist[4:])/count, 6),
                pixel_max_delta_histogram=hist)


def run(args):
    started, monotonic_start = utc(), time.monotonic()
    folder = inside_root(Path(args.screenshots))
    manifest_path = inside_root(Path(args.manifest)) if args.manifest else folder/"capture_manifest.json"
    output = inside_root(Path(args.output))
    report = dict(theme="HillsideOnsen", effort="ultra", started_at_utc=started,
                  screenshots=str(folder), capture_manifest=str(manifest_path),
                  generator=str(Path(__file__).resolve()),
                  analysis_scope="PNG integrity and numeric image/temporal statistics only; no image edits or generation",
                  expected_names=list(NAMES), expected_resolution=[1920, 1080],
                  images={}, temporal_comparisons={}, errors=[], warnings=[],
                  animation_certified=False, visual_review_required=True,
                  limitations=[
                      "Temporal hashes alone do not establish visible or correct animation.",
                      "Local changes may include temporal rendering noise, moving geometry, shadows or mixed effects.",
                      "Water ROI may also contain projected vapor. Vapor ROI is a fixed above-pool screen region.",
                      "Control comparison uses current fixed camera framing; visual inspection must confirm ROI suitability.",
                      "A local maximum above control is a numerical detection threshold, not an animation quality pass."])
    images = {}
    views = {}
    manifest = None
    try:
        manifest_bytes=manifest_path.read_bytes()
        report["capture_manifest_sha256"]=hashlib.sha256(manifest_bytes).hexdigest()
        manifest=json.loads(manifest_bytes)
        views={view["name"]:view for view in manifest.get("views", [])}
    except Exception as error:
        report["errors"].append(f"Manifest: {type(error).__name__}: {error}")
    for name in NAMES:
        path=folder/(name+".png")
        entry=dict(path=str(path))
        try:
            image=decode_png(path)
            stats=image_stats(image)
            entry.update({key:value for key,value in image.items() if key != "pixels"})
            entry.update(stats)
            expected=views.get(name, {})
            entry["manifest_sha256"]=expected.get("sha256")
            entry["manifest_hash_matches"]=image["sha256"] == expected.get("sha256")
            entry["manifest_filename_matches"]=expected.get("file") == path.name
            entry["resolution_matches"]=image["width"] == 1920 and image["height"] == 1080
            entry["integrity_and_nonblank_pass"]=all(entry[k] for k in (
                "crc_valid", "manifest_hash_matches", "manifest_filename_matches", "resolution_matches",
                "finite", "value_range_valid", "nonblank"))
            if not entry["integrity_and_nonblank_pass"]:
                report["errors"].append(f"{name}: one or more integrity, hash, resolution or nonblank checks failed")
            images[name]=image
        except Exception as error:
            entry["error"]=f"{type(error).__name__}: {error}"
            entry["integrity_and_nonblank_pass"]=False
            report["errors"].append(f"{name}: {entry['error']}")
        report["images"][name]=entry
    if "hot_spring" in images:
        for name in ("hot_spring_timed_04s", "hot_spring_timed_08s"):
            if name not in images:
                continue
            try:
                stats={key:region_delta(images["hot_spring"], images[name], rect)
                       for key,rect in REGIONS.items()}
                control=stats["static_grass_control"]
                control_max=control["maximum_rgb_delta"]
                for region in ("water", "vapor_over_grass"):
                    value=stats[region]
                    value["local_max_exceeds_control_max"]=value["maximum_rgb_delta"] > control_max
                    value["control_max_threshold"]=control_max
                    hist=value["pixel_max_delta_histogram"]
                    value["fraction_pixels_exceed_control_max"]=round(sum(hist[control_max+1:])/value["pixel_count"], 6)
                    value["absolute_mean_delta_minus_control"]=round(value["mean_absolute_rgb_delta"]-control["mean_absolute_rgb_delta"], 6)
                base_view, after_view=views.get("hot_spring", {}), views.get(name, {})
                elapsed=None
                if isinstance(base_view.get("game_seconds"), (int,float)) and isinstance(after_view.get("game_seconds"), (int,float)):
                    elapsed=after_view["game_seconds"]-base_view["game_seconds"]
                camera_matches=base_view.get("camera") is not None and base_view.get("camera") == after_view.get("camera")
                report["temporal_comparisons"][name]=dict(
                    baseline="hot_spring", actual_game_seconds_delta=elapsed,
                    same_manifest_camera=camera_matches, regions=stats,
                    interpretation="Numeric local changes only; root must visually inspect actual captures")
                if not camera_matches:
                    report["warnings"].append(f"{name}: manifest cameras do not match; ROI temporal comparisons are not isolated")
                for region in ("water", "vapor_over_grass"):
                    if not stats[region]["local_max_exceeds_control_max"]:
                        report["warnings"].append(f"{name}/{region}: local maximum does not exceed static control maximum")
            except Exception as error:
                report["errors"].append(f"Temporal {name}: {type(error).__name__}: {error}")
    report["all_six_integrity_and_nonblank_checks_pass"]=len(images) == 6 and all(
        report["images"][name].get("integrity_and_nonblank_pass", False) for name in NAMES)
    report["finished_at_utc"]=utc()
    report["elapsed_seconds"]=round(time.monotonic()-monotonic_start, 3)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("Wrote:", output)
    print("Six PNG integrity/nonblank:", report["all_six_integrity_and_nonblank_checks_pass"])
    for name, comparison in report["temporal_comparisons"].items():
        print(name, "game seconds:", comparison["actual_game_seconds_delta"])
        for key, value in comparison["regions"].items():
            print(" ", key, "mean absolute RGB delta:", value["mean_absolute_rgb_delta"],
                  "max:", value["maximum_rgb_delta"], "exceeds control:", value.get("local_max_exceeds_control_max"))
    for warning in report["warnings"]:
        print("WARNING:", warning)
    for error in report["errors"]:
        print("ERROR:", error)
    print("Animation is not certified by this script; actual-image visual review is required.")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshots", default=str(ROOT/"Screenshots"))
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--output", default=str(ROOT/"Validation/image_quality.json"))
    sys.exit(run(parser.parse_args()))
