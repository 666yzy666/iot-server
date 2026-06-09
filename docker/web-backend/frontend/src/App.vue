<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  // ====== Particle Canvas Background ======
  const c = document.createElement('canvas')
  c.id = 'particleCanvas'
  document.body.prepend(c)
  const ctx = c.getContext('2d')
  let dots = [], mouse = { x: -9999, y: -9999 }, W, H, anim

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    W = window.innerWidth; H = window.innerHeight
    c.width = W * dpr; c.height = H * dpr
    c.style.width = W + 'px'; c.style.height = H + 'px'
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    buildDots()
  }

  function buildDots() {
    const step = 16, cols = Math.floor(W / step), rows = Math.floor(H / step)
    const px = (W % step) / 2, py = (H % step) / 2
    dots = []
    for (let r = 0; r < rows; r++)
      for (let col = 0; col < cols; col++)
        dots.push({ ax: px + col * step + step / 2, ay: py + r * step + step / 2, x: 0, y: 0 })
  }

  function tick() {
    ctx.clearRect(0, 0, W, H)
    const rad = 1
    ctx.beginPath()
    for (let i = 0, len = dots.length; i < len; i++) {
      const d = dots[i], dx = mouse.x - d.ax, dy = mouse.y - d.ay
      let sx = d.ax, sy = d.ay
      const dist = dx * dx + dy * dy
      if (dist < 120000) {
        const t = 1 - Math.sqrt(dist) / 346, push = t * t * 30
        const angle = Math.atan2(dy, dx)
        sx = d.ax - Math.cos(angle) * push
        sy = d.ay - Math.sin(angle) * push
      }
      d.x += (sx - d.x) * 0.12
      d.y += (sy - d.y) * 0.12
      ctx.moveTo(d.x + rad, d.y)
      ctx.arc(d.x, d.y, rad, 0, Math.PI * 2)
    }
    ctx.fillStyle = 'rgba(139,92,246,0.12)'
    ctx.fill()
    anim = requestAnimationFrame(tick)
  }

  // ====== Glow Cursor ======
  const g = document.createElement('div')
  g.id = 'glowCursor'
  document.body.prepend(g)
  let cx = -999, cy = -999, tx = -999, ty = -999
  function glowAnim() {
    cx += (tx - cx) * 0.08
    cy += (ty - cy) * 0.08
    g.style.transform = 'translate(' + cx + 'px,' + cy + 'px) translate(-50%,-50%)'
    requestAnimationFrame(glowAnim)
  }

  const onMouse = (e) => { tx = e.clientX; ty = e.clientY; g.style.opacity = '1' }
  const onLeave = () => { g.style.opacity = '0' }
  window.addEventListener('mousemove', onMouse, { passive: true })
  document.addEventListener('mouseleave', onLeave)
  window.addEventListener('resize', resize)

  resize()
  tick()
  glowAnim()

  onUnmounted(() => {
    cancelAnimationFrame(anim)
    window.removeEventListener('mousemove', onMouse)
    document.removeEventListener('mouseleave', onLeave)
    window.removeEventListener('resize', resize)
    c.remove()
    g.remove()
  })
})
</script>
