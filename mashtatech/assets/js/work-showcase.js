// Curved WebGL project showcase ("our work" section).
// Built with OGL (https://github.com/oframe/ogl), loaded by the caller.
// Exports init(container, opts) -> { destroy() }.

const VERT = `
  attribute vec3 position;
  attribute vec2 uv;
  uniform mat4 modelMatrix;
  uniform mat4 modelViewMatrix;
  uniform mat4 projectionMatrix;
  uniform float uStrength;
  uniform float uHalfViewportWidth;
  uniform float uVelocity;
  uniform float uCardCenterX;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    vec3 p = position;
    vec4 world = modelMatrix * vec4(p, 1.0);
    float d = (world.x + uCardCenterX) / uHalfViewportWidth;
    d = clamp(d, -1.5, 1.5);
    p.z -= (d * d) * uStrength * 12.0;
    p.z -= abs(uVelocity) * 0.5;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }
`;

const FRAG = `
  precision highp float;
  uniform sampler2D tMap;
  uniform float uOpacity;
  varying vec2 vUv;
  void main() {
    vec4 tex = texture2D(tMap, vUv);
    gl_FragColor = vec4(tex.rgb, tex.a * uOpacity);
  }
`;

const GRID_VERT = `
  attribute vec3 position;
  attribute vec2 uv;
  uniform mat4 modelMatrix;
  uniform mat4 modelViewMatrix;
  uniform mat4 projectionMatrix;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const GRID_FRAG = `
  precision highp float;
  varying vec2 vUv;
  uniform float uOpacity;
  void main() {
    vec2 uv = vUv * 2.0 - 1.0;
    vec2 grid = fract(vUv * vec2(24.0, 40.0));
    float lineX = smoothstep(0.0, 0.03, grid.x) * smoothstep(1.0, 0.97, grid.x);
    float lineY = smoothstep(0.0, 0.03, grid.y) * smoothstep(1.0, 0.97, grid.y);
    float line = 1.0 - min(lineX, lineY);
    float radial = 1.0 - smoothstep(0.15, 1.0, length(uv));
    float depth = 1.0 - smoothstep(0.0, 1.0, vUv.y);
    float alpha = line * radial * depth * 0.35 * uOpacity;
    gl_FragColor = vec4(vec3(1.0), alpha);
  }
`;

export async function init(container, opts = {}) {
  const OGL = await import('https://cdn.jsdelivr.net/npm/ogl@1.0.6/src/index.js');
  const { Renderer, Camera, Transform, Plane, Program, Mesh, Texture } = OGL;

  const projects = opts.projects || [];
  const onActivate = opts.onActivate || (() => {});
  const rtl = !!opts.rtl;
  const reducedMotionStrength = opts.reducedStrength ?? 0.35;

  const CARD_ASPECT = 1.4;
  const CARD_HEIGHT_WORLD = 2.6;
  const CARD_WIDTH_WORLD = CARD_HEIGHT_WORLD * CARD_ASPECT;
  const GAP_WORLD = 0.16;
  const STEP = CARD_WIDTH_WORLD + GAP_WORLD;

  let strength = 0.35;
  let disposed = false;

  const renderer = new Renderer({ dpr: Math.min(window.devicePixelRatio || 1, 2), alpha: false, antialias: true });
  const gl = renderer.gl;
  gl.clearColor(0, 0, 0, 1);
  container.appendChild(gl.canvas);
  gl.canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;';

  const camera = new Camera(gl, { fov: 35, near: 0.1, far: 100 });
  camera.position.set(0, 0.55, 6.2);
  camera.lookAt([0, -0.05, 0]);

  const scene = new Transform();

  let halfViewportWidth = 1;
  function computeHalfViewportWidth() {
    const distance = camera.position.z;
    const vFov = (camera.fov * Math.PI) / 180;
    const visibleHeight = 2 * Math.tan(vFov / 2) * distance;
    const visibleWidth = visibleHeight * camera.aspect;
    halfViewportWidth = visibleWidth / 2;
  }

  function resize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    renderer.setSize(w, h);
    camera.perspective({ aspect: w / h });
    computeHalfViewportWidth();
  }

  // --- Grid floor ---
  const gridGeometry = new Plane(gl, { width: 40, height: 40, widthSegments: 1, heightSegments: 1 });
  const gridProgram = new Program(gl, {
    vertex: GRID_VERT,
    fragment: GRID_FRAG,
    uniforms: { uOpacity: { value: 0 } },
    transparent: true,
    depthWrite: false,
  });
  const gridMesh = new Mesh(gl, { geometry: gridGeometry, program: gridProgram });
  gridMesh.rotation.x = -Math.PI / 2;
  gridMesh.position.y = -1.35;
  gridMesh.position.z = -6;
  gridMesh.setParent(scene);

  // --- Cards ---
  const SEGMENTS = 32;
  const cardGeometry = new Plane(gl, {
    width: CARD_WIDTH_WORLD,
    height: CARD_HEIGHT_WORLD,
    widthSegments: SEGMENTS,
    heightSegments: SEGMENTS,
  });

  const maxAniso = gl.renderer.parameters.maxAnisotropy || 1;

  const cards = projects.map((proj, i) => {
    const texture = new Texture(gl, { generateMipmaps: true, anisotropy: maxAniso });
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => { texture.image = img; };
    img.src = proj.poster;

    const program = new Program(gl, {
      vertex: VERT,
      fragment: FRAG,
      uniforms: {
        tMap: { value: texture },
        uStrength: { value: strength },
        uHalfViewportWidth: { value: halfViewportWidth },
        uVelocity: { value: 0 },
        uCardCenterX: { value: 0 },
        uOpacity: { value: 1 },
      },
      transparent: true,
    });

    const mesh = new Mesh(gl, { geometry: cardGeometry, program });
    mesh.setParent(scene);
    return { mesh, program, texture, proj, index: i, videoEl: null, videoActive: false };
  });

  const n = cards.length;
  let dir = rtl ? -1 : 1;

  const scroll = { current: 0, target: 0, last: 0 };
  let velocity = 0;
  let smoothedVelocity = 0;

  const totalWidth = STEP * n;
  // Wrap each card to whichever copy of it (base position + k*totalWidth)
  // sits closest to center, so a card's world.x only ever changes by a
  // continuous amount frame to frame instead of snapping across the seam.
  function wrapX(x) {
    return x - Math.round(x / totalWidth) * totalWidth;
  }

  function updateCardPositions() {
    cards.forEach((card) => {
      const baseX = card.index * STEP * dir;
      const x = wrapX(baseX - scroll.current * dir);
      card.mesh.position.x = x;
      card.program.uniforms.uCardCenterX.value = x;
      card.program.uniforms.uVelocity.value = smoothedVelocity;
      card.program.uniforms.uHalfViewportWidth.value = halfViewportWidth;
      card.program.uniforms.uStrength.value = strength;
    });
  }

  // --- Drag / wheel input ---
  let isDown = false;
  let startX = 0;
  let startScroll = 0;

  function onPointerDown(e) {
    isDown = true;
    startX = (e.touches ? e.touches[0].clientX : e.clientX);
    startScroll = scroll.target;
    container.style.cursor = 'grabbing';
  }
  function onPointerMove(e) {
    if (!isDown) return;
    const x = (e.touches ? e.touches[0].clientX : e.clientX);
    const delta = (x - startX) * 0.01;
    scroll.target = startScroll - delta;
  }
  function onPointerUp() {
    isDown = false;
    container.style.cursor = 'grab';
  }
  function onWheel(e) {
    e.preventDefault();
    scroll.target += (e.deltaY || e.deltaX) * 0.003;
  }

  container.style.cursor = 'grab';
  container.addEventListener('mousedown', onPointerDown);
  window.addEventListener('mousemove', onPointerMove);
  window.addEventListener('mouseup', onPointerUp);
  container.addEventListener('touchstart', onPointerDown, { passive: true });
  container.addEventListener('touchmove', onPointerMove, { passive: true });
  container.addEventListener('touchend', onPointerUp);
  container.addEventListener('wheel', onWheel, { passive: false });

  function step() {
    scroll.current += (scroll.target - scroll.current) * 0.08;
    velocity = scroll.current - scroll.last;
    scroll.last = scroll.current;
    // Smooth velocity itself so the shader's extra Z-bend during drag
    // ramps in/out instead of flickering with per-frame timing noise.
    smoothedVelocity += (velocity - smoothedVelocity) * 0.15;
    updateCardPositions();
  }

  // --- Video swap (poster -> video near center, cap concurrent plays) ---
  const MAX_PLAYING = 4;
  function updateVideoActivation() {
    const active = cards
      .map((c) => ({ c, dist: Math.abs(c.mesh.position.x) }))
      .sort((a, b) => a.dist - b.dist)
      .slice(0, MAX_PLAYING)
      .map((e) => e.c);

    cards.forEach((card) => {
      const shouldPlay = active.includes(card) && card.dist < STEP * 1.5 && !!card.proj.video;
      if (shouldPlay && !card.videoActive) {
        if (!card.videoEl) {
          const v = document.createElement('video');
          v.src = card.proj.video;
          v.muted = true;
          v.loop = true;
          v.playsInline = true;
          v.crossOrigin = 'anonymous';
          card.videoEl = v;
        }
        card.videoEl.play().catch(() => {});
        card.videoActive = true;
      } else if (!shouldPlay && card.videoActive) {
        card.videoEl && card.videoEl.pause();
        card.videoActive = false;
      }
    });
  }

  // --- DOM overlay for labels/buttons (accessible, projected each frame) ---
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:absolute;inset:0;pointer-events:none;';
  container.appendChild(overlay);

  const labelEls = cards.map((card, i) => {
    const wrap = document.createElement('div');
    wrap.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;opacity:0;transition:opacity .6s ease;';
    wrap.innerHTML = `
      <div class="showcase-label" style="font-family:'Frank Ruhl Libre',serif;font-weight:400;color:#fff;white-space:nowrap;"></div>
      <button class="showcase-arrow" type="button" aria-hidden="true" tabindex="-1" style="pointer-events:auto;border:none;border-radius:50%;background:rgba(14,16,14,.82);color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;">&#8594;</button>
    `;
    overlay.appendChild(wrap);
    const btn = wrap.querySelector('.showcase-arrow');
    btn.addEventListener('click', () => onActivate(card.proj, i));
    return wrap;
  });

  function project(vec3) {
    camera.updateMatrixWorld();
    const v = vec3.clone().applyMatrix4(camera.projectionViewMatrix);
    const w = container.clientWidth;
    const h = container.clientHeight;
    return {
      x: (v.x * 0.5 + 0.5) * w,
      y: (1 - (v.y * 0.5 + 0.5)) * h,
    };
  }

  // Mirrors the vertex shader's parabolic push-back so CPU-side label
  // projection matches what the GPU actually renders for each card.
  function bentZ(worldX) {
    const d = Math.max(-1.5, Math.min(1.5, worldX / halfViewportWidth));
    return -(d * d) * strength * 12.0 - Math.abs(smoothedVelocity) * 0.5;
  }

  function updateLabels() {
    const w = container.clientWidth;
    cards.forEach((card, i) => {
      const el = labelEls[i];
      const distNorm = Math.abs(card.mesh.position.x) / (STEP * 1.5);
      const visible = distNorm < 1;
      if (!visible) { el.style.opacity = '0'; return; }
      const scale = 1 - Math.min(distNorm, 1) * 0.35;
      const bottomLeft = card.mesh.position.clone();
      bottomLeft.x -= CARD_WIDTH_WORLD / 2;
      bottomLeft.y -= CARD_HEIGHT_WORLD / 2;
      bottomLeft.z = card.mesh.position.z + bentZ(card.mesh.position.x);
      const screen = project(bottomLeft);
      el.style.opacity = String(Math.max(0, 1 - distNorm * 1.4));
      el.style.transform = `translate(${screen.x + 18}px, ${screen.y - 74}px) scale(${scale})`;
      const nameEl = el.querySelector('.showcase-label');
      nameEl.style.fontSize = Math.round(34 * scale) + 'px';
    });
  }

  // --- Intro animation ---
  let introT = 0;
  const introDuration = 600;
  let introStart = null;
  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

  camera.position.z = 6.2 + 6;
  gridProgram.uniforms.uOpacity.value = 0;

  let raf = null;
  function frame(time) {
    if (disposed) return;
    if (introStart === null) introStart = time;
    const t = Math.min(1, (time - introStart) / introDuration);
    const eased = easeOutCubic(t);
    camera.position.z = 6.2 + (1 - eased) * 6;
    gridProgram.uniforms.uOpacity.value = eased;
    if (t >= 1 && introT < 1) {
      introT = 1;
      labelEls.forEach((el, i) => setTimeout(() => { el.style.opacity = '1'; }, i * 60));
    }

    step();
    updateVideoActivation();
    updateLabels();
    renderer.render({ scene, camera });
    raf = requestAnimationFrame(frame);
  }

  resize();
  updateCardPositions();
  const ro = new ResizeObserver(resize);
  ro.observe(container);
  raf = requestAnimationFrame(frame);

  function setStrength(v) { strength = v; }
  setStrength(opts.strength ?? 0.35);

  function destroy() {
    disposed = true;
    if (raf) cancelAnimationFrame(raf);
    ro.disconnect();
    container.removeEventListener('mousedown', onPointerDown);
    window.removeEventListener('mousemove', onPointerMove);
    window.removeEventListener('mouseup', onPointerUp);
    container.removeEventListener('touchstart', onPointerDown);
    container.removeEventListener('touchmove', onPointerMove);
    container.removeEventListener('touchend', onPointerUp);
    container.removeEventListener('wheel', onWheel);
    cards.forEach((card) => {
      card.mesh.geometry.remove();
      card.program.remove();
      card.texture.image = null;
      if (card.videoEl) { card.videoEl.pause(); card.videoEl.src = ''; }
    });
    gridGeometry.remove();
    gridProgram.remove();
    if (gl.canvas.parentNode) gl.canvas.parentNode.removeChild(gl.canvas);
    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
  }

  return {
    destroy,
    setStrength,
    goTo(i) { scroll.target = i * STEP * dir; },
    setRtl(isRtl) {
      dir = isRtl ? -1 : 1;
      scroll.current = 0;
      scroll.target = 0;
      scroll.last = 0;
    },
  };
}
