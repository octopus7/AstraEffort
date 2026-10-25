"""Compose the completed 81-model HALF contact sheet without changing any source.

Run with Blender's bundled Python on Windows. Uses built-in System.Drawing;
no Pillow, package installation, Blender session, or model source is needed.
Only overview_half_all.png and overview_half_all.json are written.
"""
from __future__ import annotations

import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PNG = ROOT / "overview_half_all.png"
JSON = ROOT / "overview_half_all.json"
ROWS = [
    ("farm", "forestry"),
    ("factory", "construction"),
    ("antarctic", "fire_rescue"),
    ("harbor", "bakery"),
    ("mine", "airfield"),
    ("desert", "recycling"),
    ("mountain_railway", "geothermal"),
    ("spaceport", "canal"),
    ("underwater", "camping"),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as source:
        header = source.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", header[16:24])


POWERSHELL = r'''
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$p = [Console]::In.ReadToEnd() | ConvertFrom-Json
$bitmap = New-Object System.Drawing.Bitmap 3664,4720
$g = [System.Drawing.Graphics]::FromImage($bitmap)
$g.Clear([System.Drawing.ColorTranslator]::FromHtml('#14202E'))
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$fontCache = @{}
$brushCache = @{}
function Font($size, $bold = $false) {
    $key = "$size/$bold"
    if (-not $fontCache.ContainsKey($key)) {
        $style = [System.Drawing.FontStyle]::Regular
        if ($bold) { $style = [System.Drawing.FontStyle]::Bold }
        $fontCache[$key] = New-Object System.Drawing.Font('Malgun Gothic',[single]$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
    }
    return $fontCache[$key]
}
function Brush($hex) {
    if (-not $brushCache.ContainsKey($hex)) {
        $brushCache[$hex] = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml($hex))
    }
    return $brushCache[$hex]
}
function Text($value, $x, $y, $size, $color, $bold = $false) {
    $g.DrawString([string]$value,(Font $size $bold),(Brush $color),[single]$x,[single]$y)
}
function Rect($x, $y, $w, $h, $color) {
    $g.FillRectangle((Brush $color),[single]$x,[single]$y,[single]$w,[single]$h)
}
function Wrap($value, $width, $size) {
    $lines = New-Object 'System.Collections.Generic.List[string]'
    $line = ''
    foreach ($word in ($value -split ' ')) {
        $next = ($line + ' ' + $word).Trim()
        if ($g.MeasureString($next,(Font $size)).Width -le $width) {
            $line = $next
        } else {
            if ($line.Length -eq 0) { throw "Single word exceeds label: $value" }
            $lines.Add($line)
            $line = $word
        }
    }
    if ($line.Length -gt 0) { $lines.Add($line) }
    return $lines.ToArray()
}

Text 'VOXEL LIBRARY / SMALL · HALF' 40 22 48 '#F4F7FA' $true
Text '81 models · 18 themes · actual rendered previews' 42 88 26 '#AFC0D1'
Text $p.snapshot_label 40 126 17 '#AFC0D1'
Text 'ALL 81 MODELS ACCEPTED' 2480 38 23 '#9BE0BF' $true
Text 'HALF RESOLUTION · 64' 3110 38 23 '#AFC0D1' $true
Text 'Full frames · uniform 384 × 384 thumbnails · individual files preserved' 2480 87 18 '#AFC0D1'

$results = @()
foreach ($item in $p.items) {
    $x = 40 + 400 * [int]$item.column
    $y = 160 + 504 * [int]$item.row
    Rect $x $y 384 488 '#FFFFFF'
    Rect $x $y 384 36 '#E9EFF5'
    Text $item.theme_display ($x + 11) ($y + 4) 17 '#263A4F' $true
    switch ($item.status) {
        'accepted' { $badge = 'ACCEPTED'; $bg = '#DDEFE6'; $fg = '#225F47' }
        'pending_review' { $badge = 'PENDING'; $bg = '#FFF0CD'; $fg = '#805300' }
        'wip_unverified' { $badge = 'WIP'; $bg = '#EEE4FA'; $fg = '#624196' }
        default { throw 'Unknown status' }
    }
    Rect ($x + 289) ($y + 5) 84 26 $bg
    Text $badge ($x + 298) ($y + 7) 13 $fg $true
    $source = [System.Drawing.Image]::FromFile($item.absolute_path)
    try {
        $destination = New-Object System.Drawing.Rectangle ($x),($y + 36),384,384
        $g.DrawImage($source,$destination,0,0,$source.Width,$source.Height,[System.Drawing.GraphicsUnit]::Pixel)
    } finally { $source.Dispose() }
    $label = ('{0:D2}  ' -f [int]$item.index) + $item.label
    $lines = @(Wrap $label 360 19)
    if ($lines.Count -gt 2) { throw "More than two label lines: $label" }
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($g.MeasureString($lines[$i],(Font 19)).Width -gt 360) { throw "Clipped label: $label" }
        Text $lines[$i] ($x + 10) ($y + 428 + $i * 25) 19 '#213448'
    }
    if ($x + 384 -gt $bitmap.Width -or $y + 488 -gt $bitmap.Height) { throw 'Card outside image' }
    $results += [PSCustomObject]@{
        index = $item.index
        thumbnail_rectangle = @($x,($y + 36),384,384)
        label_lines = $lines
        label_bounds_checked = $true
    }
}

try {
    $bitmap.Save($p.output,[System.Drawing.Imaging.ImageFormat]::Png)
} finally {
    $g.Dispose()
    $bitmap.Dispose()
    foreach ($f in $fontCache.Values) { $f.Dispose() }
    foreach ($b in $brushCache.Values) { $b.Dispose() }
}
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::Write((ConvertTo-Json -InputObject @($results) -Depth 8 -Compress))
'''


def main() -> None:
    started = datetime.now(timezone.utc)
    state_path = ROOT / "EXPANSION_STATE.json"
    manifest_path = ROOT / "delivery_manifest_first39.json"
    state = read_json(state_path)
    manifest = read_json(manifest_path)
    assert set(state["accepted"]) == set(state["units"]), "All expansion units must be accepted first"
    review_paths = [ROOT / "validation" / f"expansion_{theme}_visual_review.json" for theme in state["accepted"]]
    assert all(read_json(path)["accepted"] for path in review_paths)
    accepted_original = {(a["theme"], a["asset"]) for a in manifest["assets"]}
    paths = sorted(
        p
        for pattern in ("*/assets/*/half/preview.png", "*/additions/assets/*/half/preview.png")
        for p in ROOT.glob(pattern)
        if not any(part.startswith(("_", ".")) for part in p.relative_to(ROOT).parts)
    )
    assert len(paths) == len(set(paths)) == 81, "Expected exactly 81 real previews"
    by_theme = {}
    for path in paths:
        theme = path.relative_to(ROOT).parts[0]
        by_theme.setdefault(theme, []).append(path)
    assert set(by_theme) == {theme for row in ROWS for theme in row if theme}
    items = []
    for row, themes in enumerate(ROWS):
        for group, theme in enumerate(themes):
            if theme is None:
                continue
            theme_paths = sorted(by_theme[theme], key=lambda p: p.parent.parent.name)
            assert len(theme_paths) == (5 if group == 0 else 4), theme
            for offset, path in enumerate(theme_paths):
                asset = path.parent.parent.name
                metadata = path.parent / "metadata.json"
                label = read_json(metadata)["label"]
                assert isinstance(label, str) and label.strip(), metadata
                if (theme, asset) in accepted_original or theme in state["accepted"]:
                    status = "accepted"
                else:
                    raise AssertionError(f"Unclassified theme: {theme}")
                items.append({
                    "index": len(items) + 1,
                    "theme": theme,
                    "theme_display": theme.replace("_", " ").title(),
                    "asset": asset,
                    "label": label,
                    "status": status,
                    "row": row,
                    "column": offset + group * 5,
                    "source_path": path.relative_to(REPO).as_posix(),
                    "absolute_path": str(path),
                    "source_dimensions": png_size(path),
                    "sha256_before": digest(path),
                    "metadata_path": metadata.relative_to(REPO).as_posix(),
                    "metadata_sha256_before": digest(metadata),
                })
    counts = dict(Counter(item["status"] for item in items))
    assert counts == {"accepted": 81}, counts
    payload = {
        "output": str(PNG),
        "snapshot_label": "Snapshot " + started.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "items": items,
    }
    encoded = base64.b64encode(POWERSHELL.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        input=json.dumps(payload, ensure_ascii=True),
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    layout = json.loads(result.stdout.lstrip("\ufeff"))
    assert len(layout) == len(items)
    for item, rendered in zip(items, layout):
        assert item["index"] == rendered["index"]
        item.update(rendered)
        path = REPO / item["source_path"]
        metadata = REPO / item["metadata_path"]
        item["sha256_after"] = digest(path)
        item["metadata_sha256_after"] = digest(metadata)
        assert item["sha256_before"] == item["sha256_after"], path
        assert item["metadata_sha256_before"] == item["metadata_sha256_after"], metadata
        del item["absolute_path"]
    dimensions = png_size(PNG)
    assert dimensions == (3664, 4720)
    finished = datetime.now(timezone.utc)
    provenance = {
        "schema_version": 1,
        "description": "One contact sheet of all 81 accepted real SMALL/HALF rendered previews.",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "source_count": len(items),
        "unique_source_count": len({item["source_path"] for item in items}),
        "theme_count": len(by_theme),
        "status_counts": counts,
        "status_basis": "Original 39 preserved models plus all 15 parent-accepted expansion units (six additions and nine new themes).",
        "status_sources": [
            {"path": p.relative_to(REPO).as_posix(), "sha256": digest(p)}
            for p in [manifest_path, *review_paths]
        ],
        "compositor": "Windows System.Drawing, invoked from Python; full-frame high-quality bicubic scaling only",
        "columns": 9,
        "rows": 9,
        "thumbnail_size": [384, 384],
        "exclusions": ["voxel/_tools/smoke/**", "underscore/cache/scratch roots", "all LARGE previews"],
        "source_previews_unchanged": True,
        "source_metadata_unchanged": True,
        "all_labels_fit": all(item["label_bounds_checked"] for item in items),
        "output": {
            "path": PNG.relative_to(REPO).as_posix(),
            "dimensions": dimensions,
            "sha256": digest(PNG),
            "bytes": PNG.stat().st_size,
        },
        "sources": items,
    }
    JSON.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: provenance[k] for k in ("source_count", "theme_count", "status_counts", "source_previews_unchanged", "all_labels_fit", "output")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
