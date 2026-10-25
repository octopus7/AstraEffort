from publish_delivery import *
data=read('render_analysis.json')
write('visual_review.json',{
    'utc':datetime.now(timezone.utc).isoformat(),
    'accepted':True,
    'method':'Parent directly inspected all seven final original UE PNGs with view_image after prop correction. Independent reviewer inspected refreshed evidence separately.',
    'image_sha256':{r['name']:r['sha256'] for r in data['images']},
    'observations':{
        'overview':'Coherent quiet farm; mill, barn, shed, four fenced fields and connected dirt approaches. Upright trees and architecture.',
        'top_down':'Complete square 100m footprint visible; four fields and broad connected route visible, no blank capture.',
        'windmill':'Readable canvas/lattice sails, tiled cap, wood gallery, stone entrance and plaster; rounded game art.',
        'farm_detail':'Cart, barn facade, separated barrel and shed readable. Mill partly cropped intentionally for detail composition.',
        'prop_contact':'Upper bale visibly supported on lower pair and all bales stand clear of barn rear wall; numerical gap/clearance saved separately.',
        'windmill_motion_t0_t1':'Clearly changed sail angles in the same camera. Pixel difference includes moving shadow and temporal rendering, not isolated rotor-only measurement.'},
    'limitations':['Dark shaded faces are intentional dynamic sun/skylight lighting.','This is visual review of recorded viewpoints, not an exhaustive every-actor contact or human-input walkthrough.'],
    'independent_review':'QA/implementation_review.md'})
print('Recorded visual review of seven inspected final renders.')
