"""Matte and register the two arm paintings from the approved design sheet."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ART=Path(__file__).resolve().parent
NATIVE=(704,854)
ARM_SCALE=.62
NEAR_ROOT=np.array([430.,266.])
FAR_ROOT=np.array([462.,276.])
NEAR_SHEET_ROOT=np.array([805.,412.])
FAR_SHEET_ROOT=np.array([1109.,426.])


def arm_coords(points,near):
    root,source=(NEAR_ROOT,NEAR_SHEET_ROOT) if near else (FAR_ROOT,FAR_SHEET_ROOT)
    return root+(np.asarray(points,dtype=float)-source)*ARM_SCALE


def remove_paper(patch,interior_seeds=()):
    rgb=np.asarray(patch.convert('RGB')).astype(float)
    sample=np.concatenate([rgb[0],rgb[-1],rgb[:,0],rgb[:,-1]])
    paper=np.median(sample,axis=0)
    difference=np.max(np.abs(rgb-paper),axis=2)
    barrier=Image.fromarray(np.where(difference<38,255,0).astype('uint8')).copy()
    for seed in [(0,0),*interior_seeds]:
        if barrier.getpixel(seed)==255:
            ImageDraw.floodfill(barrier,seed,120)
    solid=Image.fromarray(np.where(np.asarray(barrier)==120,0,255).astype('uint8'))
    edge=np.asarray(solid.filter(ImageFilter.MinFilter(3)))==0
    alpha=np.asarray(solid).astype(float)/255
    alpha[edge]*=np.clip((difference[edge]-14)/110,0,1)
    # Remove the warm paper contribution in partially covered outline pixels.
    foreground=(rgb-(1-alpha[:,:,None])*paper)/np.maximum(alpha[:,:,None],.001)
    pixels=np.dstack([np.clip(foreground,0,255),alpha*255]).round().astype('uint8')
    pixels[pixels[:,:,3]==0]=0
    return Image.fromarray(pixels)


def registered(patch,crop,near):
    offset=arm_coords(crop[:2],near)
    result=Image.new('RGBA',NATIVE)
    resized=patch.resize(tuple(round(x*ARM_SCALE) for x in patch.size),Image.Resampling.LANCZOS)
    result.alpha_composite(resized,tuple(np.round(offset).astype(int)))
    return result


def extract_arms(sheet_path,destination):
    destination.mkdir(parents=True,exist_ok=True)
    with Image.open(sheet_path) as original:
        if original.size!=(1536,1024):
            raise ValueError('The approved design sheet must be 1536×1024.')
        for near,crop,seeds,name in [
            (True,(737,352,944,820),(), 'near-arm.png'),
            (False,(1060,142,1490,853),((240,225),(160,500)), 'far-arm-bow.png'),
        ]:
            art=remove_paper(original.crop(crop),seeds)
            registered(art,crop,near).save(destination/name)


if __name__=='__main__':
    extract_arms(ART/'approved-design.png', ART/'layers')
