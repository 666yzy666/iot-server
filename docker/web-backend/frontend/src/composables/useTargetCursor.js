import { onMounted, onUnmounted } from 'vue'
import { gsap } from 'gsap'

export function useTargetCursor(options = {}) {
  const { targetSelector = '.cursor-target', spinDuration = 2 } = options
  let cleanup = null

  function init() {
    if (typeof window === 'undefined' || window.innerWidth <= 768) return

    const body = document.body
    body.style.cursor = 'none'

    const wrap = document.createElement('div')
    wrap.id = 'targetCursor'
    wrap.innerHTML = [
      '<div class="tc-dot"></div>',
      '<div class="tc-corner tc-tl"></div>',
      '<div class="tc-corner tc-tr"></div>',
      '<div class="tc-corner tc-br"></div>',
      '<div class="tc-corner tc-bl"></div>',
    ].join('')
    document.body.appendChild(wrap)

    const dot = wrap.querySelector('.tc-dot')
    const corners = [wrap.querySelector('.tc-tl'), wrap.querySelector('.tc-tr'), wrap.querySelector('.tc-br'), wrap.querySelector('.tc-bl')]

    function createSpin() {
      const tl = gsap.timeline({ repeat: -1 })
      tl.to(wrap, { rotation: '+=360', duration: spinDuration, ease: 'none' })
      return tl
    }
    let spinTl = createSpin()
    gsap.set(wrap, { xPercent: -50, yPercent: -50, x: window.innerWidth / 2, y: window.innerHeight / 2 })

    const onMove = (e) => gsap.to(wrap, { x: e.clientX, y: e.clientY, duration: 0.12, ease: 'power3.out' })
    window.addEventListener('mousemove', onMove)

    const onEnter = (e) => {
      const target = e.target.closest(targetSelector)
      if (!target) return
      const rect = target.getBoundingClientRect()
      const pad = 4, cs = 12
      spinTl.pause()
      gsap.killTweensOf(corners)
      gsap.set(wrap, { rotation: 0 })

      const pos = [
        { x: rect.left - pad, y: rect.top - pad },
        { x: rect.right + pad - cs, y: rect.top - pad },
        { x: rect.right + pad - cs, y: rect.bottom + pad - cs },
        { x: rect.left - pad, y: rect.bottom + pad - cs },
      ]
      corners.forEach((el, i) => {
        gsap.to(el, {
          x: pos[i].x - gsap.getProperty(wrap, 'x'),
          y: pos[i].y - gsap.getProperty(wrap, 'y'),
          duration: 0.25, ease: 'power2.out',
        })
      })

      const onLeave = () => {
        const off = 18
        const reset = [
          { x: -off, y: -off },
          { x: off - cs + 6, y: -off },
          { x: off - cs + 6, y: off - cs + 6 },
          { x: -off, y: off - cs + 6 },
        ]
        corners.forEach((el, i) => gsap.to(el, { x: reset[i].x, y: reset[i].y, duration: 0.3, ease: 'power3.out' }))
        setTimeout(() => { spinTl = createSpin(); spinTl.play() }, 50)
        target.removeEventListener('mouseleave', onLeave)
      }
      target.addEventListener('mouseleave', onLeave)
    }
    window.addEventListener('mouseover', onEnter)

    const onDown = () => { gsap.to(dot, { scale: 0.6, duration: 0.2 }); gsap.to(wrap, { scale: 0.9, duration: 0.15 }) }
    const onUp = () => { gsap.to(dot, { scale: 1, duration: 0.2 }); gsap.to(wrap, { scale: 1, duration: 0.15 }) }
    window.addEventListener('mousedown', onDown)
    window.addEventListener('mouseup', onUp)

    cleanup = () => {
      body.style.cursor = ''
      spinTl.kill()
      wrap.remove()
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseover', onEnter)
      window.removeEventListener('mousedown', onDown)
      window.removeEventListener('mouseup', onUp)
    }
  }

  onMounted(init)
  onUnmounted(() => { if (cleanup) cleanup() })
}
