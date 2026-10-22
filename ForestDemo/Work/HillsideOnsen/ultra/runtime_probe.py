"""Asynchronous native-Character PIE walking probe, authored for HillsideOnsen/ultra.

Call start_runtime_probe(editor_world, routes, output_path, on_done).  Each route
has name and points in cm; point Z is the walkable surface, not capsule center.
Optional obstacle_point marks a known solid face for an expected-block test; the
last route point must be beyond it.  Optional obstacle_actor_label strengthens
identification.  The callback receives the final JSON-compatible report.  This
module leaves PIE running so the caller controls captures and editor shutdown.

No location/transform setters are used to produce walking evidence. One native
Character is placed temporarily in the editor at each route's first point before
PIE. Its PIE duplicate remains disabled until that route starts, then all motion
is CharacterMovement gravity/collision plus continuous AddMovementInput.
"""

import datetime
import json
import math
from pathlib import Path
import time
import traceback
import uuid

try:
    import unreal
except ImportError:
    unreal = None  # Allows offline checks of validation/measurement helpers only.


_ACTIVE_PROBES = []


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def _distance(a, b, dimensions=3):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(dimensions)))


def _point(value):
    if len(value) != 3:
        raise ValueError("Each point needs three coordinates in centimeters")
    result = [float(v) for v in value]
    if not all(math.isfinite(v) for v in result):
        raise ValueError("Point coordinates must be finite")
    return result


def normalize_routes(routes):
    """Reject underspecified/degenerate routes before opening PIE."""
    result = []
    names = set()
    for index, source in enumerate(routes):
        route = dict(source)
        route["name"] = str(route.get("name", "route_%d" % index))
        if route["name"] in names:
            raise ValueError("Route names must be unique")
        names.add(route["name"])
        route["points"] = [_point(p) for p in route["points"]]
        if len(route["points"]) < 2:
            raise ValueError("A route needs a start and at least one goal")
        distances = [_distance(a, b, 2) for a, b in zip(route["points"], route["points"][1:])]
        if any(d < 50.0 for d in distances):
            raise ValueError("Each route leg needs at least 50 cm horizontal travel")
        route["planned_horizontal_distance_cm"] = sum(distances)
        route.setdefault("waypoint_tolerance_cm", 30.0)
        route.setdefault("surface_z_tolerance_cm", 35.0)
        route.setdefault("minimum_grounded_ratio", 0.90)
        route.setdefault("timeout_game_seconds", max(15.0, sum(distances) / 250.0 * 4.0 + 8.0))
        route.setdefault("minimum_motion_cm", min(80.0, sum(distances) * 0.5))
        route.setdefault("obstacle_tolerance_cm", 100.0)
        if route.get("obstacle_point") is not None:
            route["obstacle_point"] = _point(route["obstacle_point"])
        for key in ("waypoint_tolerance_cm", "surface_z_tolerance_cm", "timeout_game_seconds",
                    "minimum_motion_cm", "obstacle_tolerance_cm"):
            if not math.isfinite(float(route[key])) or float(route[key]) <= 0:
                raise ValueError("%s must be positive and finite" % key)
        if not 0.0 < float(route["minimum_grounded_ratio"]) <= 1.0:
            raise ValueError("minimum_grounded_ratio must be in (0, 1]")
        if float(route["waypoint_tolerance_cm"]) >= min(distances):
            raise ValueError("Waypoint tolerance must be smaller than every leg")
        result.append(route)
    if not result:
        raise ValueError("At least one route is required")
    return result


def motion_summary(samples):
    """Summarize observed game ticks; this never substitutes for UE physics."""
    duration = grounded = distance_xy = distance_3d = 0.0
    suspicious = []
    for previous, current in zip(samples, samples[1:]):
        delta = max(0.0, current["game_seconds"] - previous["game_seconds"])
        duration += delta
        if current["grounded"]:
            grounded += delta
        step = _distance(previous["center_cm"], current["center_cm"])
        distance_3d += step
        distance_xy += _distance(previous["center_cm"], current["center_cm"], 2)
        if step > max(120.0, 350.0 * delta):
            suspicious.append({"game_seconds": current["game_seconds"], "distance_cm": step,
                               "delta_seconds": delta})
    return {"sample_count": len(samples), "game_duration_seconds": duration,
            "grounded_time_ratio": grounded / duration if duration else 0.0,
            "horizontal_distance_cm": distance_xy, "distance_3d_cm": distance_3d,
            "observed_elevation_change_cm": (samples[-1]["center_cm"][2] - samples[0]["center_cm"][2]) if samples else 0.0,
            "suspicious_discontinuities": suspicious}


class RuntimeProbe:
    CAPSULE_RADIUS = 28.0
    CAPSULE_HALF_HEIGHT = 88.0
    MAX_WALK_SPEED = 250.0

    def __init__(self, editor_world, routes, output_path, on_done):
        if unreal is None:
            raise RuntimeError("The runtime probe must run inside the Unreal Editor")
        self.routes = normalize_routes(routes)
        self.output_path = Path(output_path)
        self.on_done = on_done
        self.editor_world = editor_world
        self.editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        self.level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        self.actor_editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        self.world = self.character = self.movement = self.capsule = None
        self.controller = self.original_pawn = None
        self.editor_characters = []
        self.pie_characters = {}
        self.route_tags = ["OnsenRuntimeProbe_%s_%d" % (uuid.uuid4().hex, i) for i in range(len(self.routes))]
        self.handle = None
        self.tick_callback = self._tick
        self.started = self.last_game_advance_wall = time.monotonic()
        self.last_game_seconds = None
        self.index = -1
        self.route = self.current = None
        self.phase = "waiting_for_pie"
        self.done = False
        self.report = {"schema": "hillside_onsen_native_character_probe_v1", "status": "working",
                       "started_at_utc": _utc(), "editor_world": editor_world.get_path_name(),
                       "piemode": "requested PlayInEditor via editor_request_begin_play",
                       "movement_driver": "native /Script/Engine.Character + CharacterMovement + AddMovementInput",
                       "capsule_radius_cm": self.CAPSULE_RADIUS, "capsule_half_height_cm": self.CAPSULE_HALF_HEIGHT,
                       "max_walk_speed_cm_per_second": self.MAX_WALK_SPEED,
                       "reset_policy": "distinct unsaved nontransient editor-preplaced Character duplicated into PIE for each route; no movement teleports",
                       "preplaced_characters": [],
                       "routes": [], "blockers": [], "warnings": [], "pie_left_running": False}
        if self.level_editor.is_in_play_in_editor():
            raise RuntimeError("End existing PIE/SIE first: probe requires its own explicit PlayInEditor request")
        self._write()
        _ACTIVE_PROBES.append(self)
        try:
            self._prepare_editor_characters()
            self.handle = unreal.register_slate_pre_tick_callback(self.tick_callback)
            self.level_editor.editor_request_begin_play()
        except Exception:
            self._finish("failed", "Temporary Character preparation or PIE request failed", traceback.format_exc())

    def _prepare_editor_characters(self):
        """Editor-only unsaved preparation; nontransient permits PIE copying."""
        for index, route in enumerate(self.routes):
            point = route["points"][0]
            center = [point[0], point[1], point[2] + self.CAPSULE_HALF_HEIGHT + 3.0]
            actor = self.actor_editor.spawn_actor_from_class(
                unreal.Character, unreal.Vector(*center), unreal.Rotator(0.0, 0.0, 0.0), False)
            if actor is None:
                raise RuntimeError("Temporary editor Character spawn failed for " + route["name"])
            self.editor_characters.append(actor)
            actor.set_editor_property("tags", [self.route_tags[index]])
            actor.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
            actor.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.DISABLED)
            capsule = actor.get_editor_property("capsule_component")
            movement = actor.get_editor_property("character_movement")
            capsule.set_capsule_size(self.CAPSULE_RADIUS, self.CAPSULE_HALF_HEIGHT, True)
            capsule.set_collision_profile_name("NoCollision", True)
            capsule.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            movement.set_editor_property("run_physics_with_no_controller", False)
            movement.set_editor_property("default_land_movement_mode", unreal.MovementMode.MOVE_NONE)
            movement.set_editor_property("default_water_movement_mode", unreal.MovementMode.MOVE_NONE)
            movement.set_editor_property("max_walk_speed", self.MAX_WALK_SPEED)
            movement.set_editor_property("max_step_height", 35.0)
            movement.set_editor_property("air_control", 0.0)
            movement.set_editor_property("auto_activate", False)
            movement.set_walkable_floor_angle(45.0)
            movement.set_movement_mode(unreal.MovementMode.MOVE_NONE)
            movement.deactivate()
            movement.set_component_tick_enabled(False)
            actual = _xyz(actor.get_actor_location())
            if _distance(actual, center) > 1.0:
                raise RuntimeError("Editor spawn did not preserve requested center for " + route["name"])
            self.report["preplaced_characters"].append({
                "route": route["name"], "tag": self.route_tags[index],
                "editor_actor": actor.get_path_name(), "center_cm": actual,
                "transient": False, "saved": False,
                "inactive_movement_mode": "MOVE_NONE", "inactive_collision": "NoCollision"})
        self._write()

    def _find_pie_characters(self):
        characters = unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.Character)
        matches = {tag: [] for tag in self.route_tags}
        self.report["pie_character_inventory"] = []
        for actor in characters:
            tags = [str(t) for t in actor.get_editor_property("tags")]
            self.report["pie_character_inventory"].append({"actor": actor.get_path_name(), "tags": tags})
            for tag in tags:
                if tag in matches:
                    matches[tag].append(actor)
        self.report["pie_character_tag_matches"] = {tag: [_path.get_path_name() for _path in actors]
                                                      for tag, actors in matches.items()}
        for index, tag in enumerate(self.route_tags):
            if len(matches[tag]) != 1:
                raise RuntimeError("Expected one PIE Character for tag %s; found %d" % (tag, len(matches[tag])))
            self.pie_characters[index] = matches[tag][0]

    def _write(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding="utf-8")

    def _game_time(self):
        return float(unreal.SystemLibrary.get_game_time_in_seconds(self.world))

    def _tick(self, slate_delta_seconds):
        if self.done:
            return
        try:
            if time.monotonic() - self.started > max(240.0, len(self.routes) * 120.0):
                self._finish("failed", "Overall wall-time watchdog expired")
                return
            if self.phase == "waiting_for_pie":
                candidate = self.editor.get_game_world()
                if candidate is None:
                    if time.monotonic() - self.started > 60.0:
                        self._finish("failed", "No PIE world within 60 s; full editor active viewport required")
                    return
                world_path = candidate.get_path_name()
                if candidate == self.editor_world or "UEDPIE_" not in world_path:
                    self._finish("failed", "Returned world is not a distinct UEDPIE world: " + world_path)
                    return
                self.world = candidate
                self.report["pie_world"] = world_path
                self.report["pie_left_running"] = True
                self._find_pie_characters()
                self.controller = unreal.GameplayStatics.get_player_controller(self.world, 0)
                if self.controller:
                    self.original_pawn = self.controller.get_controlled_pawn()
                    if self.original_pawn:
                        self.original_collision = self.original_pawn.get_actor_enable_collision()
                        self.original_pawn.set_actor_enable_collision(False)
                    self.report["controller"] = self.controller.get_path_name()
                else:
                    self.report["warnings"].append("No PlayerController; native Character uses run_physics_with_no_controller")
                self.last_game_advance_wall = time.monotonic()
                self._next_route()
                return
            if self.editor.get_game_world() != self.world:
                self._finish("failed", "PIE ended or world changed during probe")
                return
            game_seconds = self._game_time()
            if self.last_game_seconds is not None and game_seconds <= self.last_game_seconds:
                if time.monotonic() - self.last_game_advance_wall > 25.0:
                    self._finish("failed", "PIE game clock stopped advancing for 25 wall seconds")
                return
            self.last_game_seconds = game_seconds
            self.last_game_advance_wall = time.monotonic()
            if self.phase == "next_route":
                self._next_route()
            elif self.phase in ("settling", "walking"):
                self._step(game_seconds)
        except Exception:
            self._finish("failed", "Unreal API/runtime exception", traceback.format_exc())

    def _next_route(self):
        self._destroy_character()
        self.index += 1
        if self.index >= len(self.routes):
            passed = all(r["status"] == "passed" for r in self.report["routes"])
            self._finish("passed" if passed else "failed")
            return
        self.route = self.routes[self.index]
        self.current = {"name": self.route["name"], "status": "working", "specification": self.route,
                        "started_at_utc": _utc(), "samples": [], "hits": [], "waypoints_reached": [],
                        "input_ticks": 0, "input_game_seconds": 0.0, "blockers": []}
        self.report["routes"].append(self.current)
        start = self.route["points"][0]
        expected_center = [start[0], start[1], start[2] + self.CAPSULE_HALF_HEIGHT + 3.0]
        self.character = self.pie_characters.pop(self.index)
        actual_center = _xyz(self.character.get_actor_location())
        self.current["preplaced_tag"] = self.route_tags[self.index]
        self.current["preactivation_center_cm"] = actual_center
        self.current["preactivation_position_error_cm"] = _distance(actual_center, expected_center)
        if self.current["preactivation_position_error_cm"] > 1.0:
            raise RuntimeError("Inactive PIE Character moved before route activation: " + self.route["name"])
        self.capsule = self.character.get_editor_property("capsule_component")
        self.movement = self.character.get_editor_property("character_movement")
        self.current["preactivation_collision_diagnostics"] = self._preactivation_collision_diagnostics(actual_center)
        self._write()
        self.capsule.set_collision_profile_name("Pawn", True)
        self.capsule.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        self.movement.set_editor_property("run_physics_with_no_controller", True)
        self.movement.set_editor_property("default_land_movement_mode", unreal.MovementMode.MOVE_WALKING)
        if self.controller:
            self.controller.possess(self.character)
            if self.controller.get_controlled_pawn() != self.character:
                raise RuntimeError("PlayerController failed to possess native probe Character")
        self.movement.set_component_tick_enabled(True)
        self.movement.activate(True)
        self.movement.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
        self.current["character"] = self.character.get_path_name()
        self.current["character_class"] = self.character.get_class().get_path_name()
        self.current["possessed"] = self.controller is not None
        self.current["capsule_actual_cm"] = {"radius": self.capsule.get_scaled_capsule_radius(),
                                               "half_height": self.capsule.get_scaled_capsule_half_height()}
        self.current["spawn_center_cm"] = _xyz(self.character.get_actor_location())
        self.phase = "settling"
        self.phase_started_game = self._game_time()
        self.settled_since = None
        self.goal_index = 1
        self.last_input_direction = [0.0, 0.0, 0.0]
        self.last_sample_game = None
        self.last_trace_game = -1.0
        self._write()

    def _preactivation_collision_diagnostics(self, center):
        """Read-only queries before enabling this Character's collision/physics."""
        result = {"game_seconds": self._game_time(), "sky_actors": [], "errors": []}
        try:
            actors = unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.StaticMeshActor)
            for actor in actors:
                label = actor.get_actor_label()
                if "sky" not in label.lower():
                    continue
                component = actor.get_editor_property("static_mesh_component")
                result["sky_actors"].append({
                    "actor": actor.get_path_name(), "actor_label": label,
                    "actor_collision_enabled": bool(actor.get_actor_enable_collision()),
                    "component": component.get_path_name(),
                    "component_collision_enabled": str(component.get_collision_enabled()),
                    "component_collision_profile": str(component.get_collision_profile_name())})
        except Exception:
            result["errors"].append({"query": "PIE sky collision settings", "exception": traceback.format_exc()})
        end = [center[0], center[1], center[2] - 20.0]
        trace = {"evidence_type": "preactivation_read_only_capsule_trace_by_Pawn_profile",
                 "trace_start_cm": center[:], "trace_end_cm": end,
                 "capsule_radius_cm": self.CAPSULE_RADIUS, "capsule_half_height_cm": self.CAPSULE_HALF_HEIGHT,
                 "trace_complex": False, "blocking_hit": False, "start_penetrating": False}
        result["downward_capsule_trace"] = trace
        try:
            ignored = [self.character]
            if self.original_pawn:
                ignored.append(self.original_pawn)
            hit = unreal.SystemLibrary.capsule_trace_single_by_profile(
                self.world, unreal.Vector(*center), unreal.Vector(*end),
                self.CAPSULE_RADIUS, self.CAPSULE_HALF_HEIGHT, "Pawn", False,
                ignored, unreal.DrawDebugTrace.NONE, True)
            if hit is not None:
                broken = hit.to_tuple()
                if len(broken) < 18:
                    raise RuntimeError("Unexpected HitResult.to_tuple layout: %d fields" % len(broken))
                actor, component = broken[9], broken[10]
                trace.update({"blocking_hit": bool(broken[0]), "start_penetrating": bool(broken[1]),
                              "trace_time": float(broken[2]), "trace_distance_cm": float(broken[3]),
                              "location_cm": _xyz(broken[4]), "impact_point_cm": _xyz(broken[5]),
                              "hit_normal": _xyz(broken[6]), "impact_normal": _xyz(broken[7]),
                              "actor": actor.get_path_name() if actor else None,
                              "actor_label": actor.get_actor_label() if actor else None,
                              "component": component.get_path_name() if component else None})
        except Exception:
            result["errors"].append({"query": "preactivation downward Pawn capsule trace", "exception": traceback.format_exc()})
            trace["blocking_hit"] = trace["start_penetrating"] = None
        if result["errors"]:
            self.report["warnings"].append("Preactivation collision diagnostics incomplete for " + self.route["name"])
        return result

    def _sample(self, game_seconds):
        location = _xyz(self.character.get_actor_location())
        velocity = _xyz(self.character.get_velocity())
        base = self.movement.get_movement_base()
        sample = {"game_seconds": game_seconds, "phase": self.phase, "center_cm": location,
                  "foot_z_cm": location[2] - self.CAPSULE_HALF_HEIGHT, "velocity_cm_per_second": velocity,
                  "grounded": bool(self.movement.is_moving_on_ground()) and base is not None,
                  "falling": bool(self.movement.is_falling()), "flying": bool(self.movement.is_flying()),
                  "swimming": bool(self.movement.is_swimming()),
                  "movement_mode": str(self.movement.get_editor_property("movement_mode")),
                  "movement_base": base.get_path_name() if base else None,
                  "goal_index": self.goal_index, "previous_input_direction": self.last_input_direction[:]}
        self.current["samples"].append(sample)
        return sample

    def _step(self, game_seconds):
        sample = self._sample(game_seconds)
        if sample["flying"] or sample["swimming"]:
            self._route_finish(False, "Unexpected flying/swimming movement mode")
            return
        if sample["foot_z_cm"] < min(p[2] for p in self.route["points"]) - 180.0:
            self._route_finish(False, "Character fell more than 180 cm below the route")
            return
        if self.phase == "settling":
            if sample["grounded"]:
                if self.settled_since is None:
                    self.settled_since = game_seconds
                if game_seconds - self.settled_since >= 0.5:
                    if abs(sample["foot_z_cm"] - self.route["points"][0][2]) > self.route["surface_z_tolerance_cm"]:
                        self._route_finish(False, "Spawn landed on a different height from the requested surface")
                        return
                    self.phase = "walking"
                    self.phase_started_game = game_seconds
                    self.current["walking_started_game_seconds"] = game_seconds
            else:
                self.settled_since = None
            if game_seconds - self.phase_started_game > 5.0:
                self._route_finish(False, "Character did not establish grounded support within 5 game seconds")
            return
        target = self.route["points"][self.goal_index]
        distance = _distance(sample["center_cm"], target, 2)
        height_ok = abs(sample["foot_z_cm"] - target[2]) <= self.route["surface_z_tolerance_cm"]
        if distance <= self.route["waypoint_tolerance_cm"] and height_ok and sample["grounded"]:
            self.current["waypoints_reached"].append({"index": self.goal_index, "game_seconds": game_seconds,
                                                       "center_cm": sample["center_cm"], "foot_z_cm": sample["foot_z_cm"]})
            self.goal_index += 1
            if self.goal_index == len(self.route["points"]):
                self._route_finish(self.route.get("obstacle_point") is None,
                                   "Reached beyond expected obstacle; solid-block test failed" if self.route.get("obstacle_point") else None)
                return
            target = self.route["points"][self.goal_index]
            distance = _distance(sample["center_cm"], target, 2)
        if self.route.get("obstacle_point") is not None:
            if game_seconds - self.last_trace_game >= 0.1:
                self._trace_obstacle(sample)
                self.last_trace_game = game_seconds
            if self._known_obstacle_stopped(sample):
                self._route_finish(True)
                return
        if game_seconds - self.phase_started_game > self.route["timeout_game_seconds"]:
            self._route_finish(False, "Route timeout without verified arrival/known-obstacle stop")
            return
        if distance > 0.001:
            direction = [(target[0] - sample["center_cm"][0]) / distance,
                         (target[1] - sample["center_cm"][1]) / distance, 0.0]
            self.character.add_movement_input(unreal.Vector(*direction), 1.0, True)
            self.last_input_direction = direction
            self.current["input_ticks"] += 1
            if self.last_sample_game is not None:
                self.current["input_game_seconds"] += max(0.0, game_seconds - self.last_sample_game)
            self.last_sample_game = game_seconds

    def _trace_obstacle(self, sample):
        # UE5.7's Python conversion does not reliably expose sparse hit delegates.
        # This is a query, NOT a movement operation or a substituted hit event.
        # The pass additionally requires measured Character stopping under input.
        direction = self.last_input_direction
        if math.hypot(*direction[:2]) < 0.5:
            return
        start = sample["center_cm"]
        end = [start[i] + direction[i] * 80.0 for i in range(3)]
        ignored = [self.character]
        if self.original_pawn:
            ignored.append(self.original_pawn)
        hit = unreal.SystemLibrary.capsule_trace_single_by_profile(
            self.world, unreal.Vector(*start), unreal.Vector(*end),
            self.CAPSULE_RADIUS, self.CAPSULE_HALF_HEIGHT, "Pawn", False,
            ignored, unreal.DrawDebugTrace.NONE, True)
        if hit is None:
            return
        # PackReturnValues returns HitResult or None, not (bool, HitResult).
        # NativeBreakFunc methods are omitted from the Python library class.
        # Struct.to_tuple() invokes the registered native break and exposes its
        # 18 outputs in the known order (blocking, overlap, time, distance, ...).
        broken = hit.to_tuple()
        if len(broken) < 18:
            raise RuntimeError("Unexpected HitResult.to_tuple layout: %d fields" % len(broken))
        other_actor, other_component = broken[9], broken[10]
        record = {"game_seconds": sample["game_seconds"],
                  "evidence_type": "capsule_trace_by_Pawn_profile_at_observed_character_position",
                  "actor": other_actor.get_path_name() if other_actor else None,
                  "actor_label": other_actor.get_actor_label() if other_actor else None,
                  "component": other_component.get_path_name() if other_component else None,
                  "blocking_hit": bool(broken[0]), "start_penetrating": bool(broken[1]),
                  "trace_distance_cm": float(broken[3]),
                  "impact_point_cm": _xyz(broken[5]), "impact_normal": _xyz(broken[7]),
                  "trace_start_cm": start, "trace_end_cm": end,
                  "input_direction": direction[:]}
        self.current["hits"].append(record)

    def _known_obstacle_stopped(self, sample):
        recent = [s for s in self.current["samples"] if s["phase"] == "walking" and
                  sample["game_seconds"] - s["game_seconds"] <= 1.2]
        if len(recent) < 5 or sample["game_seconds"] - recent[0]["game_seconds"] < 1.0:
            return False
        if not all(s["grounded"] for s in recent):
            return False
        if max(_distance(s["center_cm"], sample["center_cm"], 2) for s in recent) > 4.0:
            return False
        if math.hypot(*sample["velocity_cm_per_second"][:2]) > 5.0:
            return False
        if self.current["input_game_seconds"] < 1.0:
            return False
        for hit in reversed(self.current["hits"]):
            if sample["game_seconds"] - hit["game_seconds"] > 1.5:
                continue
            normal = hit["impact_normal"]
            opposition = sum(normal[i] * hit["input_direction"][i] for i in range(2))
            label = self.route.get("obstacle_actor_label")
            if (hit["blocking_hit"] and not hit["start_penetrating"] and opposition < -0.30 and
                    hit["trace_distance_cm"] <= 6.0 and
                    _distance(hit["impact_point_cm"], self.route["obstacle_point"], 2) <= self.route["obstacle_tolerance_cm"] and
                    (label is None or hit["actor_label"] == label)):
                self.current["verified_obstacle_hit"] = hit
                self.current["stationary_under_input_game_seconds"] = sample["game_seconds"] - recent[0]["game_seconds"]
                return True
        return False

    def _route_finish(self, candidate_pass, reason=None):
        walking = [s for s in self.current["samples"] if s["phase"] == "walking"]
        summary = motion_summary(walking)
        self.current["measurement"] = summary
        if reason:
            self.current["blockers"].append(reason)
        if summary["sample_count"] < 5 or self.current["input_ticks"] < 5:
            self.current["blockers"].append("Insufficient observed movement/input ticks")
        if summary["horizontal_distance_cm"] < self.route["minimum_motion_cm"]:
            self.current["blockers"].append("Insufficient actual Character horizontal motion")
        if summary["grounded_time_ratio"] < self.route["minimum_grounded_ratio"]:
            self.current["blockers"].append("Insufficient grounded fraction during movement")
        if summary["suspicious_discontinuities"]:
            self.current["blockers"].append("Observed motion discontinuity; cannot certify continuous walking")
        self.current["status"] = "passed" if candidate_pass and not self.current["blockers"] else "failed"
        self.current["finished_at_utc"] = _utc()
        self.movement.stop_movement_immediately()
        self.phase = "next_route"
        self._write()

    def _destroy_character(self):
        if self.character and unreal.SystemLibrary.is_valid(self.character):
            self.character.destroy_actor()
        self.character = self.movement = self.capsule = None

    def _finish(self, status, blocker=None, exception=None):
        if self.done:
            return
        self.done = True
        self.report["status"] = status
        self.report["finished_at_utc"] = _utc()
        self.report["elapsed_wall_seconds"] = time.monotonic() - self.started
        if blocker:
            self.report["blockers"].append(blocker)
        if exception:
            self.report["exception"] = exception
        if self.current and self.current["status"] == "working":
            self.current["status"] = "failed"
            self.current["blockers"].append(blocker or "Probe ended before route completion")
        if self.handle is not None:
            unreal.unregister_slate_pre_tick_callback(self.handle)
            self.handle = None
        try:
            self._destroy_character()
            for actor in self.pie_characters.values():
                if unreal.SystemLibrary.is_valid(actor):
                    actor.destroy_actor()
            self.pie_characters.clear()
            if self.original_pawn and unreal.SystemLibrary.is_valid(self.original_pawn):
                self.original_pawn.set_actor_enable_collision(self.original_collision)
                if self.controller and unreal.SystemLibrary.is_valid(self.controller):
                    self.controller.possess(self.original_pawn)
        except Exception as exc:
            self.report["warnings"].append("Cleanup: " + str(exc))
        # Editor preparation is deliberately never saved. While
        # PIE is active the editor actor subsystem refuses editing operations;
        # the private editor's shutdown disposes of these unsaved source actors.
        if self.world is None:
            for actor in self.editor_characters:
                try:
                    if unreal.SystemLibrary.is_valid(actor):
                        self.actor_editor.destroy_actor(actor)
                except Exception as exc:
                    self.report["warnings"].append("Editor preparation cleanup: " + str(exc))
        self.report["editor_preparation_saved"] = False
        self._write()
        if self in _ACTIVE_PROBES:
            _ACTIVE_PROBES.remove(self)
        unreal.log("Native Character PIE probe: %s -> %s" % (status, self.output_path))
        if self.on_done:
            try:
                self.on_done(self.report)
            except Exception:
                unreal.log_error("Probe on_done callback failed: " + traceback.format_exc())

    def cancel(self, reason="Cancelled by caller"):
        self._finish("failed", reason)


def start_runtime_probe(editor_world, routes, output_path, on_done=None):
    """Return a retained asynchronous probe; on_done(report) runs after JSON save."""
    return RuntimeProbe(editor_world, routes, output_path, on_done)
