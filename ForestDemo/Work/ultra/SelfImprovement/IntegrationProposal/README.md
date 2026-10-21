# Forest ultra: minimal native tree integration proposal

The approved BP_AnimeFoliageTree requires its native construction/runtime behavior and a custom canopy rim renderer. These ten plugin source/shader/descriptor files were compiled successfully with UE 5.7 in the isolated ultra scratch project. Actor/module/shader/CVar identifiers are namespaced to ForestUltraTrees; the original algorithms and defaults are preserved. Source hashes and exact adaptations are recorded in ../native_port_manifest.json.

Supervisor integration (worker has not modified shared Plugins, Config, Source, uproject or Binaries):
1. Copy this Plugins/ForestUltraTrees directory to the shared ForestDemo/Plugins/ForestUltraTrees.
2. Enable stencil custom depth in shared DefaultEngine.ini: under [/Script/Engine.RendererSettings], set r.CustomDepth=3. This is the only required renderer setting. No temporary CoreRedirect belongs in the shared project.
3. Build ForestDemoEditor Win64 Development with UE 5.7. The plugin is EnabledByDefault and PostConfigInit; shader mapping is plugin-relative. No shared game module source edits are needed.
4. Confirm /Script/ForestUltraTrees.ForestUltraAnimeTreeActor loads before accepting the new ultra map. The worker will publish only the validated owned Content and map after the native dependency is integrated.

The renamed BP is /Game/Forest/ultra/AnimeTree/BP_AnimeFoliageTree. Final assets will have no /Script/TunaSweeper or /Game/Environment dependencies. Do not integrate the scratch migration redirect. The source TunaSweeper project remains read-only.

Runtime controls: r.ForestUltra.CanopyRim=1, .GapRadius=3, .Debug=0 (1 stencil IDs, 2 closed mask, 3 rim weight). Tree source defaults and SetTreeParameters/RefreshTree behavior are retained; no ticking native actor is added. The shared stencil allocator covers IDs 16-255 per world.

Validation is ongoing. Consult ../STATUS.json, ../source_tree_inspection.json, ../validation.json and actual render evidence. Successful native compilation alone is not a claim of final scene/runtime validation.
