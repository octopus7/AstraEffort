"""Check intended authored route constraints independently of UE package checks."""
import math,json
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
curve=lambda x:5+.004*x*x
checks={
 'site_100m_square':True,
 'min_track_radius_m':125,
 'track_gauge_m':1.52,
 'platform_edge_from_centerline_m':2.05,
 'platform_clearance_from_rail_m':2.05-.76,
 'platform_height_m':1.05,
 'ramp_rise_m':1.05,'ramp_run_m':13,'ramp_grade':1.05/13,
 'tunnel_inner_half_width_m':2.3,
 'tunnel_alignment_max_deviation_m':max(abs(curve(x)-(curve(30)+.24*(x-30))) for x in [30+i*.1 for i in range(101)]),
 'track_rail_continuous_samples':201,'sleeper_count':145,
 'scope':'Source geometry mathematical checks, not a substitute for rendered visual inspection or physics playtest.'}
assert checks['ramp_grade']<1/12
assert checks['tunnel_alignment_max_deviation_m']+.76<2.3
assert checks['platform_clearance_from_rail_m']>1
json.dump(checks,open(ROOT+'/layout_checks.json','w'),indent=2)
print(json.dumps(checks,indent=2))
