"use strict";

const pixelStage = document.querySelector("#stage");
const playToggles = document.querySelectorAll(".play-toggle");
const positions = document.querySelectorAll(".timeline input");
const speedButtons = document.querySelectorAll("button[data-speed]");
const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
const cycleMs = 1000;

let playing = !motionPreference.matches;
let speed = 1;
let originPhase = 0;
let originTime = performance.now();
let animationId = 0;

// All studies sample the same one-second clock.
function phaseAt(time) {
  if (!playing) return originPhase;
  return (originPhase + (time - originTime) * speed / cycleMs) % 1;
}

function makeStrip(sheet) {
  const count = Number(sheet.dataset.count);
  const study = sheet.closest("[data-scene-study]");
  const sample = sheet.querySelector(".sheet-live");
  const lane = sample || pixelStage.querySelector('[data-count="' + count + '"]');
  const films = [lane.querySelector("img")];
  if (study) films.push(study.querySelector('.scene-actor[data-count="' + count + '"] img'));
  const original = sheet.querySelector(".original");
  const cellSize = Number(original.getAttribute("height"));
  const strip = document.createElement("div");
  strip.className = "frame-strip count-" + count;
  strip.setAttribute("role", "group");
  strip.setAttribute("aria-label", count + "프레임 시트. 방향키로 프레임 선택");
  strip.style.setProperty("--count", count);
  strip.style.setProperty("--sheet", 'url("' + original.getAttribute("src") + '")');

  const cells = [];
  for (let index = 0; index < count; index++) {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "frame-cell";
    cell.tabIndex = index === 0 ? 0 : -1;
    cell.dataset.frame = index;
    cell.setAttribute("aria-label", count + "프레임 시트의 " + (index + 1) + "번 프레임에서 멈춤");
    cell.style.setProperty("--offset", -(cellSize * index) + "px");

    const pose = document.createElement("span");
    pose.className = "pose";
    pose.setAttribute("aria-hidden", "true");
    const ordinal = document.createElement("span");
    ordinal.className = "frame-index";
    ordinal.setAttribute("aria-hidden", "true");
    ordinal.textContent = String(index + 1).padStart(2, "0");
    cell.append(pose, ordinal);
    cells.push(cell);
    strip.append(cell);
  }

  function inspect(index) {
    for (const cell of cells) cell.tabIndex = -1;
    cells[index].tabIndex = 0;
    cells[index].focus({ preventScroll: true });
    if (study) selectFeature(study, count);
    seek(index / count);
  }

  strip.addEventListener("click", event => {
    const cell = event.target.closest(".frame-cell");
    if (cell) inspect(Number(cell.dataset.frame));
  });
  strip.addEventListener("keydown", event => {
    const index = Number(event.target.dataset.frame);
    if (!Number.isInteger(index)) return;
    const targets = {
      ArrowLeft: (index + count - 1) % count,
      ArrowRight: (index + 1) % count,
      Home: 0,
      End: count - 1
    };
    if (!(event.key in targets)) return;
    event.preventDefault();
    inspect(targets[event.key]);
  });

  original.hidden = true;
  original.after(strip);
  return { count, lane, films, cells, current: -1 };
}

if (location.protocol === "file:") {
  for (const link of document.querySelectorAll("a[download]")) {
    link.removeAttribute("download");
    link.target = "_blank";
    link.rel = "noopener";
    if (link.lastChild.nodeType === Node.TEXT_NODE) {
      link.lastChild.textContent = link.lastChild.textContent.replace("저장", "열기");
    }
    link.setAttribute("aria-label", link.getAttribute("aria-label").replace("저장", "열기"));
  }
}

const versions = Array.from(document.querySelectorAll(".sheet"), makeStrip);

function render(phase) {
  for (const version of versions) {
    const frame = Math.min(version.count - 1, Math.floor(phase * version.count));
    if (frame === version.current) continue;
    if (version.current >= 0) version.cells[version.current].removeAttribute("aria-current");
    version.cells[frame].setAttribute("aria-current", "step");
    for (const film of version.films) {
      film.style.setProperty("--offset", (-100 * frame / version.count) + "%");
    }
    version.lane.dataset.frame = frame;
    version.current = frame;
  }
  const percent = (phase * 100).toFixed(1) + "%";
  for (const position of positions) {
    position.value = Math.round(phase * cycleMs);
    position.style.setProperty("--progress", percent);
    position.setAttribute("aria-valuetext", Math.round(phase * 100) + "%");
  }
}

function draw() {
  render(phaseAt(performance.now()));
  if (playing && !document.hidden) animationId = requestAnimationFrame(draw);
}

function refreshPlayback() {
  cancelAnimationFrame(animationId);
  for (const toggle of playToggles) {
    toggle.classList.toggle("is-playing", playing);
    toggle.querySelector(".play-label").textContent = playing ? "일시정지" : "재생";
  }
  draw();
}

function seek(phase) {
  playing = false;
  originPhase = phase;
  originTime = performance.now();
  refreshPlayback();
}

function togglePlayback() {
  const now = performance.now();
  originPhase = phaseAt(now);
  originTime = now;
  playing = !playing;
  refreshPlayback();
}

for (const toggle of playToggles) toggle.addEventListener("click", togglePlayback);

for (const position of positions) {
  position.addEventListener("input", () => seek(Number(position.value) / cycleMs));
}

for (const button of speedButtons) {
  button.addEventListener("click", () => {
    const now = performance.now();
    originPhase = phaseAt(now);
    originTime = now;
    speed = Number(button.dataset.speed);
    for (const choice of speedButtons) choice.setAttribute("aria-pressed", choice.dataset.speed === button.dataset.speed);
  });
}

for (const group of document.querySelectorAll("[data-backdrop-controls]")) {
  const stage = document.getElementById(group.dataset.backdropControls);
  const choices = group.querySelectorAll("button[data-backdrop]");
  for (const button of choices) {
    button.addEventListener("click", () => {
      stage.dataset.backdrop = button.dataset.backdrop;
      for (const choice of choices) choice.setAttribute("aria-pressed", choice === button);
    });
  }
}

function selectFeature(study, count) {
  const stage = study.querySelector(".illustrated-scene");
  for (const actor of stage.querySelectorAll(".scene-actor")) {
    actor.hidden = Number(actor.dataset.count) !== count;
  }
  for (const button of study.querySelectorAll("button[data-feature]")) {
    button.setAttribute("aria-pressed", Number(button.dataset.feature) === count);
  }
  const sceneLink = study.querySelector(".scene-link");
  sceneLink.href = "./scene.html?frames=" + count + sceneLink.hash;
  const medium = study.querySelector(".art-medium").textContent;
  stage.setAttribute("aria-label", "꽃활을 든 금발 엘프의 " + count + "프레임 오른쪽 걷기 " + medium);
}

for (const study of document.querySelectorAll("[data-scene-study]")) {
  for (const button of study.querySelectorAll("button[data-feature]")) {
    button.addEventListener("click", () => selectFeature(study, Number(button.dataset.feature)));
  }
}

function revealLinkedLayers() {
  if (location.hash === "#anime-layers") document.getElementById("anime-layers").open = true;
}

window.addEventListener("hashchange", revealLinkedLayers);
revealLinkedLayers();
document.addEventListener("visibilitychange", refreshPlayback);
motionPreference.addEventListener("change", event => {
  if (event.matches && playing) seek(phaseAt(performance.now()));
});
document.documentElement.classList.replace("no-js", "js");
refreshPlayback();
