import * as THREE from 'three';
import { OrbitControls } from './vendor/controls/OrbitControls.js';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';

const status = document.querySelector('#status');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9c9f9d);
scene.fog = new THREE.Fog(0x9c9f9d, 110, 250);
const camera = new THREE.PerspectiveCamera(40, innerWidth/innerHeight, 0.1, 600);
const renderer = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
renderer.setSize(innerWidth,innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
const hemi = new THREE.HemisphereLight(0xe7ebeb,0x635848,2.1);scene.add(hemi);
const sunlight = new THREE.DirectionalLight(0xffe1b5,3.0);sunlight.position.set(-24,42,-18);sunlight.castShadow=true;
sunlight.shadow.mapSize.set(2048,2048);Object.assign(sunlight.shadow.camera,{left:-65,right:65,top:65,bottom:-65,near:1,far:180});sunlight.shadow.bias=-0.0003;scene.add(sunlight);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(240,240),new THREE.MeshStandardMaterial({color:0x75716b,roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-0.025;floor.receiveShadow=true;scene.add(floor);
const controls = new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(-6,4,16);controls.maxDistance=180;controls.minDistance=3;controls.maxPolarAngle=Math.PI*.49;
const presets={overview:{p:[51,30,-43],t:[7,4,17]},front:{p:[4,16,-55],t:[8,5,12]},inside:{p:[1,3.1,-4],t:[0,4,22]},top:{p:[6,75,16],t:[6,0,16]}};
function cameraPreset(name){const v=presets[name];camera.position.set(...v.p);controls.target.set(...v.t);controls.update()}
cameraPreset('overview');
document.querySelectorAll('[data-camera]').forEach(b=>b.addEventListener('click',()=>cameraPreset(b.dataset.camera)));
const loader=new GLTFLoader();
const manifestName=new URLSearchParams(location.search).has('check_assembled')?'__verify_manifest.json':'manifest.json';
const manifest=await fetch('./assets/'+manifestName).then(r=>{if(!r.ok)throw Error('manifest: '+r.status);return r.json()});
let good=0;const failed=[];
for(const entry of manifest.assets){
 try{
   const asset=await loader.loadAsync('./assets/'+entry.file);
   asset.scene.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;if(o.material && o.material.side===THREE.FrontSide && entry.doubleSided)o.material.side=THREE.DoubleSide}});
   for(const placement of entry.placements){const copy=asset.scene.clone(true);copy.position.set(...placement.position);if(placement.rotation)copy.rotation.set(...placement.rotation);if(placement.scale)copy.scale.set(...placement.scale);scene.add(copy)}
   good++;
 }catch(e){console.error('Could not load',entry.file,e);failed.push(entry.file)}
 status.textContent=`불러온 모듈 ${good} / ${manifest.assets.length}`;
}
if(failed.length){status.textContent=`모듈 ${good}개 로드됨. 실패: ${failed.join(', ')}`;status.classList.add('error')}
else status.textContent=`모듈 ${good}개 로드 완료 · ${manifest.bays}개 구간 조립`;
window.stationReady=true;window.stationReport={good,failed};
window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera)});
