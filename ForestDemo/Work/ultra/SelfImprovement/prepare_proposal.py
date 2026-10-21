import json,shutil,datetime,hashlib
from pathlib import Path
root=Path(r'D:/github/AstraEffort/ForestDemo')
work=root/'Work/ultra/SelfImprovement';scratch=root/'Saved/Workers/ultra/SelfImprovement/ForestDemo'
src=scratch/'Plugins/ForestUltraTrees';dst=work/'IntegrationProposal/Plugins/ForestUltraTrees'
for relative in ['Source','Shaders']:
 shutil.copytree(src/relative,dst/relative,dirs_exist_ok=True)
shutil.copy2(src/'ForestUltraTrees.uplugin',dst/'ForestUltraTrees.uplugin')
files=[{'path':str(p.relative_to(work/'IntegrationProposal')).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(dst.rglob('*')) if p.is_file()]
(work/'IntegrationProposal/manifest.json').write_text(json.dumps({'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'native_build_exit_code':0,'native_build_evidence':'../Execution/native-build.json','source_port_manifest':'../native_port_manifest.json'},indent=2))
(work/'IntegrationProposal/README.md').write_text('''# Forest ultra: minimal native tree integration proposal

The approved BP_AnimeFoliageTree requires its native construction/runtime behavior and a custom canopy rim renderer. These ten plugin source/shader/descriptor files were compiled successfully with UE 5.7 in the isolated ultra scratch project. Actor/module/shader/CVar identifiers are namespaced to ForestUltraTrees; the original algorithms and defaults are preserved. Source hashes and exact adaptations are recorded in ../native_port_manifest.json.

Supervisor integration (worker has not modified shared Plugins, Config, Source, uproject or Binaries):
1. Copy this Plugins/ForestUltraTrees directory to the shared ForestDemo/Plugins/ForestUltraTrees.
2. Enable stencil custom depth in shared DefaultEngine.ini: under [/Script/Engine.RendererSettings], set r.CustomDepth=3. This is the only required renderer setting. No temporary CoreRedirect belongs in the shared project.
3. Build ForestDemoEditor Win64 Development with UE 5.7. The plugin is EnabledByDefault and PostConfigInit; shader mapping is plugin-relative. No shared game module source edits are needed.
4. Confirm /Script/ForestUltraTrees.ForestUltraAnimeTreeActor loads before accepting the new ultra map. The worker will publish only the validated owned Content and map after the native dependency is integrated.

The renamed BP is /Game/Forest/ultra/AnimeTree/BP_AnimeFoliageTree. Final assets will have no /Script/TunaSweeper or /Game/Environment dependencies. Do not integrate the scratch migration redirect. The source TunaSweeper project remains read-only.

Runtime controls: r.ForestUltra.CanopyRim=1, .GapRadius=3, .Debug=0 (1 stencil IDs, 2 closed mask, 3 rim weight). Tree source defaults and SetTreeParameters/RefreshTree behavior are retained; no ticking native actor is added. The shared stencil allocator covers IDs 16-255 per world.

Validation is ongoing. Consult ../STATUS.json, ../source_tree_inspection.json, ../validation.json and actual render evidence. Successful native compilation alone is not a claim of final scene/runtime validation.
''',encoding='utf-8')
s=json.loads((work/'STATUS.json').read_text());now=datetime.datetime.now(datetime.timezone.utc);start=datetime.datetime.fromisoformat(s['started_at_utc'].replace('Z','+00:00'));s.update(elapsed_seconds=(now-start).total_seconds(),last_updated_at_utc=now.isoformat(),validation={'phase':'source component/runtime inspection and UE asset migration queued; private native build passed; before renders complete'},integration_proposal='ForestDemo/Work/ultra/SelfImprovement/IntegrationProposal',native_integration_status='proposal ready for supervisor installation/build; final scene validation pending');(work/'STATUS.json').write_text(json.dumps(s,indent=2))
print(json.dumps({'proposal_files':len(files),'elapsed_seconds':s['elapsed_seconds']}))
