import { onMounted, onUnmounted, ref } from 'vue'
import * as THREE from 'three'

// ===== GLSL Shaders =====
const face_vert = `attribute vec3 position;uniform vec2 px;uniform vec2 boundarySpace;varying vec2 uv;precision highp float;void main(){vec3 pos=position;vec2 scale=1.0-boundarySpace*2.0;pos.xy=pos.xy*scale;uv=vec2(0.5)+(pos.xy)*0.5;gl_Position=vec4(pos,1.0);}`
const advection_frag = `precision highp float;uniform sampler2D velocity;uniform float dt;uniform bool isBFECC;uniform vec2 fboSize;uniform vec2 px;varying vec2 uv;void main(){vec2 ratio=max(fboSize.x,fboSize.y)/fboSize;if(isBFECC==false){vec2 vel=texture2D(velocity,uv).xy;vec2 uv2=uv-vel*dt*ratio;vec2 newVel=texture2D(velocity,uv2).xy;gl_FragColor=vec4(newVel,0.0,0.0);}else{vec2 spot_new=uv;vec2 vel_old=texture2D(velocity,uv).xy;vec2 spot_old=spot_new-vel_old*dt*ratio;vec2 vel_new1=texture2D(velocity,spot_old).xy;vec2 spot_new2=spot_old+vel_new1*dt*ratio;vec2 error=spot_new2-spot_new;vec2 spot_new3=spot_new-error/2.0;vec2 vel_2=texture2D(velocity,spot_new3).xy;vec2 spot_old2=spot_new3-vel_2*dt*ratio;vec2 newVel2=texture2D(velocity,spot_old2).xy;gl_FragColor=vec4(newVel2,0.0,0.0);}}`
const color_frag = `precision highp float;uniform sampler2D velocity;uniform sampler2D palette;uniform vec4 bgColor;varying vec2 uv;void main(){vec2 vel=texture2D(velocity,uv).xy;float lenv=clamp(length(vel),0.0,1.0);vec3 c=texture2D(palette,vec2(lenv,0.5)).rgb;vec3 outRGB=mix(bgColor.rgb,c,lenv);float outA=mix(bgColor.a,1.0,lenv);gl_FragColor=vec4(outRGB,outA);}`
const divergence_frag = `precision highp float;uniform sampler2D velocity;uniform float dt;uniform vec2 px;varying vec2 uv;void main(){float x0=texture2D(velocity,uv-vec2(px.x,0.0)).x;float x1=texture2D(velocity,uv+vec2(px.x,0.0)).x;float y0=texture2D(velocity,uv-vec2(0.0,px.y)).y;float y1=texture2D(velocity,uv+vec2(0.0,px.y)).y;float divergence=(x1-x0+y1-y0)/2.0;gl_FragColor=vec4(divergence/dt);}`
const externalForce_frag = `precision highp float;uniform vec2 force;uniform vec2 center;uniform vec2 scale;uniform vec2 px;varying vec2 vUv;void main(){vec2 circle=(vUv-0.5)*2.0;float d=1.0-min(length(circle),1.0);d*=d;gl_FragColor=vec4(force*d,0.0,1.0);}`
const poisson_frag = `precision highp float;uniform sampler2D pressure;uniform sampler2D divergence;uniform vec2 px;varying vec2 uv;void main(){float p0=texture2D(pressure,uv+vec2(px.x*2.0,0.0)).r;float p1=texture2D(pressure,uv-vec2(px.x*2.0,0.0)).r;float p2=texture2D(pressure,uv+vec2(0.0,px.y*2.0)).r;float p3=texture2D(pressure,uv-vec2(0.0,px.y*2.0)).r;float div=texture2D(divergence,uv).r;float newP=(p0+p1+p2+p3)/4.0-div;gl_FragColor=vec4(newP);}`
const pressure_frag = `precision highp float;uniform sampler2D pressure;uniform sampler2D velocity;uniform vec2 px;uniform float dt;varying vec2 uv;void main(){float step=1.0;float p0=texture2D(pressure,uv+vec2(px.x*step,0.0)).r;float p1=texture2D(pressure,uv-vec2(px.x*step,0.0)).r;float p2=texture2D(pressure,uv+vec2(0.0,px.y*step)).r;float p3=texture2D(pressure,uv-vec2(0.0,px.y*step)).r;vec2 v=texture2D(velocity,uv).xy;vec2 gradP=vec2(p0-p1,p2-p3)*0.5;v=v-gradP*dt;gl_FragColor=vec4(v,0.0,1.0);}`
const viscous_frag = `precision highp float;uniform sampler2D velocity;uniform sampler2D velocity_new;uniform float v;uniform vec2 px;uniform float dt;varying vec2 uv;void main(){vec2 old=texture2D(velocity,uv).xy;vec2 new0=texture2D(velocity_new,uv+vec2(px.x*2.0,0.0)).xy;vec2 new1=texture2D(velocity_new,uv-vec2(px.x*2.0,0.0)).xy;vec2 new2=texture2D(velocity_new,uv+vec2(0.0,px.y*2.0)).xy;vec2 new3=texture2D(velocity_new,uv-vec2(0.0,px.y*2.0)).xy;vec2 newv=4.0*old+v*dt*(new0+new1+new2+new3);newv/=4.0*(1.0+v*dt);gl_FragColor=vec4(newv,0.0,0.0);}`
const line_vert = `attribute vec3 position;uniform vec2 px;precision highp float;varying vec2 uv;void main(){vec3 pos=position;uv=0.5+pos.xy*0.5;vec2 n=sign(pos.xy);pos.xy=abs(pos.xy)-px*1.0;pos.xy*=n;gl_Position=vec4(pos,1.0);}`
const mouse_vert = `precision highp float;attribute vec3 position;attribute vec2 uv;uniform vec2 center;uniform vec2 scale;uniform vec2 px;varying vec2 vUv;void main(){vec2 pos=position.xy*scale*2.0*px+center;vUv=uv;gl_Position=vec4(pos,0.0,1.0);}`

// ===== makePaletteTexture =====
function makePaletteTexture(stops) {
  let arr = stops.length ? (stops.length === 1 ? [stops[0], stops[0]] : stops) : ['#ffffff', '#ffffff']
  const w = arr.length
  const data = new Uint8Array(w * 4)
  for (let i = 0; i < w; i++) { const c = new THREE.Color(arr[i]); data[i * 4] = Math.round(c.r * 255); data[i * 4 + 1] = Math.round(c.g * 255); data[i * 4 + 2] = Math.round(c.b * 255); data[i * 4 + 3] = 255 }
  const tex = new THREE.DataTexture(data, w, 1, THREE.RGBAFormat)
  tex.magFilter = tex.minFilter = THREE.LinearFilter
  tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping
  tex.generateMipmaps = false; tex.needsUpdate = true
  return tex
}

// ===== Helpers =====
function setupCommon() {
  let width = 0, height = 0, pixelRatio = 1
  let renderer = null, clock = null
  let time = 0, delta = 0
  let container = null

  function init(el) {
    container = el; pixelRatio = Math.min(window.devicePixelRatio || 1, 2)
    resize()
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.autoClear = false
    renderer.setClearColor(new THREE.Color(0x000000), 0)
    renderer.setPixelRatio(pixelRatio)
    renderer.setSize(width, height)
    const canvas = renderer.domElement
    canvas.style.cssText = 'width:100%;height:100%;display:block;position:absolute;top:0;left:0'
    clock = new THREE.Clock()
    return canvas
  }

  function resize() {
    if (!container) return
    const rect = container.getBoundingClientRect()
    width = Math.max(1, Math.floor(rect.width))
    height = Math.max(1, Math.floor(rect.height))
    if (renderer) renderer.setSize(width, height, false)
  }

  function update() {
    if (!clock) return
    delta = clock.getDelta(); time += delta
  }

  return { get width() { return width }, get height() { return height }, init, resize, update, pixelRatio, get renderer() { return renderer } }
}

function setupMouse() {
  const coords = new THREE.Vector2()
  const coords_old = new THREE.Vector2()
  const diff = new THREE.Vector2()
  let isHoverInside = false, hasUserControl = false, isAutoActive = false
  let container = null, timer = null
  let onInteract = null

  function isPointInside(cx, cy) {
    if (!container) return false
    const rect = container.getBoundingClientRect()
    return cx >= rect.left && cx <= rect.right && cy >= rect.top && cy <= rect.bottom
  }

  function setCoords(x, y) {
    if (!container) return; if (timer) clearTimeout(timer)
    const rect = container.getBoundingClientRect()
    const nx = (x - rect.left) / rect.width; const ny = (y - rect.top) / rect.height
    coords.set(nx * 2 - 1, -(ny * 2 - 1))
    if (onInteract) onInteract()
    timer = setTimeout(() => {}, 100)
  }

  function setNormalized(nx, ny) { coords.set(nx, ny) }

  function onMouseMove(e) { if (!isPointInside(e.clientX, e.clientY)) return; setCoords(e.clientX, e.clientY); hasUserControl = true }
  function onTouchStart(e) { if (e.touches.length !== 1) return; const t = e.touches[0]; if (isPointInside(t.clientX, t.clientY)) { setCoords(t.clientX, t.clientY); hasUserControl = true } }
  function onTouchMove(e) { if (e.touches.length !== 1) return; const t = e.touches[0]; if (isPointInside(t.clientX, t.clientY)) setCoords(t.clientX, t.clientY) }
  function onTouchEnd() { isHoverInside = false }
  function onDocLeave() { isHoverInside = false }

  function init(el) {
    container = el
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('touchstart', onTouchStart, { passive: true })
    window.addEventListener('touchmove', onTouchMove, { passive: true })
    window.addEventListener('touchend', onTouchEnd)
    document.addEventListener('mouseleave', onDocLeave)
  }

  function dispose() {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('touchstart', onTouchStart)
    window.removeEventListener('touchmove', onTouchMove)
    window.removeEventListener('touchend', onTouchEnd)
    document.removeEventListener('mouseleave', onDocLeave)
    if (timer) clearTimeout(timer)
  }

  function update() {
    diff.subVectors(coords, coords_old)
    coords_old.copy(coords)
    if (isAutoActive) diff.multiplyScalar(2.2)
  }

  return { init, dispose, update, setNormalized, get coords() { return coords }, get diff() { return diff }, get isHoverInside() { return isHoverInside },
    set onInteract(fn) { onInteract = fn }, set isAutoActive(v) { isAutoActive = v }, set hasUserControl(v) { hasUserControl = v } }
}

// ===== Shader Pass =====
class ShaderPass {
  constructor(props) { this.props = props || {}; this.uniforms = this.props.material?.uniforms }
  init() {
    this.scene = new THREE.Scene(); this.camera = new THREE.Camera()
    if (this.uniforms) { this.material = new THREE.RawShaderMaterial(this.props.material); this.geometry = new THREE.PlaneGeometry(2, 2); this.plane = new THREE.Mesh(this.geometry, this.material); this.scene.add(this.plane) }
  }
  render(renderer) { if (renderer && this.scene && this.camera) { renderer.setRenderTarget(this.props.output || null); renderer.render(this.scene, this.camera); renderer.setRenderTarget(null) } }
}

// ===== Advection =====
class AdvectionPass extends ShaderPass {
  constructor(props) {
    super({ material: { vertexShader: face_vert, fragmentShader: advection_frag, uniforms: { boundarySpace: { value: new THREE.Vector2(0.003, 0.003) }, velocity: { value: null }, dt: { value: 0.016 }, isBFECC: { value: true }, fboSize: { value: new THREE.Vector2(256, 256) }, px: { value: new THREE.Vector2(1 / 256, 1 / 256) } } }, output: props.dst })
    this.init()
    const bg = new THREE.BufferGeometry()
    const vb = new Float32Array([-1, -1, 0, -1, 1, 0, -1, 1, 0, 1, 1, 0, 1, 1, 0, 1, -1, 0, 1, -1, 0, -1, -1, 0])
    bg.setAttribute('position', new THREE.BufferAttribute(vb, 3))
    const bm = new THREE.RawShaderMaterial({ vertexShader: line_vert, fragmentShader: advection_frag, uniforms: this.uniforms })
    this.line = new THREE.LineSegments(bg, bm)
    this.scene.add(this.line)
  }
  render(renderer, opts) {
    if (opts) { if (typeof opts.dt === 'number') this.uniforms.dt.value = opts.dt; if (typeof opts.BFECC === 'boolean') this.uniforms.isBFECC.value = opts.BFECC; this.line.visible = !!opts.isBounce }
    super.render(renderer)
  }
}

// ===== ExternalForce =====
class ExternalForcePass extends ShaderPass {
  constructor(props) {
    super({ output: props.dst })
    this.init()
    const mg = new THREE.PlaneGeometry(1, 1)
    const mm = new THREE.RawShaderMaterial({ vertexShader: mouse_vert, fragmentShader: externalForce_frag, blending: THREE.AdditiveBlending, depthWrite: false, uniforms: { px: { value: props.cellScale }, force: { value: new THREE.Vector2(0, 0) }, center: { value: new THREE.Vector2(0, 0) }, scale: { value: new THREE.Vector2(props.cursorSize, props.cursorSize) } } })
    this.mouse = new THREE.Mesh(mg, mm); this.scene.add(this.mouse)
  }
  render(renderer, opts) {
    const forceX = (opts.diff.x / 2) * opts.mouseForce; const forceY = (opts.diff.y / 2) * opts.mouseForce
    const cs = opts.cursorSize; const cx = opts.cellScale.x; const cy = opts.cellScale.y
    const mx = Math.min(Math.max(opts.coords.x, -1 + cs * cx + cx * 2), 1 - cs * cx - cx * 2)
    const my = Math.min(Math.max(opts.coords.y, -1 + cs * cy + cy * 2), 1 - cs * cy - cy * 2)
    const u = this.mouse.material.uniforms
    u.force.value.set(forceX, forceY); u.center.value.set(mx, my); u.scale.value.set(cs, cs)
    super.render(renderer)
  }
}

// ===== Divergence =====
class DivergencePass extends ShaderPass {
  constructor(props) { super({ material: { vertexShader: face_vert, fragmentShader: divergence_frag, uniforms: { boundarySpace: { value: props.boundarySpace }, velocity: { value: null }, px: { value: props.cellScale }, dt: { value: 0.016 } } }, output: props.dst }); this.init() }
  render(renderer, opts) { if (opts.vel) this.uniforms.velocity.value = opts.vel.texture; super.render(renderer) }
}

// ===== Poisson =====
class PoissonPass extends ShaderPass {
  constructor(props) { super({ material: { vertexShader: face_vert, fragmentShader: poisson_frag, uniforms: { boundarySpace: { value: props.boundarySpace }, pressure: { value: null }, divergence: { value: null }, px: { value: props.cellScale } } }, output: props.dst, output0: props.dst_, output1: props.dst }); this.init() }
  render(renderer, opts) {
    let pin, pout; const iter = opts.iterations || 0
    for (let i = 0; i < iter; i++) { pin = i % 2 === 0 ? this.props.output0 : this.props.output1; pout = i % 2 === 0 ? this.props.output1 : this.props.output0; this.uniforms.pressure.value = pin.texture; this.props.output = pout; super.render(renderer) }
    return pout
  }
}

// ===== Pressure =====
class PressurePass extends ShaderPass {
  constructor(props) { super({ material: { vertexShader: face_vert, fragmentShader: pressure_frag, uniforms: { boundarySpace: { value: props.boundarySpace }, pressure: { value: null }, velocity: { value: null }, px: { value: props.cellScale }, dt: { value: 0.016 } } }, output: props.dst }); this.init() }
  render(renderer, opts) { if (opts.vel && opts.pressure) { this.uniforms.velocity.value = opts.vel.texture; this.uniforms.pressure.value = opts.pressure.texture } super.render(renderer) }
}

// ===== Simulation =====
class Simulation {
  constructor(opts) {
    this.options = Object.assign({ iterationsPoisson: 32, iterationsViscous: 32, mouseForce: 20, resolution: 0.5, cursorSize: 100, viscous: 30, isBounce: false, dt: 0.014, isViscous: false, BFECC: true }, opts || {})
    this.fbos = {}; this.cellScale = new THREE.Vector2(); this.boundarySpace = new THREE.Vector2(); this.fboSize = new THREE.Vector2()
  }
  init(cw, ch) {
    this.calcSize(cw, ch); this.createFBOs(); this.createPasses()
  }
  getFloatType() { return /(iPad|iPhone|iPod)/i.test(navigator.userAgent) ? THREE.HalfFloatType : THREE.FloatType }
  createFBOs() {
    const opts = { type: this.getFloatType(), depthBuffer: false, stencilBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, wrapS: THREE.ClampToEdgeWrapping, wrapT: THREE.ClampToEdgeWrapping }
    ;['vel_0', 'vel_1', 'vel_v0', 'vel_v1', 'div', 'p_0', 'p_1'].forEach(k => { this.fbos[k] = new THREE.WebGLRenderTarget(this.fboSize.x, this.fboSize.y, opts) })
  }
  createPasses() {
    this.advection = new AdvectionPass({ dst: this.fbos.vel_1 })
    this.externalForce = new ExternalForcePass({ dst: this.fbos.vel_1, cellScale: this.cellScale, cursorSize: this.options.cursorSize })
    this.divergence = new DivergencePass({ dst: this.fbos.div, boundarySpace: this.boundarySpace, cellScale: this.cellScale })
    this.poisson = new PoissonPass({ dst: this.fbos.p_1, dst_: this.fbos.p_0, boundarySpace: this.boundarySpace, cellScale: this.cellScale })
    this.pressure = new PressurePass({ dst: this.fbos.vel_0, boundarySpace: this.boundarySpace, cellScale: this.cellScale })
  }
  calcSize(cw, ch) {
    const w = Math.max(1, Math.round(this.options.resolution * cw))
    const h = Math.max(1, Math.round(this.options.resolution * ch))
    this.cellScale.set(1 / w, 1 / h); this.fboSize.set(w, h)
  }
  resize(cw, ch) { this.calcSize(cw, ch); Object.values(this.fbos).forEach(f => f.setSize(this.fboSize.x, this.fboSize.y)) }
  update(renderer, opts) {
    this.boundarySpace.copy(opts.isBounce ? new THREE.Vector2(0, 0) : this.cellScale)
    this.advection.render(renderer, { dt: opts.dt, isBounce: opts.isBounce, BFECC: opts.BFECC })
    this.externalForce.render(renderer, { diff: opts.diff, coords: opts.coords, mouseForce: opts.mouseForce, cursorSize: opts.cursorSize, cellScale: this.cellScale })
    this.divergence.render(renderer, { vel: this.fbos.vel_1 })
    const pressure = this.poisson.render(renderer, { iterations: opts.iterationsPoisson })
    this.pressure.render(renderer, { vel: this.fbos.vel_1, pressure })
  }
}

// ===== Output =====
class OutputRenderer {
  constructor(paletteTex, bgVec4) {
    this.paletteTex = paletteTex; this.bgVec4 = bgVec4; this.simulation = null
    this.scene = new THREE.Scene(); this.camera = new THREE.Camera()
  }
  init(cw, ch) {
    this.simulation = new Simulation()
    this.simulation.init(cw, ch)
    this.output = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.RawShaderMaterial({
      vertexShader: face_vert, fragmentShader: color_frag, transparent: true, depthWrite: false,
      uniforms: { velocity: { value: this.simulation.fbos.vel_0.texture }, boundarySpace: { value: new THREE.Vector2() }, palette: { value: this.paletteTex }, bgColor: { value: this.bgVec4 } }
    }))
    this.scene.add(this.output)
  }
  resize(cw, ch) { if (this.simulation) this.simulation.resize(cw, ch) }
  render(renderer, rat) {
    this.simulation.update(renderer, this.simulation.options)
    if (this.output) { this.output.material.uniforms.velocity.value = this.simulation.fbos.vel_0.texture }
    renderer.setRenderTarget(null); renderer.render(this.scene, this.camera)
  }
}

// ===== Main Composable =====
export function useLiquidEther(options = {}) {
  const containerRef = ref(null)
  const colors = options.colors || ['#5227FF', '#FF9FFC', '#B497CF']

  let webgl = null, animId = null, running = false
  let paletteTex = null, bgVec4 = null
  let common = null, mouse = null, output = null

  onMounted(() => {
    const el = containerRef.value
    if (!el) return
    el.style.position = 'relative'; el.style.overflow = 'hidden'

    paletteTex = makePaletteTexture(colors)
    bgVec4 = new THREE.Vector4(0, 0, 0, 0)

    common = setupCommon()
    const canvas = common.init(el)
    el.prepend(canvas)

    mouse = setupMouse()
    mouse.init(el)

    const cw = common.width, ch = common.height
    output = new OutputRenderer(paletteTex, bgVec4)
    output.init(cw, ch)

    let lastInteraction = 0
    mouse.onInteract = () => { lastInteraction = performance.now() }

    running = true
    function loop() {
      if (!running) return
      mouse.update()
      common.update()
      if (output) output.render(common.renderer)
      animId = requestAnimationFrame(loop)
    }
    loop()

    const onResize = () => {
      common.resize()
      if (output) output.resize(common.width, common.height)
    }
    window.addEventListener('resize', onResize)

    onUnmounted(() => {
      running = false
      if (animId) cancelAnimationFrame(animId)
      window.removeEventListener('resize', onResize)
      if (mouse) mouse.dispose()
      if (common.renderer) { const c = common.renderer.domElement; if (c && c.parentNode) c.parentNode.removeChild(c); common.renderer.dispose(); common.renderer.forceContextLoss() }
    })
  })

  return containerRef
}
