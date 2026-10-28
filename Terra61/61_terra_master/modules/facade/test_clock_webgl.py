#!/usr/bin/env python3
"""Regression: Three.js GLTFLoader dial must survive backing depth at distance.

Compare the center of the angled clock render with and without the backing
materials under the same lighting. The opaque dial should cover the backing;
per-pixel differences from z-fighting are not allowed. Render with shadows both
on and off to distinguish depth fighting from ordinary shadowing.
"""
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
subprocess.run(['node',str(ROOT/'qa_clock.cjs')],check=True,stdout=subprocess.DEVNULL)
y,x=np.mgrid[:900,:1200]
mask=((x-600)/145)**2+((y-450)/170)**2<1
pairs=[('angled_noshadow','angled_no_backing_noshadow'),('angled_shadow','angled_no_backing')]
failures=[]
for normal,control in pairs:
 a=np.asarray(Image.open(ROOT/f'qa_{normal}.png').convert('RGB')).astype(np.int16)
 b=np.asarray(Image.open(ROOT/f'qa_{control}.png').convert('RGB')).astype(np.int16)
 diff=np.mean(np.abs(a-b),axis=2)[mask]
 frac=float(np.mean(diff>25))
 print(f'{normal}: {frac:.2%} of dial pixels differ strongly from isolated dial')
 if frac>.03:failures.append(f'{normal}: {frac:.2%} > 3% threshold')
lit=np.asarray(Image.open(ROOT/'qa_angled_noshadow.png').convert('RGB')).astype(np.int16)
shadow=np.asarray(Image.open(ROOT/'qa_angled_shadow.png').convert('RGB')).astype(np.int16)
shadow_diff=np.mean(np.abs(lit-shadow),axis=2)[mask]
shadow_p95=float(np.percentile(shadow_diff,95))
print(f'shadow on/off 95th percentile difference: {shadow_p95:.2f} / 255')
if shadow_p95>8:failures.append(f'visible dial shadow artifact: p95 {shadow_p95:.2f} > 8')
assert not failures, 'Visible dial depth conflict: ' + '; '.join(failures)
print('PASS: clock face remains visually intact with backing and with shadows on/off')
