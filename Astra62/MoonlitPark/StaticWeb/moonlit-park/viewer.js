(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const rows = byId("strings").textContent.trim().split(/\r?\n/).map((row) => row.split(","));
  const languages = rows.shift();
  const requested = new URLSearchParams(location.search).get("lang") || navigator.language;
  let locale = requested.split("-")[0];
  if (locale === "zh") locale = /Hant|TW|HK|MO/i.test(requested) ? "zh-Hant" : "zh-Hans";
  if (!languages.includes(locale)) locale = "ko";
  const column = languages.indexOf(locale);
  const strings = Object.fromEntries(rows.map((row) => [row[0], row[column]]));
  document.documentElement.lang = locale;
  document.title = strings["park.title"];
  for (const element of document.querySelectorAll("[data-string]")) {
    element.textContent = strings[element.dataset.string];
  }
  for (const element of document.querySelectorAll("[data-alt]")) {
    element.alt = strings[element.dataset.alt];
  }
  for (const element of document.querySelectorAll("[data-aria]")) {
    const label = strings[element.dataset.aria];
    element.setAttribute("aria-label", label);
    if (element.tagName === "BUTTON") element.title = label;
  }

  const canvas = byId("scene");
  const stage = byId("stage");
  const picker = byId("model-file");
  const buttons = [...document.querySelectorAll(".controls button")];
  function notice(key, allowOpen = false) {
    byId("status").textContent = key ? strings[key] : "";
    byId("notice").hidden = !key;
    byId("open-model").hidden = !allowOpen;
  }
  function still(key, allowOpen = false) {
    document.body.classList.remove("ready");
    buttons.forEach((button) => { button.disabled = true; });
    byId("gesture").hidden = true;
    notice(key, allowOpen);
  }

  const T = window.Park3D;
  let renderer;
  try {
    renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "low-power" });
  } catch {
    still("park.unavailable");
    return;
  }
  renderer.outputColorSpace = T.SRGBColorSpace;
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  renderer.setClearColor(0x000000, 0);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate = false;

  const scene = new T.Scene();
  scene.add(new T.HemisphereLight(0xbccff7, 0x8389ab, 1.22));

  const camera = new T.OrthographicCamera(-10, 10, 8, -8, .1, 85);
  const homeDirection = new T.Vector3(1, 1.065, 1.10).normalize();
  const controls = new T.OrbitControls(camera, canvas);
  controls.enablePan = false;
  controls.minPolarAngle = .25;
  controls.maxPolarAngle = Math.PI * .455;
  controls.minZoom = .66;
  controls.maxZoom = 3.6;
  controls.rotateSpeed = .72;
  controls.zoomSpeed = .88;
  const homeTarget = new T.Vector3(0, 1, 0);
  let frameWidth = 18, frameHeight = 12, ready = false, frame = 0;
  const glowLights = [];
  const toCamera = new T.Vector3();
  function draw() {
    frame = 0;
    if (!ready || document.hidden) return;
    camera.getWorldDirection(toCamera).negate();
    for (const { sprite, origin } of glowLights) {
      sprite.position.copy(origin).addScaledVector(toCamera, .14);
    }
    renderer.render(scene, camera);
  }
  function invalidate() {
    if (!frame) frame = requestAnimationFrame(draw);
  }
  function resize() {
    const width = Math.max(stage.clientWidth, 1), height = Math.max(stage.clientHeight, 1);
    const aspect = width / height;
    const viewHeight = Math.max(frameHeight / .965, frameWidth / (.945 * aspect));
    camera.left = -viewHeight * aspect / 2;
    camera.right = -camera.left;
    camera.top = viewHeight / 2;
    camera.bottom = -camera.top;
    camera.updateProjectionMatrix();
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    invalidate();
  }
  function home() {
    camera.zoom = 1;
    controls.target.copy(homeTarget);
    camera.position.copy(homeTarget).addScaledVector(homeDirection, 26);
    camera.updateProjectionMatrix();
    controls.update();
    invalidate();
  }
  function fitModel(root) {
    home();
    camera.updateMatrixWorld();
    root.updateWorldMatrix(true, true);
    const point = new T.Vector3();
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    root.traverse((mesh) => {
      if (!mesh.isMesh) return;
      const positions = mesh.geometry.attributes.position;
      for (let i = 0; i < positions.count; i++) {
        point.fromBufferAttribute(positions, i).applyMatrix4(mesh.matrixWorld).applyMatrix4(camera.matrixWorldInverse);
        minX = Math.min(minX, point.x); maxX = Math.max(maxX, point.x);
        minY = Math.min(minY, point.y); maxY = Math.max(maxY, point.y);
      }
    });
    if (!Number.isFinite(minX) || maxX === minX || maxY === minY) throw new Error("Empty mesh");
    const offset = new T.Vector3((minX + maxX) / 2, (minY + maxY) / 2, 0).applyQuaternion(camera.quaternion);
    homeTarget.add(offset);
    frameWidth = maxX - minX;
    frameHeight = maxY - minY;
    home();
    resize();
  }
  function zoom(factor) {
    camera.zoom = Math.max(controls.minZoom, Math.min(controls.maxZoom, camera.zoom * factor));
    camera.updateProjectionMatrix();
    controls.update();
    syncButtons();
    invalidate();
  }
  function syncButtons() {
    byId("zoom-out").disabled = !ready || camera.zoom <= controls.minZoom + .001;
    byId("zoom-in").disabled = !ready || camera.zoom >= controls.maxZoom - .001;
    byId("home").disabled = !ready;
  }
  byId("zoom-in").addEventListener("click", () => zoom(1.25));
  byId("zoom-out").addEventListener("click", () => zoom(1 / 1.25));
  byId("home").addEventListener("click", home);
  controls.addEventListener("change", () => { syncButtons(); invalidate(); });
  canvas.addEventListener("keydown", (event) => {
    const key = event.key;
    if (["+", "=", "-", "Home", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(key)) event.preventDefault();
    else return;
    if (key === "Home") return home();
    if (key === "+" || key === "=" || key === "-") return zoom(key === "-" ? .8 : 1.25);
    const orbit = new T.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
    if (key === "ArrowLeft") orbit.theta -= .09;
    if (key === "ArrowRight") orbit.theta += .09;
    if (key === "ArrowUp") orbit.phi -= .07;
    if (key === "ArrowDown") orbit.phi += .07;
    orbit.phi = Math.max(controls.minPolarAngle, Math.min(controls.maxPolarAngle, orbit.phi));
    camera.position.setFromSpherical(orbit).add(controls.target);
    controls.update();
  });
  new ResizeObserver(resize).observe(stage);
  document.addEventListener("visibilitychange", invalidate);
  canvas.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    still("park.unavailable");
  });
  canvas.addEventListener("webglcontextrestored", () => location.reload());

  const glow = document.createElement("canvas");
  glow.width = glow.height = 96;
  const ctx = glow.getContext("2d");
  const gradient = ctx.createRadialGradient(48, 48, 0, 48, 48, 48);
  [[0, ".79"], [.16, ".55"], [.34, ".26"], [.60, ".080"], [1, "0"]].forEach(([t, alpha]) => {
    gradient.addColorStop(t, `rgba(255,170,73,${alpha})`);
  });
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 96, 96);
  const glowTexture = new T.CanvasTexture(glow);
  glowTexture.colorSpace = T.SRGBColorSpace;
  const glowMaterial = new T.SpriteMaterial({ map: glowTexture, blending: T.AdditiveBlending, depthWrite: false, transparent: true, toneMapped: false });
  const loader = new T.GLTFLoader();
  async function show(buffer) {
    const { scene: root } = await loader.parseAsync(buffer, "");
    fitModel(root);
    const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    root.traverse((object) => {
      if (object.isDirectionalLight && object.name === "Moonlight") {
        object.castShadow = true;
        object.shadow.mapSize.set(1536, 1536);
        Object.assign(object.shadow.camera, { left: -11, right: 11, top: 11, bottom: -11, near: .5, far: 35 });
        object.shadow.normalBias = .025;
        object.shadow.bias = -.00025;
      }
      if (object.isMesh) {
        object.receiveShadow = true;
        object.castShadow = object.material.name !== "Garden paths and grass";
        if (object.material.map) object.material.map.anisotropy = anisotropy;
      }
      if (object.isPointLight) {
        const sprite = new T.Sprite(glowMaterial);
        sprite.scale.setScalar(object.name.startsWith("Porch") ? .78 : 1.36);
        const origin = object.getWorldPosition(new T.Vector3());
        if (object.name.startsWith("Porch")) origin.set(2.40, 2.064, -.12);
        glowLights.push({ sprite, origin });
        scene.add(sprite);
      }
    });
    scene.add(root);
    renderer.shadowMap.needsUpdate = true;
    ready = true;
    document.body.classList.add("ready");
    byId("gesture").hidden = false;
    notice("");
    syncButtons();
    invalidate();
  }
  byId("open-model").addEventListener("click", () => picker.click());
  picker.addEventListener("change", async () => {
    const file = picker.files[0];
    if (!file) return;
    notice("park.loading");
    try { await show(await file.arrayBuffer()); }
    catch { still("park.failed", true); }
    picker.value = "";
  });
  async function start() {
    if (location.protocol === "file:") {
      still("park.local", true);
      return;
    }
    notice("park.loading");
    try {
      const response = await fetch("./assets/moonlit-park.glb");
      if (!response.ok) throw new Error(String(response.status));
      await show(await response.arrayBuffer());
    } catch {
      still("park.failed", true);
    }
  }
  start();
})();
