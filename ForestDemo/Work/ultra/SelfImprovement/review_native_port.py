import ast,json,hashlib,datetime
from pathlib import Path
out=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
tree=ast.parse((out/'prepare_plugin.py').read_text())
replacements=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='replacement' for t in n.targets))
port=json.loads((out/'native_port_manifest.json').read_text());rows=[]
for r in port['source_files']:
 expected=Path(r['source']).read_text(encoding='utf-8-sig')
 for a,b in replacements:expected=expected.replace(a,b)
 actual=Path(r['destination']).read_text()
 rows.append({'source':r['source'],'port':r['destination'],'only_declared_mechanical_changes':expected==actual})
manifest=json.loads((out/'IntegrationProposal/manifest.json').read_text());proposal=[]
for r in manifest['files']:
 p=out/'IntegrationProposal'/r['path'];proposal.append({'path':r['path'],'manifest_matches':hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']})
report={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'review_type':'Inline source review and exact normalized source comparison; no independent reviewer used.','source_comparisons':rows,'proposal_files':proposal,'review_notes':['Plugin loads at PostConfigInit, before global shader type initialization; native build and fresh editor load passed.','Shader path resolves through IPluginManager, independent of the source project directory.','Renderer styles are copied to render-thread-owned values; no UObject pointers are stored in render data.','FWorldSceneViewExtension restricts the renderer to its world; stencil ownership is weak and capped at IDs 16-255. The scene uses 63 unique IDs.','Leaf and hidden-shadow MIDs are per actor; refresh destroys old proxy components before rebuilding, verified by inspection.','Trunk collision uses complex-as-simple geometry; leaf/proxy collision disabled. Actual PIE collision validation remains separate.','Native gradient CPD getter is not reflected into Python. Rendered guide movement will supply behavioral evidence; no direct CPD read pass is claimed.'],'limitations':['Packaged-game build and non-D3D12 render backends are not tested.','The shared r.CustomDepth setting is supervisor-owned and requires integration before publication.'],'success':all(r['only_declared_mechanical_changes'] for r in rows) and all(r['manifest_matches'] for r in proposal)}
(out/'native_code_review.json').write_text(json.dumps(report,indent=2));print(json.dumps({'success':report['success'],'source_files':len(rows),'proposal_files':len(proposal)}))
