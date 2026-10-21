import sys,time,json
from pathlib import Path
sys.path.insert(0,r'C:/Program Files/Epic Games/UE_5.7/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python')
import remote_execution
r=remote_execution.RemoteExecution()
try:
 r.start();time.sleep(3)
 nodes=[n for n in r.remote_nodes if 'Saved/Workers/ultra/SelfImprovement/ForestDemo' in str(n).replace('\\','/')]
 print(json.dumps({'matching_private_nodes':nodes,'total_discovered':len(r.remote_nodes)}))
finally:r.stop()
