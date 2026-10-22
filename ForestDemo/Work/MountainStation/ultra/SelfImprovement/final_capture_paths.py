from pathlib import Path
R=Path(__file__).resolve().parent
for name in ['review_unreal.py','capture_views.py','publish_validated.py','finish_report.py','build_unreal.py']:
    p=R/name;s=p.read_text(encoding='utf-8')
    s=s.replace("'CAPTURE_PHASE':'after'","'CAPTURE_PHASE':'after_final'")
    s=s.replace("phase=='after'","phase.startswith('after')")
    s=s.replace('Screenshots/after/','Screenshots/after_final/').replace("Screenshots/after'","Screenshots/after_final'")
    s=s.replace("('Tunnel entrance fill',1.5,900.),('Tunnel inner fill',5.,650.)","('Tunnel entrance fill',1.5,35.),('Tunnel inner fill',5.,25.)")
    p.write_text(s,encoding='utf-8')
