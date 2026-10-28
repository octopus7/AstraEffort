import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const qs=new URLSearchParams(location.search);if(qs.has('clean'))document.body.classList.add('clean');
const assetSelect=document.querySelector('#asset');assetSelect.value=(qs.get('model')||'').replace('../modules/','').replace('.glb','');assetSelect.onchange=()=>{location.search=assetSelect.value?'?model=../modules/'+assetSelect.value+'.glb':''};
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;document.body.prepend(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#b5bec4');scene.fog=new THREE.Fog('#b5bec4',150,340);
const camera=new THREE.PerspectiveCamera(42,innerWidth/innerHeight,.15,600);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.49;
const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.08).texture;scene.environmentIntensity=.48;
scene.add(new THREE.HemisphereLight(0xc8ddf4,0x73614b,1.7));
const sun=new THREE.DirectionalLight(0xffdfb0,3.1);sun.position.set(-55,75,40);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-95,right:95,top:75,bottom:-75,near:1,far:230});sun.shadow.bias=-.00012;sun.shadow.normalBias=.05;sun.target.position.set(-15,0,-15);scene.add(sun,sun.target);
const fill=new THREE.DirectionalLight(0xb7d3ff,1);fill.position.set(40,20,-60);scene.add(fill);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(450,450),new THREE.MeshStandardMaterial({color:0x8a8a7f,roughness:.98}));floor.rotation.x=-Math.PI/2;floor.position.y=-.035;floor.receiveShadow=true;scene.add(floor);
const presets={hero:{pos:[45,33,65],target:[-20,10,-18],fov:40},platform:{pos:[17,6,10],target:[-6,5,-22],fov:52},facade:{pos:[-38,12,68],target:[-38,12,-2],fov:38},train:{pos:[16,5.4,15],target:[5.5,2.4,-3],fov:46},aerial:{pos:[55,92,83],target:[-17,0,-19],fov:43}};
function view(name){let p=presets[name]||presets.hero;camera.position.fromArray(p.pos);camera.fov=p.fov;camera.updateProjectionMatrix();controls.target.fromArray(p.target);controls.update();document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===name));}
window.setView=(name)=>{view(name);renderer.render(scene,camera)};view(qs.get('view')||'hero');
window.freezeRender=()=>{renderer.setAnimationLoop(null);controls.enableDamping=false;controls.update();renderer.render(scene,camera)};
let model,roofParts=[],wire=false;
const loader=new GLTFLoader();
function optimize(root){
 root.updateMatrixWorld(true);const buckets=new Map(),leaves=[];
 root.traverse(o=>{if(!o.isMesh)return;leaves.push(o);let roof=false;for(let p=o;p;p=p.parent)if(/roof|glass/i.test(p.name))roof=true;
  const mat=o.material;mat.side=mat.side??THREE.FrontSide;if(mat.map)mat.map.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
  const key=o.geometry.uuid+'|'+mat.uuid+'|'+roof;let b=buckets.get(key);if(!b)buckets.set(key,b={g:o.geometry,m:mat,trans:[],roof});b.trans.push(o.matrixWorld.clone());
 });
 const combined=new THREE.Group();combined.name='Render instances';
 for(const b of buckets.values()){
  const im=new THREE.InstancedMesh(b.g,b.m,b.trans.length);b.trans.forEach((m,i)=>im.setMatrixAt(i,m));im.instanceMatrix.needsUpdate=true;im.computeBoundingSphere();im.castShadow=!b.m.transparent;im.receiveShadow=true;combined.add(im);if(b.roof&&b.m.transparent)roofParts.push(im);
 }
 return combined;
}
async function load(){
 try{
  const path=qs.get('model')||'../Riverdale_Station_assembled.glb';const gltf=await loader.loadAsync(path);model=optimize(gltf.scene);scene.add(model);
  if(qs.has('model')){
   const box=new THREE.Box3().setFromObject(model);const c=box.getCenter(new THREE.Vector3()),s=box.getSize(new THREE.Vector3());const r=Math.max(s.x,s.y,s.z);controls.target.copy(c);camera.position.copy(c).add(new THREE.Vector3(r*.95,r*.52,r*1.1));camera.fov=42;camera.updateProjectionMatrix();controls.update();sun.target.position.copy(c);
  }
  if(qs.get('roof')==='0')roofParts.forEach(p=>p.visible=false);
  document.querySelector('#loading').style.display='none';renderer.render(scene,camera);sun.shadow.autoUpdate=false;document.querySelector('#status').textContent=`${renderer.info.render.triangles.toLocaleString()} triangles · ${renderer.info.render.calls} draw calls`;
  window.stationReady=true;window.stationModel=model;window.stationInfo={meshes:model.children.length,triangles:renderer.info.render.triangles};
 }catch(e){window.stationError=e.message;document.querySelector('#loading').textContent='모델을 불러오지 못했습니다. start_viewer.py로 열어 주세요.';console.error(e);}
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));
document.querySelector('#roof').onclick=e=>{const show=roofParts.length?!roofParts[0].visible:true;roofParts.forEach(p=>p.visible=show);e.target.textContent=show?'유리 지붕 숨기기':'유리 지붕 보이기';};
document.querySelector('#wire').onclick=e=>{wire=!wire;model?.traverse(o=>{if(o.isMesh)o.material.wireframe=wire});e.target.textContent=wire?'재질 보기':'와이어 표시';};
window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera)});load();
