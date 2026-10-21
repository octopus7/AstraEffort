# Alder Pass — MountainStation / ultra

Started 2026-10-21 12:27:25 UTC / 21:27:25 KST. This is the independently authored ultra assignment; no scene authoring is delegated.

A 100 m square mountain clearing, composed as a quiet miniature railway stop. A broad bowed single track runs past a stone platform toward a masonry tunnel on the right. The station has sage timber walls, a terracotta roof with standing seams, cream trim, glazed windows, covered platform and a clear entrance. Pine groups and layered outcrops frame the station rather than hiding it. A looping gravel footpath climbs behind the station to a fenced overlook. The forecourt, platform access ramp, freight shed, benches, clock, lamps, luggage, signs and stacked crates explain how the place is used.

All geometry and palette are authored here with background Blender. Distinct semantic mesh groups retain a compact asset set; UE materials use deliberately restrained colors. Static ground and structures have collision. Lighting is dynamic. A PlayerStart and the baseline native ScreenDebugLogger remain in the map.

Implementation sequence: author source geometry; import into private baseline project; construct and save non-partitioned map; reload and recursively validate package dependencies and ground/ramp traces; capture four actual UE views; inspect pixels; close editor and publish only owned assets and map; write evidence and timing report. Camera centre is (0,0), ground datum Z0=0 cm.

No source art, assets, scripts or reports from another assignment are used. No Git mutations. All UE processes pass through the shared named-mutex launcher. No public project editor sessions.
