import { onMounted, onUnmounted, ref } from 'vue'

export function useDotField(options = {}) {
  const containerRef = ref(null)

  const DEFAULTS = {
    density: 1.0,       // particle density multiplier
    speed: 0.3,         // drift speed
    lineDistance: 120,  // max px for line connections
    repelRadius: 100,   // mouse repel radius
    repelStrength: 8,   // mouse repel force
    color: '168,85,247',// RGB of dot/line color (primary purple)
    dotRadius: 1.8,
    fadeLines: true,
  }

  const cfg = { ...DEFAULTS, ...options }
  let canvas, ctx, W, H, dpr
  let particles = []
  let mouse = { x: -9999, y: -9999 }
  let animId = null
  let running = false

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2)
    W = window.innerWidth
    H = window.innerHeight
    canvas.width = W * dpr
    canvas.height = H * dpr
    canvas.style.width = W + 'px'
    canvas.style.height = H + 'px'
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    rebuildParticles()
  }

  function rebuildParticles() {
    const count = Math.floor(Math.min(W, H) * 0.5 * cfg.density)
    particles = []
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * cfg.speed,
        vy: (Math.random() - 0.5) * cfg.speed,
        ox: Math.random() * 100, // phase offset for gentle wobble
        oy: Math.random() * 100,
      })
    }
  }

  function tick() {
    if (!running) return
    ctx.clearRect(0, 0, W, H)

    const time = performance.now() * 0.001
    const repelSq = cfg.repelRadius * cfg.repelRadius
    const lineSq = cfg.lineDistance * cfg.lineDistance

    // Update particles
    for (const p of particles) {
      // Gentle wandering
      p.x += p.vx + Math.sin(time + p.ox) * 0.08
      p.y += p.vy + Math.cos(time + p.oy) * 0.08

      // Mouse repel
      const dx = p.x - mouse.x
      const dy = p.y - mouse.y
      const distSq = dx * dx + dy * dy
      if (distSq < repelSq && distSq > 0) {
        const dist = Math.sqrt(distSq)
        const force = (1 - dist / cfg.repelRadius) * cfg.repelStrength
        p.x += (dx / dist) * force
        p.y += (dy / dist) * force
      }

      // Wrap around edges
      if (p.x < -10) p.x = W + 10
      if (p.x > W + 10) p.x = -10
      if (p.y < -10) p.y = H + 10
      if (p.y > H + 10) p.y = -10
    }

    // Draw lines between close particles
    const len = particles.length
    for (let i = 0; i < len; i++) {
      for (let j = i + 1; j < len; j++) {
        const a = particles[i], b = particles[j]
        const dx = a.x - b.x
        const dy = a.y - b.y
        const distSq = dx * dx + dy * dy
        if (distSq < lineSq) {
          const alpha = (1 - Math.sqrt(distSq) / cfg.lineDistance) * 0.45
          ctx.beginPath()
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(b.x, b.y)
          ctx.strokeStyle = `rgba(${cfg.color},${alpha})`
          ctx.lineWidth = 0.6
          ctx.stroke()
        }
      }
    }

    // Draw dots
    ctx.fillStyle = `rgba(${cfg.color},0.7)`
    for (const p of particles) {
      ctx.beginPath()
      ctx.arc(p.x, p.y, cfg.dotRadius, 0, Math.PI * 2)
      ctx.fill()
    }

    animId = requestAnimationFrame(tick)
  }

  function moveHandler(e) {
    mouse.x = e.clientX
    mouse.y = e.clientY
  }
  function leaveHandler() {
    mouse.x = -9999
    mouse.y = -9999
  }

  onMounted(() => {
    try {
      const el = containerRef.value
      if (!el) return
      canvas = document.createElement('canvas')
      ctx = canvas.getContext('2d')
      canvas.style.cssText = 'display:block;position:absolute;top:0;left:0;width:100%;height:100%'
      el.style.overflow = 'hidden'
      el.prepend(canvas)

      resize()
      running = true
      tick()

      window.addEventListener('resize', resize)
      window.addEventListener('mousemove', moveHandler, { passive: true })
      document.addEventListener('mouseleave', leaveHandler)

      onUnmounted(() => {
        running = false
        if (animId) cancelAnimationFrame(animId)
        window.removeEventListener('resize', resize)
        window.removeEventListener('mousemove', moveHandler)
        document.removeEventListener('mouseleave', leaveHandler)
        if (canvas && canvas.parentNode) canvas.parentNode.removeChild(canvas)
      })
    } catch (e) {
      console.error('[DotField] init error:', e)
    }
  })

  return containerRef
}
