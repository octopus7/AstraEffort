"""One fresh UnrealEditor-Cmd process per map; request via FOREST_ULTRA_SMOKE_REQUEST."""
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def within(path, root):
    return Path(path).resolve().is_relative_to(Path(root).resolve())


def validate_request(request):
    project = Path(request['project']).resolve()
    shared = Path(request['shared_project']).resolve()
    require(request['case'] in ('ultra', 'medium'), 'case must be ultra or medium')
    require(project != shared, 'Refuse shared project')
    require(within(project, shared.parent / 'Saved/Workers/Supervisor'),
            'Project must be beneath shared Saved/Workers/Supervisor')
    output = Path(request['output']).resolve()
    require(within(output, shared.parent / 'Saved/Workers/Supervisor') or
            within(output, shared.parent / 'Work/UltraImprovementIntegration'),
            'Output must be supervisor-owned')
    return project, shared, output


def own_dependency(package, case):
    return package == '/Game/Maps/' + case or package.startswith('/Game/Forest/' + case + '/')


def self_test():
    base = Path.cwd().resolve() / 'synthetic-project'
    good = dict(project=str(base / 'Saved/Workers/Supervisor/Smoke/ForestDemo.uproject'),
                shared_project=str(base / 'ForestDemo.uproject'), case='ultra',
                output=str(base / 'Saved/Workers/Supervisor/Smoke/result.json'))
    validate_request(good)
    for change in ({'project': good['shared_project']}, {'case': 'high'},
                   {'project': str(base / 'Saved/Workers/SupervisorSibling/project.uproject')},
                   {'output': str(base / 'Content/result.json')}):
        try:
            validate_request(dict(good, **change))
        except AssertionError:
            pass
        else:
            raise AssertionError('Unsafe request accepted: ' + repr(change))
    require(own_dependency('/Game/Forest/ultra/Tree', 'ultra'), 'own asset rejected')
    require(own_dependency('/Game/Maps/medium', 'medium'), 'own map rejected')
    for bad in ('/Game/Forest/ultraSibling/Tree', '/Game/Forest/medium/Tree', '/Game/ultra/Tree'):
        require(not own_dependency(bad, 'ultra'), 'Foreign dependency accepted')
    print('PASS: request isolation and dependency boundary tests; no Unreal imported/launched')


def run():
    import unreal
    request = json.loads(Path(os.environ['FOREST_ULTRA_SMOKE_REQUEST']).read_text(encoding='utf-8-sig'))
    project, shared, output = validate_request(request)
    actual = Path(unreal.Paths.get_project_file_path()).resolve()
    require(actual == project, 'Loaded project differs from request')
    require(project.is_file() and shared.is_file(), 'Project file missing')
    require(not output.exists(), 'Refuse overwriting earlier smoke evidence')
    report = dict(case=request['case'], project=str(project), shared_project=str(shared),
                  started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  pid=os.getpid(), success=False, errors=[], checks={},
                  limitations=['Renderer Styles and GPU pass count are not reflected; medium idle result is a source-backed inference.',
                               'Short possessed PIE/component smoke only; does not repeat movement/collision, visual, packaged or performance validation.',
                               'Process exit code and final log must be checked outside this script.'])
    case = request['case']
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    state = dict(phase='preflight', ticks=0, started=time.monotonic(), handle=None, ending_at=None)

    def check(name, condition, evidence):
        report['checks'][name] = dict(passed=bool(condition), evidence=evidence)
        require(condition, name)

    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    def preflight():
        shared_plugin = shared.parent / 'Plugins/ForestUltraTrees'
        private_plugin = project.parent / 'Plugins/ForestUltraTrees'
        files = [shared_plugin / 'ForestUltraTrees.uplugin']
        files += sorted((shared_plugin / 'Source').rglob('*.*'))
        files += sorted((shared_plugin / 'Shaders').rglob('*.*'))
        files += [shared_plugin / 'Binaries/Win64/UnrealEditor-ForestUltraTrees.dll',
                  shared_plugin / 'Binaries/Win64/UnrealEditor.modules']
        hashes = {str(f.relative_to(shared_plugin)).replace('\\', '/'): digest(f) for f in files}
        check('shared_plugin_exact_copy', all(digest(private_plugin / rel) == sha for rel, sha in hashes.items()), hashes)
        # Inspect actual loaded module, not just the DLL lying on disk.
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
        kernel.GetModuleHandleW.restype = ctypes.c_void_p
        kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
        kernel.GetModuleFileNameW.restype = ctypes.c_uint32
        module = kernel.GetModuleHandleW('UnrealEditor-ForestUltraTrees.dll')
        buffer = ctypes.create_unicode_buffer(32768)
        require(module and kernel.GetModuleFileNameW(module, buffer, len(buffer)), 'Native DLL not loaded')
        loaded = Path(buffer.value).resolve()
        expected = private_plugin / 'Binaries/Win64/UnrealEditor-ForestUltraTrees.dll'
        check('loaded_private_dll', loaded == expected.resolve() and digest(loaded) == digest(shared_plugin / 'Binaries/Win64/UnrealEditor-ForestUltraTrees.dll'), str(loaded))
        originals = ('/Script/TunaSweeper', '/Script/CanopyRim', '/Game/Environment')
        config_hits = []
        for directory in (project.parent / 'Config', private_plugin / 'Config'):
            for path in directory.rglob('*.ini'):
                for line in path.read_text(encoding='utf-8-sig', errors='replace').splitlines():
                    if line.strip() and not line.lstrip().startswith((';', '#')) and any(s.lower() in line.lower() for s in originals):
                        config_hits.append(dict(file=str(path), line=line))
        check('no_original_project_redirects', not config_hits, config_hits)
        check('custom_depth_stencil', unreal.SystemLibrary.get_console_variable_int_value('r.CustomDepth') == 3, unreal.SystemLibrary.get_console_variable_int_value('r.CustomDepth'))
        check('rim_enabled', unreal.SystemLibrary.get_console_variable_int_value('r.ForestUltra.CanopyRim') == 1, unreal.SystemLibrary.get_console_variable_int_value('r.ForestUltra.CanopyRim'))
        native = unreal.load_class(None, '/Script/ForestUltraTrees.ForestUltraAnimeTreeActor')
        require(native is not None, 'Native actor class missing')
        state['native'] = native
        root = '/Game/Forest/' + case
        map_path = '/Game/Maps/' + case
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        registry.scan_paths_synchronous([root, '/Game/Maps'], True)
        assets = registry.get_assets_by_path(root, recursive=True)
        require(len(assets) > 0, 'Own asset registry is empty')
        redirects = [str(a.package_name) for a in assets if str(a.asset_class_path.asset_name) == 'ObjectRedirector']
        check('no_own_redirectors', not redirects, redirects)
        options = unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True, include_hard_package_references=True,
            include_game_package_references=True, include_editor_only_package_references=True,
            include_searchable_names=False, include_soft_management_references=True,
            include_hard_management_references=True)
        pending = {map_path} | {str(a.package_name) for a in assets}
        graph = {}
        bad = []
        while pending:
            package = pending.pop()
            if package in graph:
                continue
            deps = [str(d) for d in registry.get_dependencies(package, options)]
            graph[package] = deps
            for dep in deps:
                if any(s.lower() in dep.lower() for s in originals):
                    bad.append([package, dep])
                if dep.startswith('/Game/'):
                    if not own_dependency(dep, case):
                        bad.append([package, dep])
                    elif dep not in graph:
                        pending.add(dep)
        check('recursive_own_dependencies', not bad, dict(packages=len(graph), foreign=bad, graph=graph, searchable_names=False))
        asset_hashes = {}
        for package in graph:
            extension = '.umap' if package == map_path else '.uasset'
            relative = Path('Content') / (package.removeprefix('/Game/') + extension)
            a, b = project.parent / relative, shared.parent / relative
            require(a.is_file() and b.is_file(), 'Missing saved package: ' + package)
            require(digest(a) == digest(b), 'Shared/private package mismatch: ' + package)
            asset_hashes[package] = digest(a)
        check('published_package_hashes', True, asset_hashes)
        if case == 'medium':
            cpp = (private_plugin / 'Source/ForestUltraTrees/Private/ForestUltraCanopyRimSubsystem.cpp').read_text()
            view = (private_plugin / 'Source/ForestUltraTrees/Private/ForestUltraCanopyRimViewExtension.cpp').read_text()
            require('for (FVector4f& Style : Styles) Style = FVector4f(0,0,0,0);' in cpp, 'Initialization guard changed')
            require('Styles.ContainsByPredicate([](FVector4f S){ return S.W > 0; })' in view, 'Subscription guard changed')
        require(level.load_level(map_path), 'Map load failed')
        world = editor.get_editor_world()
        check('loaded_map', world.get_path_name().split('.')[0] == map_path, world.get_path_name())
        check('non_world_partition', world.get_world_settings().get_editor_property('world_partition') is None, 'WorldSettings.world_partition')
        inspect_trees(world, 'editor')

    def inspect_trees(world, phase):
        trees = unreal.GameplayStatics.get_all_actors_of_class(world, state['native'])
        check(phase + '_tree_count', len(trees) == (63 if case == 'ultra' else 0), len(trees))
        records, ids = [], []
        for tree in trees:
            leaves = tree.get_leaf_clumps()
            shadows = [c for c in tree.get_components_by_class(unreal.StaticMeshComponent) if c.component_has_tag('AnimeTreeShadow')]
            trunk = tree.get_editor_property('trunk')
            stencil = {int(c.get_editor_property('custom_depth_stencil_value')) for c in leaves}
            require(len(leaves) == 10 and len(shadows) == 10, 'Leaf/shadow count: ' + tree.get_name())
            require(trunk is not None and str(trunk.get_collision_profile_name()) == 'BlockAll', 'Trunk collision profile')
            require(len(stencil) == 1 and 16 <= next(iter(stencil)) <= 255, 'Invalid rim stencil')
            require(all(c.get_editor_property('render_custom_depth') for c in leaves), 'Leaf custom depth disabled')
            ids.extend(stencil)
            records.append(dict(actor=tree.get_path_name(), leaf_count=len(leaves), shadow_count=len(shadows), stencil=list(stencil), trunk_profile=str(trunk.get_collision_profile_name())))
        check(phase + '_tree_components', len(set(ids)) == len(ids), records)
        if case == 'medium':
            report['checks'][phase + '_rim_idle_condition'] = dict(passed=True, evidence='No native tree actors in this fresh world; identical source initializes styles to zero and subscribes only when Styles.W > 0.', measurement='source-backed inference; private style memory/GPU pass count NOT measured')

    def tick(delta):
        state['ticks'] += 1
        try:
            if time.monotonic() - state['started'] > 180 and state['phase'] not in ('ending', 'drain'):
                raise TimeoutError('Smoke exceeded 180 seconds')
            if state['phase'] == 'preflight':
                preflight()
                level.editor_request_begin_play()
                state['phase'] = 'starting'
                state['ticks'] = 0
            elif state['phase'] == 'starting':
                world = editor.get_game_world()
                if world is not None and level.is_in_play_in_editor() and state['ticks'] >= 30:
                    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
                    controller = unreal.GameplayStatics.get_player_controller(world, 0)
                    check('possessed_pawn', pawn is not None and controller is not None and controller.get_controlled_pawn() == pawn,
                          dict(world=world.get_path_name(), pawn=pawn.get_path_name() if pawn else None, controller=controller.get_path_name() if controller else None))
                    inspect_trees(world, 'pie')
                    state['phase'] = 'ending'
                    state['ending_at'] = time.monotonic()
                    level.editor_request_end_play()
            elif state['phase'] == 'ending':
                if not level.is_in_play_in_editor() and editor.get_game_world() is None:
                    check('pie_ended', True, 'No PIE session or game world')
                    state['phase'], state['ticks'] = 'drain', 0
                elif time.monotonic() - state['ending_at'] > 30:
                    report['errors'].append('PIE end timed out; external exit/log audit required')
                    state['phase'], state['ticks'] = 'drain', 0
            elif state['phase'] == 'drain' and state['ticks'] >= 30:
                report['success'] = not report['errors'] and all(c['passed'] for c in report['checks'].values())
                report['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                save()
                unreal.log('FOREST_ULTRA_SHARED_SMOKE ' + str(report['success']))
                unreal.unregister_slate_post_tick_callback(state['handle'])
                unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        except Exception:
            report['errors'].append(traceback.format_exc())
            save()
            unreal.log_error(report['errors'][-1])
            state['phase'], state['ending_at'] = 'ending', time.monotonic()
            level.editor_request_end_play()

    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    state['handle'] = unreal.register_slate_post_tick_callback(tick)


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        self_test()
    else:
        run()
