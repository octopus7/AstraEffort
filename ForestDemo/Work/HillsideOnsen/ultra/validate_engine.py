"""Read-only validation of a freshly loaded HillsideOnsen/ultra saved map.

run_static_validation(world, manifest, output_path) -> JSON-compatible report.
This module never saves or changes actors, assets, meshes, materials or config.
AssetRegistry scans refresh in-memory metadata for only the owned asset root and
the exact owned map file. The caller independently verifies package hashes.
"""

import datetime
import json
import math
from pathlib import Path
import time
import traceback

try:
    import unreal
except ImportError:
    unreal = None

ROOT = "/Game/HillsideOnsen/ultra"
MAP = "/Game/Maps/HillsideOnsen_ultra"
EXPECTED_MESH_COUNT = 18
BOUNDS_TOLERANCE_CM = 1.0
DENSITY_RELATIVE_TOLERANCE = 0.05

API_EVIDENCE = {
    "section_buffers": "Engine/Plugins/Runtime/ProceduralMeshComponent/Source/ProceduralMeshComponent/Public/KismetProceduralMeshLibrary.h:87",
    "section_implementation": "Engine/Plugins/Runtime/ProceduralMeshComponent/Source/ProceduralMeshComponent/Private/KismetProceduralMeshLibrary.cpp:454",
    "build_settings": "Engine/Source/Editor/StaticMeshEditor/Public/StaticMeshEditorSubsystem.h:81",
    "section_collision": "Engine/Source/Editor/StaticMeshEditor/Public/StaticMeshEditorSubsystem.h:387",
    "section_material_slot": "Engine/Source/Editor/StaticMeshEditor/Public/StaticMeshEditorSubsystem.h:466",
    "mesh_sections_materials_bounds": "Engine/Source/Runtime/Engine/Classes/Engine/StaticMesh.h:2177",
    "actor_bounds": "Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h:1613",
    "dependency_options": "Engine/Source/Runtime/AssetRegistry/Public/AssetRegistry/IAssetRegistry.h:143",
    "dependencies": "Engine/Source/Runtime/AssetRegistry/Public/AssetRegistry/IAssetRegistry.h:557",
    "world_partition": "Engine/Source/Runtime/Engine/Classes/GameFramework/WorldSettings.h:515",
    "import_coordinate_flags": "Engine/Source/Editor/UnrealEd/Classes/Factories/FbxAssetImportData.h:42",
    "full_precision_uv": "Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h:2739",
    "line_trace_profile": "Engine/Source/Runtime/Engine/Classes/Kismet/KismetSystemLibrary.h:1524",
    "break_hit_result": "Engine/Source/Runtime/Engine/Classes/Kismet/GameplayStatics.h:1079",
    "material_textures": "Engine/Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h:237",
    "external_packages": "Engine/Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyWrapperObject.cpp:1123",
    "dirty_packages": "Engine/Source/Editor/UnrealEd/Public/FileHelpers.h:136",
}


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def _uv(value):
    return [float(value.x), float(value.y)]


def _path(value):
    return value.get_path_name() if value is not None else None


def _package(value):
    return str(value).split(".", 1)[0]


def allowed_game_package(package):
    return package == MAP or package.startswith(ROOT + "/")


def expected_bounds(meta):
    """Source meters -> world cm; local mesh keeps importer Y reflection."""
    world = [[float(low) * 100.0, float(high) * 100.0] for low, high in meta["bounds_m"]]
    local = [world[0][:], [-world[1][1], -world[1][0]], world[2][:]]
    return world, local


def max_bounds_error(actual, expected):
    return max(abs(actual[i][j] - expected[i][j]) for i in range(3) for j in range(2))


def _bounds(points):
    if not points:
        raise ValueError("Empty vertex buffer")
    return [[min(v[i] for v in points), max(v[i] for v in points)] for i in range(3)]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def triangle_density(vertices, uvs, indices, atlas_pixels):
    """Return px/m from actual triangle area in cm2 and imported UV0 area."""
    a, b, c = [vertices[i] for i in indices]
    ab = [b[i] - a[i] for i in range(3)]
    ac = [c[i] - a[i] for i in range(3)]
    cross = _cross(ab, ac)
    area_cm2 = 0.5 * math.sqrt(sum(v * v for v in cross))
    ta, tb, tc = [uvs[i] for i in indices]
    uv_area = abs((tb[0] - ta[0]) * (tc[1] - ta[1]) - (tb[1] - ta[1]) * (tc[0] - ta[0])) * 0.5
    if area_cm2 <= 1e-8 or uv_area <= 1e-16:
        return None, area_cm2, uv_area
    return float(atlas_pixels) * math.sqrt(uv_area / (area_cm2 / 10000.0)), area_cm2, uv_area


def measure_buffers(vertices, indices, normals, uvs, tangents, atlas_pixels, target):
    """Pure measurement on extracted buffers, with explicit invalid-data counts."""
    n = len(vertices)
    invalid = {"nonfinite_vertices": [], "nonfinite_normals": [], "nonfinite_uvs": [],
               "nonfinite_tangents": [], "invalid_indices": [], "uv_out_of_unit_square": []}
    for name, values in (("vertices", vertices), ("normals", normals), ("uvs", uvs), ("tangents", tangents)):
        invalid["nonfinite_" + name] = [i for i, value in enumerate(values) if not all(math.isfinite(x) for x in value)]
    invalid["invalid_indices"] = [i for i, value in enumerate(indices)
                                  if not isinstance(value, int) or value < 0 or value >= n]
    invalid["uv_out_of_unit_square"] = [i for i, value in enumerate(uvs)
                                        if any(x < -1e-6 or x > 1.0 + 1e-6 for x in value)]
    errors = [name for name, values in invalid.items() if values]
    if n == 0 or len(indices) == 0:
        errors.append("empty_geometry")
    if len(indices) % 3:
        errors.append("index_count_not_multiple_of_three")
    if any(len(values) != n for values in (normals, uvs, tangents)):
        errors.append("attribute_count_mismatch")
    result = {"vertices": n, "indices": len(indices), "triangles": len(indices) // 3,
              "invalid_counts": {name: len(values) for name, values in invalid.items()},
              "invalid_examples": {name: values[:12] for name, values in invalid.items() if values},
              "errors": errors}
    if errors:
        return result
    result["bounds_local_cm"] = _bounds(vertices)
    densities = []
    degenerates = []
    outside = []
    surface_area_m2 = uv_area_total = 0.0
    for offset in range(0, len(indices), 3):
        density, area_cm2, uv_area = triangle_density(vertices, uvs, indices[offset:offset + 3], atlas_pixels)
        surface_area_m2 += area_cm2 / 10000.0
        uv_area_total += uv_area
        if density is None:
            degenerates.append({"triangle": offset // 3, "area_cm2": area_cm2, "uv_area": uv_area})
        else:
            densities.append(density)
            if target is not None and abs(density / float(target) - 1.0) > DENSITY_RELATIVE_TOLERANCE:
                outside.append({"triangle": offset // 3, "density_px_per_m": density})
    densities.sort()
    result.update(surface_area_m2=surface_area_m2, uv_area_sum=uv_area_total,
                  measured_density_px_per_m={"min": densities[0] if densities else None,
                                             "median": densities[len(densities) // 2] if densities else None,
                                             "max": densities[-1] if densities else None},
                  density_target_px_per_m=target,
                  density_relative_tolerance=DENSITY_RELATIVE_TOLERANCE,
                  density_outside_tolerance_count=len(outside), density_outside_examples=outside[:20],
                  degenerate_triangle_count=len(degenerates), degenerate_examples=degenerates[:20])
    if degenerates:
        result["errors"].append("degenerate_geometry_or_uv")
    if outside:
        result["errors"].append("uv_density_outside_target_tolerance")
    if target is None:
        result["density_exception"] = "Steam intentionally repeats full-card alpha UVs; uniform source density was not specified"
    return result


def _check(report, scope, name, ok, observed=None, expected=None):
    record = {"scope": scope, "name": name, "passed": bool(ok)}
    if observed is not None:
        record["observed"] = observed
    if expected is not None:
        record["expected"] = expected
    report["checks"].append(record)
    if not ok:
        report["failures"].append(scope + ": " + name)
    return bool(ok)


def _exception(report, scope):
    report["errors"].append({"scope": scope, "traceback": traceback.format_exc()})


def _safe_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    if isinstance(value, dict):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _dirty_owned():
    packages = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    packages += list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    return sorted({p.get_name() for p in packages if allowed_game_package(p.get_name())})


def _validate_mesh(report, meta, actors, subsystem):
    scope = meta["name"]
    record = {"name": scope, "category": meta["category"], "sections": [], "actors": []}
    report["meshes"].append(record)
    expected_path = ROOT + "/Meshes/" + scope
    mesh = unreal.load_asset(expected_path)
    if not _check(report, scope, "asset_exists", mesh is not None, expected=expected_path):
        return
    record["asset"] = _path(mesh)
    _check(report, scope, "exact_static_mesh_class", isinstance(mesh, unreal.StaticMesh), _path(mesh.get_class()))
    world_bounds, local_bounds = expected_bounds(meta)
    record["expected_world_bounds_cm"] = world_bounds
    record["expected_local_bounds_cm"] = local_bounds
    import_data = mesh.get_editor_property("asset_import_data")
    convert_scene = bool(import_data.get_editor_property("convert_scene"))
    convert_unit = bool(import_data.get_editor_property("convert_scene_unit"))
    _check(report, scope, "import_convert_scene_false", not convert_scene, convert_scene, False)
    _check(report, scope, "import_convert_scene_unit_true", convert_unit, convert_unit, True)
    lods = int(mesh.get_num_lods())
    _check(report, scope, "one_authored_lod", lods == 1, lods, 1)
    collision_complexity = subsystem.get_collision_complexity(mesh)
    _check(report, scope, "complex_as_simple_collision", collision_complexity == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE,
           str(collision_complexity), "CTF_USE_COMPLEX_AS_SIMPLE")
    assigned = [a for a in actors if isinstance(a, unreal.StaticMeshActor)
                and a.static_mesh_component.get_editor_property("static_mesh") == mesh]
    _check(report, scope, "one_placed_actor", len(assigned) == 1, len(assigned), 1)
    expected_material = ROOT + "/Materials/M_" + meta["category"]
    for actor in assigned:
        origin, extent = actor.get_actor_bounds(False)
        origin, extent = _vec(origin), _vec(extent)
        actual_bounds = [[origin[i] - extent[i], origin[i] + extent[i]] for i in range(3)]
        scale, location = _vec(actor.get_actor_scale3d()), _vec(actor.get_actor_location())
        rotation = actor.get_actor_rotation()
        rotations = [float(rotation.pitch), float(rotation.yaw), float(rotation.roll)]
        actor_record = {"actor": _path(actor), "label": actor.get_actor_label(), "bounds_world_cm": actual_bounds,
                        "scale": scale, "location_cm": location, "rotation_degrees": rotations,
                        "maximum_world_bounds_error_cm": max_bounds_error(actual_bounds, world_bounds)}
        record["actors"].append(actor_record)
        _check(report, scope, "actor_label", actor.get_actor_label() == "Onsen_" + meta["category"], actor.get_actor_label())
        _check(report, scope, "world_bounds_match_source_cm", actor_record["maximum_world_bounds_error_cm"] <= BOUNDS_TOLERANCE_CM,
               actor_record["maximum_world_bounds_error_cm"], "<= 1 cm on all six bounds")
        _check(report, scope, "actor_handedness_scale", all(abs(a - b) <= 1e-6 for a, b in zip(scale, (1, -1, 1))), scale, [1, -1, 1])
        _check(report, scope, "actor_origin_and_rotation", max(abs(v) for v in location + rotations) <= 1e-5, location + rotations, [0] * 6)
        component = actor.static_mesh_component
        expected_collision = unreal.CollisionEnabled.QUERY_AND_PHYSICS if meta["collision"] else unreal.CollisionEnabled.NO_COLLISION
        _check(report, scope, "placed_collision_mode", component.get_collision_enabled() == expected_collision,
               str(component.get_collision_enabled()), str(expected_collision))
        _check(report, scope, "placed_collision_profile", str(component.get_collision_profile_name()) == ("BlockAll" if meta["collision"] else "NoCollision"),
               str(component.get_collision_profile_name()))
    total_triangles = 0
    for lod in range(lods):
        build = subsystem.get_lod_build_settings(mesh, lod)
        precision = bool(build.get_editor_property("use_full_precision_u_vs"))
        _check(report, scope, "lod_%d_full_precision_uv" % lod, precision, precision, True)
        _check(report, scope, "lod_%d_no_generated_lightmap_uv" % lod,
               not bool(build.get_editor_property("generate_lightmap_u_vs")))
        uv_channels = int(subsystem.get_num_uv_channels(mesh, lod))
        _check(report, scope, "lod_%d_uv0_available" % lod, uv_channels >= 1, uv_channels)
        section_count = int(mesh.get_num_sections(lod))
        _check(report, scope, "lod_%d_single_authored_section" % lod, section_count == 1, section_count, 1)
        extracted_vertices = 0
        for section in range(section_count):
            buffers = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, lod, section)
            if len(buffers) != 5:
                raise ValueError("GetSectionFromStaticMesh did not return five buffers")
            vertices = [_vec(v) for v in buffers[0]]
            indices = [int(i) for i in buffers[1]]
            normals = [_vec(v) for v in buffers[2]]
            uvs = [_uv(v) for v in buffers[3]]
            tangents = [_vec(t.get_editor_property("tangent_x")) for t in buffers[4]]
            measured = measure_buffers(vertices, indices, normals, uvs, tangents,
                                       meta["uv"]["atlas_pixels"], meta["uv"].get("target_px_per_m"))
            measured.update(lod=lod, section=section, uv_channels=uv_channels, full_precision_uv=precision)
            record["sections"].append(measured)
            extracted_vertices += len(vertices)
            if lod == 0:
                total_triangles += measured["triangles"]
            _check(report, scope, "lod_%d_section_%d_finite_valid_buffers_and_density" % (lod, section),
                   not measured["errors"], measured["errors"])
            if "bounds_local_cm" in measured:
                error = max_bounds_error(measured["bounds_local_cm"], local_bounds)
                measured["maximum_local_bounds_error_cm"] = error
                _check(report, scope, "lod_%d_section_%d_local_bounds_import_policy" % (lod, section), error <= BOUNDS_TOLERANCE_CM, error, "<= 1 cm")
            enabled = bool(subsystem.is_section_collision_enabled(mesh, lod, section))
            measured["section_collision_enabled"] = enabled
            _check(report, scope, "lod_%d_section_%d_collision" % (lod, section), enabled == meta["collision"], enabled, meta["collision"])
            slot = int(subsystem.get_lod_material_slot(mesh, lod, section))
            material = mesh.get_material(slot) if slot >= 0 else None
            measured["material_slot"] = slot
            measured["material"] = _path(material)
            _check(report, scope, "lod_%d_section_%d_material" % (lod, section),
                   material is not None and _package(_path(material)) == expected_material, _path(material), expected_material)
            for actor in assigned:
                actual = actor.static_mesh_component.get_material(slot) if slot >= 0 else None
                _check(report, scope, "placed_section_%d_material" % section,
                       actual is not None and _package(_path(actual)) == expected_material, _path(actual), expected_material)
            if material is not None and _package(_path(material)) == expected_material:
                textures = unreal.MaterialEditingLibrary.get_used_textures(material)
                measured["used_textures"] = sorted(_path(t) for t in textures)
                if meta["category"] == "Steam":
                    texture_name = "T_Steam_Opacity"
                elif meta["category"] in ("Water", "Stream"):
                    texture_name = "T_Water_Ripples"
                else:
                    texture_name = "T_" + meta["texture"].capitalize() + "_BaseColor"
                expected_texture = ROOT + "/Textures/" + texture_name
                _check(report, scope, "generated_texture_used", expected_texture in [_package(p) for p in measured["used_textures"]],
                       measured["used_textures"], expected_texture)
        render_vertices = int(subsystem.get_number_verts(mesh, lod))
        _check(report, scope, "lod_%d_all_render_vertices_examined" % lod, extracted_vertices == render_vertices,
               extracted_vertices, render_vertices)
    record["source_vertex_count_before_seam_splitting"] = meta["vertices"]
    record["source_triangle_count"] = meta["triangles"]
    record["imported_lod0_triangle_count"] = total_triangles
    _check(report, scope, "exact_source_triangle_count", total_triangles == int(meta["triangles"]), total_triangles, meta["triangles"])


def _trace(world, x, y, high, low, ignored):
    hit = unreal.SystemLibrary.line_trace_single_by_profile(
        world, unreal.Vector(x, y, high), unreal.Vector(x, y, low), "Pawn", False,
        ignored, unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return None
    b = unreal.GameplayStatics.break_hit_result(hit)
    return {"blocking": bool(b[0]), "initial_overlap": bool(b[1]), "distance_cm": float(b[3]),
            "impact_cm": _vec(b[5]), "normal": _vec(b[7]), "actor": _path(b[9]),
            "actor_label": b[9].get_actor_label() if b[9] else None, "component": _path(b[10])}


def _validate_ground(report, world, manifest, actors):
    record = {"trace_profile": "Pawn", "trace_complex": False, "route_samples": [], "foundations": []}
    report["ground_support"] = record
    # Noncolliding water/steam cannot support the ray; no colliding obstacle is
    # removed from route queries. Ignore only PlayerStarts and noncolliding sky.
    ignored = [a for a in actors if isinstance(a, unreal.PlayerStart) or a.get_actor_label() == "Muted sky backdrop"]
    for leg, (a, b) in enumerate(zip(manifest["route"], manifest["route"][1:])):
        distance = math.hypot(b[0] - a[0], b[1] - a[1])
        steps = max(1, int(math.ceil(distance / 2.0)))
        for index in range(steps + 1):
            t = index / steps
            point = [(a[i] + (b[i] - a[i]) * t) * 100.0 for i in range(3)]
            hit = _trace(world, point[0], point[1], point[2] + 80.0, point[2] - 400.0, ignored)
            sample = {"leg": leg, "t": t, "expected_route_surface_cm": point, "hit": hit}
            record["route_samples"].append(sample)
            good = bool(hit and hit["blocking"] and not hit["initial_overlap"] and
                        -15.0 <= hit["impact_cm"][2] - point[2] <= 35.0 and hit["normal"][2] >= math.cos(math.radians(45)))
            if hit:
                sample["surface_height_delta_cm"] = hit["impact_cm"][2] - point[2]
            _check(report, "route_ground", "leg_%d_sample_%d" % (leg, index), good, sample,
                   "blocking walkable support from -15 to +35 cm of source route surface")
    terrain = [a for a in actors if a.get_actor_label() == "Onsen_Terrain"]
    if not _check(report, "foundation_ground", "one_terrain_actor", len(terrain) == 1, len(terrain), 1):
        return
    terrain_only_ignored = [a for a in actors if a != terrain[0]]
    for building in [o for o in manifest["semantic_objects"] if o["type"] == "building"]:
        x, y, z = [v * 100.0 for v in building["center"]]
        w, d = [v * 100.0 for v in building["footprint"]]
        bottom, top = building["foundation_bottom"] * 100.0, building["foundation_top"] * 100.0
        item = {"name": building["name"], "source_foundation_bottom_cm": bottom,
                "source_foundation_top_cm": top, "samples": [], "query_isolates": "Onsen_Terrain"}
        record["foundations"].append(item)
        for index, (dx, dy) in enumerate(((0, 0), (-w / 2, -d / 2), (-w / 2, d / 2), (w / 2, -d / 2), (w / 2, d / 2))):
            hit = _trace(world, x + dx, y + dy, z + 200.0, bottom - 500.0, terrain_only_ignored)
            sample = {"x_cm": x + dx, "y_cm": y + dy, "hit": hit}
            item["samples"].append(sample)
            if hit:
                sample["foundation_bottom_minus_terrain_cm"] = bottom - hit["impact_cm"][2]
                sample["terrain_minus_foundation_top_cm"] = hit["impact_cm"][2] - top
            good = bool(hit and hit["blocking"] and hit["actor_label"] == "Onsen_Terrain" and
                        bottom <= hit["impact_cm"][2] + 2.0 and hit["impact_cm"][2] <= top + 15.0)
            _check(report, "foundation_" + building["name"], "terrain_support_%d" % index, good, sample,
                   "foundation bottom at/below actual terrain; terrain <=15 cm above foundation top")


def _validate_dependencies(report, world):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous([ROOT], True)
    map_file = str(Path(unreal.Paths.project_content_dir()) / "Maps" / "HillsideOnsen_ultra.umap")
    registry.scan_files_synchronous([map_file], True)
    assets = registry.get_assets_by_path(ROOT, True, True)
    map_assets = registry.get_assets_by_package_name(MAP, True)
    if not _check(report, "dependencies", "owned_root_on_disk_assets", bool(assets), len(assets) if assets else 0):
        return
    if not _check(report, "dependencies", "owned_map_registered_on_disk", bool(map_assets)):
        return
    options = unreal.AssetRegistryDependencyOptions()
    flags = ("include_soft_package_references", "include_hard_package_references",
             "include_game_package_references", "include_editor_only_package_references",
             "include_searchable_names", "include_soft_management_references", "include_hard_management_references")
    for key in flags:
        options.set_editor_property(key, True)
    seeds = {MAP} | {str(a.package_name) for a in assets}
    queue, visited, edges, external, violations, unknown = sorted(seeds), set(), {}, set(), [], []
    while queue:
        package = queue.pop()
        if package in visited:
            continue
        if not allowed_game_package(package):
            violations.append({"from": None, "to": package})
            continue
        visited.add(package)
        dependencies = registry.get_dependencies(package, options)
        if dependencies is None:
            unknown.append(package)
            continue
        edges[package] = sorted({str(p) for p in dependencies})
        for dependency in edges[package]:
            if dependency.startswith("/Game/"):
                if allowed_game_package(dependency):
                    if dependency not in visited:
                        queue.append(dependency)
                else:
                    # Do not inspect or load a foreign creative package.
                    violations.append({"from": package, "to": dependency})
            elif dependency.startswith("/Engine/") or dependency.startswith("/Script/"):
                external.add(dependency)
            else:
                violations.append({"from": package, "to": dependency})
    report["dependencies"] = {"options": {key: True for key in flags}, "seeds": sorted(seeds),
                              "visited_owned_packages": sorted(visited), "edges": edges,
                              "allowed_builtin_terminals": sorted(external), "violations": violations,
                              "unknown_queries": unknown, "foreign_packages_inspected": False}
    _check(report, "dependencies", "all_queries_complete", not unknown, unknown)
    _check(report, "dependencies", "all_references_within_owned_scope_or_builtins", not violations, violations)
    _check(report, "dependencies", "map_has_authored_mesh_references",
           any(p.startswith(ROOT + "/Meshes/") for p in edges.get(MAP, [])), edges.get(MAP, []))


def run_static_validation(world, manifest, output_path):
    """Validate read-only; write a failed report even if an Unreal API throws."""
    started = time.monotonic()
    report = {"schema": "hillside_onsen_saved_map_static_validation_v1", "status": "working", "passed": False,
              "started_at_utc": _utc(), "map": MAP, "owned_root": ROOT, "checks": [], "failures": [],
              "errors": [], "meshes": [], "api_source_root": "C:/Program Files/Epic Games/UE_5.7/",
              "api_evidence": API_EVIDENCE, "read_only_package_policy": True,
              "limitations": ["Only LOD render buffers/UV0 are extracted; all authored meshes are expected to have exactly one LOD and one section.",
                              "Source vertices can split at UV/normal seams; exact source triangle counts and complete render-vertex coverage are checked instead of source vertex equality.",
                              "Imported UV density is measured per triangle. Source polygon island padding/overlap is not independently recomputed after triangulation.",
                              "Steam has intentional overlapping full-card UVs and no uniform density target.",
                              "UV density uses source atlas-equivalent pixels; actual materials tile generated 512px imagery across unique charts rather than unique baked artwork per island.",
                              "Ground rays sample route centers every <=2 m and five foundation locations; they do not substitute for runtime Character walking or exhaustive contact testing.",
                              "Foundation terrain queries intentionally ignore nonterrain actors to avoid self-support hits; source foundation bottom/top are compared to actual terrain.",
                              "AssetRegistry dependency queries use on-disk packages. Engine and native Script packages are permitted terminal references and are not recursively inspected.",
                              "The caller must independently compare saved-package hashes before/after this read-only validation."]}
    dirty_before = None
    try:
        if unreal is None:
            raise RuntimeError("Validation must execute inside the Unreal Editor")
        if isinstance(manifest, (str, Path)):
            manifest = json.loads(Path(manifest).read_text(encoding="utf-8"))
        project = unreal.Paths.get_project_file_path().replace("\\", "/")
        report["project"] = project
        if "/Saved/Workers/HillsideOnsen/ultra/" not in project:
            raise RuntimeError("Refusing validation outside this task's private project")
        world_package = world.get_outermost().get_name()
        report["loaded_world"] = world.get_path_name()
        if world_package != MAP:
            raise RuntimeError("Loaded world is not the assigned saved map: " + world_package)
        if manifest.get("theme") != "HillsideOnsen" or manifest.get("effort") != "ultra":
            raise RuntimeError("Manifest ownership mismatch")
        dirty_before = _dirty_owned()
        report["dirty_owned_packages_before"] = dirty_before
        _check(report, "saved_map", "fresh_clean_saved_packages", not dirty_before, dirty_before)
        actors = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor))
        _check(report, "saved_map", "map_name", world_package == MAP, world_package, MAP)
        wp = world.get_world_settings().get_editor_property("world_partition")
        _check(report, "saved_map", "non_world_partition", wp is None, _path(wp))
        external = []
        for actor in actors:
            for obj in [actor] + list(actor.get_components_by_class(unreal.ActorComponent)):
                if obj.is_package_external() or obj.get_package().get_name() != MAP:
                    external.append({"object": _path(obj), "package": obj.get_package().get_name()})
        _check(report, "saved_map", "no_external_actor_or_component_packages", not external, external)
        starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
        _check(report, "saved_map", "one_player_start", len(starts) == 1, len(starts), 1)
        report["player_starts"] = [{"actor": _path(a), "location_cm": _vec(a.get_actor_location())} for a in starts]
        expected_start = manifest.get("player_start_cm", [0, -4400, 360])
        if len(starts) == 1:
            _check(report, "saved_map", "player_start_position", max(abs(a - b) for a, b in zip(_vec(starts[0].get_actor_location()), expected_start)) <= 1.0,
                   _vec(starts[0].get_actor_location()), expected_start)
        _check(report, "manifest", "eighteen_authored_meshes", len(manifest["meshes"]) == EXPECTED_MESH_COUNT,
               len(manifest["meshes"]), EXPECTED_MESH_COUNT)
        _check(report, "manifest", "unique_mesh_names", len({m["name"] for m in manifest["meshes"]}) == len(manifest["meshes"]))
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        for meta in manifest["meshes"]:
            try:
                _validate_mesh(report, meta, actors, subsystem)
            except Exception:
                _exception(report, meta.get("name", "unnamed_mesh"))
        for name, operation in (("dependencies", lambda: _validate_dependencies(report, world)),
                                ("ground_support", lambda: _validate_ground(report, world, manifest, actors))):
            try:
                operation()
            except Exception:
                _exception(report, name)
    except Exception:
        _exception(report, "validation")
    finally:
        if unreal is not None and dirty_before is not None:
            try:
                dirty_after = _dirty_owned()
                report["dirty_owned_packages_after"] = dirty_after
                _check(report, "read_only", "no_new_dirty_owned_packages", not (set(dirty_after) - set(dirty_before)),
                       sorted(set(dirty_after) - set(dirty_before)))
            except Exception:
                _exception(report, "read_only_dirty_check")
        report["finished_at_utc"] = _utc()
        report["elapsed_wall_seconds"] = time.monotonic() - started
        report["status"] = "passed" if report["checks"] and not report["failures"] and not report["errors"] else "failed"
        report["passed"] = report["status"] == "passed"
        report = _safe_json(report)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return report
