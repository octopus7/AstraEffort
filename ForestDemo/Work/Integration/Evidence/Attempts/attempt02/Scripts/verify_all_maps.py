"""Read-only saved-map integration checks. Run only in the prepared supervisor project."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback

import unreal as u


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


request_path = Path(os.environ['FOREST_INTEGRATION_REQUEST'])
request = json.loads(request_path.read_text(encoding='utf-8-sig'))
project = Path(request['project']).resolve()
evidence = Path(request['evidence']).resolve()
if evidence != project.parent / 'Evidence' or Path(request['candidate_manifest']).resolve() != evidence / 'candidate_snapshot.json':
    raise RuntimeError('Evidence/manifest paths do not belong to the supervisor snapshot')
if request_path.resolve() != project.parent / 'request.json' or '/Saved/Workers/Supervisor/' not in project.as_posix():
    raise RuntimeError('Request/project are not inside the supervisor snapshot')
result_path = evidence / 'saved_maps_validation.json'
result = {'started_at_utc': utc(), 'baseline_commit': request['baseline_commit'],
          'project': str(project), 'passed': False, 'maps': [], 'errors': []}


def persist():
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def package_name(path):
    return str(path).split('.', 1)[0]


def verify_frozen_files():
    manifest = json.loads(Path(request['candidate_manifest']).read_text(encoding='utf-8-sig'))
    mismatches = []
    expected = {row['path'] for row in manifest['files']}
    actual = {'ForestDemo.uproject'}
    for directory in ['Config', 'Source', 'Content']:
        actual.update(p.relative_to(project).as_posix() for p in (project / directory).rglob('*') if p.is_file())
    for row in manifest['files']:
        path = project / row['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            mismatches.append(row['path'])
    check(actual == expected, f'Snapshot file set changed: {sorted(actual ^ expected)}')
    check(not mismatches, f'Snapshot hashes changed: {mismatches}')
    return len(manifest['files'])


def dependencies(registry, start_packages, asset_root, own_map):
    options = u.AssetRegistryDependencyOptions(True, True, True, True, True, True, True)
    graph, errors = {}, []
    todo = list(start_packages)
    engine_modules = set(request['engine_script_modules'])
    while todo:
        package = todo.pop()
        if package in graph:
            continue
        refs = sorted(str(ref) for ref in registry.get_dependencies(package, options))
        graph[package] = refs
        for ref in refs:
            if '__ExternalActors__' in ref or '__ExternalObjects__' in ref or 'BuiltData' in ref:
                errors.append({'from': package, 'to': ref, 'reason': 'external/baked package'})
            if ref.startswith('/Game/'):
                if ref != own_map and not ref.startswith(asset_root + '/'):
                    errors.append({'from': package, 'to': ref, 'reason': 'foreign or old asset root'})
                elif ref not in graph:
                    todo.append(ref)
            elif ref.startswith('/Script/'):
                if ref != '/Script/ForestDemo' and ref[8:] not in engine_modules:
                    errors.append({'from': package, 'to': ref, 'reason': 'non-baseline native module'})
            elif not ref.startswith('/Engine/'):
                errors.append({'from': package, 'to': ref, 'reason': 'non-Engine mount'})
    return graph, errors


try:
    actual_project = Path(u.Paths.get_project_file_path()).resolve().parent
    check(actual_project == project, f'Wrong project: {actual_project}')
    check('/Saved/Workers/Supervisor/' in project.as_posix(), 'Not a supervisor scratch project')
    check(request['final_defaults_applied'], 'Candidate default-map/main retirement changes have not been applied')
    result['files_verified_before'] = verify_frozen_files()
    content = project / 'Content'
    actual_maps = sorted(p.stem for p in content.rglob('*.umap'))
    check(actual_maps == sorted(request['expected_maps']), f'Unexpected map set: {actual_maps}')
    forbidden_files = [p.relative_to(content).as_posix() for p in content.rglob('*')
                       if p.is_file() and ('__External' in p.as_posix() or 'BuiltData' in p.name)]
    check(not forbidden_files, f'External/baked files: {forbidden_files}')
    # These are reflected config properties on the live settings object.
    settings = u.get_default_object(u.GameMapsSettings)
    defaults = {}
    result['default_map_api'] = {}
    for key in ['editor_startup_map', 'game_default_map']:
        value = settings.get_editor_property(key)
        diagnostic = {'type': type(value).__name__, 'method': 'to_tuple',
                      'has_to_tuple': hasattr(value, 'to_tuple')}
        result['default_map_api'][key] = diagnostic
        # NativeBreakFunc is excluded from Python's SystemLibrary. StructBase.to_tuple()
        # invokes SoftObjectPath's HasNativeBreak function and returns its one string output.
        parts = value.to_tuple()
        diagnostic['result_type'] = type(parts).__name__
        diagnostic['result_repr'] = repr(parts)
        check(isinstance(parts, tuple) and len(parts) == 1 and isinstance(parts[0], str),
              f'Unexpected SoftObjectPath.to_tuple result for {key}: {parts!r}')
        defaults[key] = parts[0]
        check(package_name(defaults[key]) == request['expected_default_map'], f'Wrong live {key}: {defaults[key]}')
    result['live_default_maps'] = defaults
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors_api = u.get_editor_subsystem(u.EditorActorSubsystem)
    initial = editor.get_editor_world()
    result['initial_editor_world'] = initial.get_path_name() if initial else None
    # Explicitly load the value returned by the live default setting.
    check(levels.load_level(package_name(defaults['game_default_map'])), 'Cannot load actual configured default')
    result['loaded_actual_default_world'] = editor.get_editor_world().get_path_name()
    check(package_name(result['loaded_actual_default_world']) == request['expected_default_map'], 'Default resolved to wrong world')
    logger_class = u.load_class(None, '/Script/ForestDemo.ScreenDebugLogger')
    check(logger_class is not None, 'Native ScreenDebugLogger class unavailable')
    result['native_logger_class'] = logger_class.get_path_name()
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous(['/Game'], force_rescan=True)
    all_assets = registry.get_assets_by_path('/Game', recursive=True)
    redirectors = [str(a.package_name) for a in all_assets if a.is_redirector()]
    check(not redirectors, f'Redirectors present: {redirectors}')
    allowed_roots = []
    for name in request['expected_maps']:
        effort = name.removeprefix('MountainStation_')
        theme = 'MountainStation' if name.startswith('MountainStation_') else 'Forest'
        allowed_roots.append('/Game/' + theme + '/' + effort + '/')
    own_maps = {'/Game/Maps/' + name for name in request['expected_maps']}
    unowned = sorted({str(a.package_name) for a in all_assets
                      if str(a.package_name) not in own_maps and not any(str(a.package_name).startswith(root) for root in allowed_roots)})
    check(not unowned, f'Unowned/old-root packages in snapshot: {unowned}')
    for name in request['expected_maps']:
        effort = name.removeprefix('MountainStation_')
        theme = 'MountainStation' if name.startswith('MountainStation_') else 'Forest'
        root = '/Game/' + theme + '/' + effort
        map_path = '/Game/Maps/' + name
        record = {'map': map_path, 'asset_root': root, 'started_at_utc': utc(), 'passed': False}
        result['maps'].append(record)
        try:
            check(levels.load_level(map_path), f'Load failed: {map_path}')
            world = editor.get_editor_world()
            check(world is not None and world.get_path_name() == map_path + '.' + name, 'Wrong saved world loaded')
            record['world_path'] = world.get_path_name()
            world_settings = world.get_world_settings()
            partition = world_settings.get_editor_property('world_partition')
            record['world_partition'] = partition.get_path_name() if partition else None
            check(partition is None, 'World Partition is enabled')
            record['force_no_precomputed_lighting'] = bool(world_settings.get_editor_property('force_no_precomputed_lighting'))
            actors = actors_api.get_all_level_actors()
            record['actor_count'] = len(actors)
            record['native_loggers'] = [a.get_path_name() for a in actors if a.get_class().get_path_name() == '/Script/ForestDemo.ScreenDebugLogger']
            record['player_starts'] = [a.get_path_name() for a in actors if isinstance(a, u.PlayerStart)]
            check(record['native_loggers'], 'No baseline native logger actor in saved map')
            check(record['player_starts'], 'No PlayerStart in saved map')
            # Optional future native-rim regression baseline: failure is unknown, not zero.
            census = {'primitive_count': 0, 'enabled_count': 0, 'enabled': [], 'unknown': []}
            try:
                for component in actors_api.get_all_level_actors_components():
                    if not isinstance(component, u.PrimitiveComponent):
                        continue
                    census['primitive_count'] += 1
                    try:
                        enabled = bool(component.get_editor_property('render_custom_depth'))
                        stencil = int(component.get_editor_property('custom_depth_stencil_value'))
                        if enabled:
                            census['enabled_count'] += 1
                            census['enabled'].append({'component': component.get_path_name(), 'stencil': stencil})
                    except Exception as exc:
                        census['unknown'].append({'component': component.get_path_name(), 'error': str(exc)})
                census['enabled_stencil_values'] = sorted({row['stencil'] for row in census['enabled']})
                census['enabled_in_future_rim_range_16_255'] = sum(16 <= row['stencil'] <= 255 for row in census['enabled'])
            except Exception as exc:
                census['unknown'].append({'error': str(exc)})
            record['custom_depth_census'] = census
            packages = [map_path] + [str(a.package_name) for a in registry.get_assets_by_path(root, recursive=True)]
            graph, errors = dependencies(registry, packages, root, map_path)
            record['dependency_graph'] = graph
            record['dependency_packages_checked'] = len(graph)
            record['forbidden_dependencies'] = errors
            check(not errors, f'Forbidden references in {map_path}')
            record['passed'] = True
        except Exception:
            record['error'] = traceback.format_exc()
            result['errors'].append({'map': map_path, 'error': record['error']})
        record['finished_at_utc'] = utc()
        persist()
    result['files_verified_after'] = verify_frozen_files()
    result['passed'] = len(result['maps']) == 8 and all(m['passed'] for m in result['maps'])
except Exception:
    result['errors'].append({'error': traceback.format_exc()})
finally:
    result['finished_at_utc'] = utc()
    result['limitations'] = ['Saved-world integration and native-class presence only; per-scene PIE/collision and visual evidence remain in the committed comparison reports.', 'Hello dispatch/message registration is verified by a separate native automation process, not by this script.']
    persist()
    u.log('INTEGRATION_SAVED_MAPS_' + ('PASS' if result['passed'] else 'FAIL'))
    u.SystemLibrary.quit_editor()
