// Port of Coda's useCarousel (useCarousel-DE99UO_7.js) as used by the card carousel:
// snapElement ".carousel-snap", spacerElement ".carousel-spacer", slide true, no target/secondary
// size elements, setOuterHeight false. See CLONE_SPEC.md §7.
import { useCallback, useEffect, useRef, useState } from 'react'

// react-use useWindowSize: state updated on the next animation frame after a resize event.
function useWindowWidth() {
  const [width, setWidth] = useState(() => (typeof window !== 'undefined' ? window.innerWidth : Infinity))
  useEffect(() => {
    let raf = 0
    const onResize = () => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(() => setWidth(window.innerWidth))
    }
    window.addEventListener('resize', onResize)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', onResize)
    }
  }, [])
  return width
}

export function useCarousel({ snapElement, spacerElement, startEnabled = true, startControls = true, slide = true }) {
  const carouselRef = useRef(null)
  const width = useWindowWidth()
  const [current, setCurrent] = useState(0)
  const [enabled] = useState(startEnabled)
  const controlsRef = useRef(startControls)
  const currentRef = useRef(0)
  const itemsRef = useRef(null)
  const spacerRef = useRef(null)
  const stateRef = useRef([])
  const drag = useRef({ down: false, dragged: false, start: { x: 0, y: 0 }, delta: { x: 0, y: 0 }, current: { xLerp: 0, yLerp: 0 } })

  const next = useCallback(() => {
    const n = itemsRef.current?.length || 1
    currentRef.current = currentRef.current + 1 < n ? currentRef.current + 1 : 0
    setCurrent(currentRef.current)
  }, [])
  const prev = useCallback(() => {
    const n = itemsRef.current?.length || 1
    currentRef.current = currentRef.current - 1 >= 0 ? currentRef.current - 1 : n - 1
    setCurrent(currentRef.current)
  }, [])

  useEffect(() => {
    currentRef.current = current
  }, [current])

  // Measure items; (re)initialise per-item lerp state on width change, exactly as live (xLerp resets to 0).
  useEffect(() => {
    const root = carouselRef.current
    itemsRef.current = root?.querySelectorAll(snapElement) || null
    spacerRef.current = (spacerElement ? root?.querySelector(spacerElement) : null) || null
    const links = root?.querySelectorAll('a')
    const block = (e) => { if (controlsRef.current) e.preventDefault() }
    const blockClick = (e) => {
      if (controlsRef.current && drag.current.dragged) { e.preventDefault(); e.stopPropagation() }
    }
    itemsRef.current?.forEach((el, i) => {
      if (enabled) {
        el.style.setProperty('position', 'absolute')
        el.style.setProperty('left', '0px')
        el.style.setProperty('top', '0px')
        el.style.setProperty('transition', 'none')
        el.style.setProperty('user-select', 'none')
      } else {
        ;['position', 'left', 'top', 'transition', 'user-select'].forEach((p) => el.style.removeProperty(p))
      }
      const img = el.querySelector('img')
      if (img) enabled ? img.style.setProperty('transition', 'none') : img.style.removeProperty('transition')
      stateRef.current[i] = { x: 0, w: 0, h: 0, xLerp: 0 }
    })
    links?.forEach((a) => {
      a.addEventListener('mousedown', block, false)
      a.addEventListener('mousemove', block, false)
      a.addEventListener('click', blockClick, false)
    })
    return () => {
      links?.forEach((a) => {
        a.removeEventListener('mousedown', block, false)
        a.removeEventListener('mousemove', block, false)
        a.removeEventListener('click', blockClick, false)
      })
    }
  }, [width, enabled, snapElement, spacerElement])

  // rAF loop (react-use useRafLoop). Live's 1000/60 throttle compares against a ref that is never
  // updated, so it never skips; every frame runs.
  useEffect(() => {
    let raf = 0
    const tick = () => {
      const d = drag.current
      d.current.xLerp += (d.delta.x - d.current.xLerp) * 0.2
      d.current.yLerp += (d.delta.y - d.current.yLerp) * 0.2
      const items = itemsRef.current
      if (items && carouselRef.current) {
        let x = 0
        let target = 0
        const gap = spacerRef.current?.offsetWidth || 0
        items.forEach((el, i) => {
          const s = stateRef.current[i]
          s.x = x
          s.w = el.offsetWidth
          s.h = el.offsetHeight
          if (i === currentRef.current) target = x
          x += s.w + gap
        })
        items.forEach((el, i) => {
          const s = stateRef.current[i]
          s.xLerp += (s.x - target + d.current.xLerp - s.xLerp) * 0.125
          s.xLerp = Math.round(s.xLerp * 1e3) / 1e3
          if (enabled && slide) el.style.transform = `translateX(${s.xLerp}px)`
          else el.style.removeProperty('transform')
        })
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [enabled, slide])

  // Window pointer listeners + touchmove suppression while dragging.
  useEffect(() => {
    const root = carouselRef.current
    const end = () => {
      if (!controlsRef.current) return
      const d = drag.current
      if (d.down) { d.down = false; d.delta.x = 0; d.delta.y = 0 }
    }
    const down = (e) => {
      if (controlsRef.current && e.target instanceof HTMLElement && root?.contains(e.target)) {
        const d = drag.current
        d.start.x = e.clientX; d.start.y = e.clientY; d.down = true; d.dragged = false
      }
    }
    const move = (e) => {
      if (!controlsRef.current) return
      const d = drag.current
      if (!d.down) return
      d.delta.x = e.clientX - d.start.x
      d.delta.y = e.clientY - d.start.y
      if (Math.abs(d.delta.x) > 10) d.dragged = true
      if (Math.abs(d.delta.x) > (itemsRef.current?.[0]?.offsetWidth || window.innerWidth) * 0.15) {
        d.delta.x < 0 ? next() : prev()
        end()
      }
    }
    const touchmove = (e) => {
      if (controlsRef.current && drag.current.dragged && drag.current.down) { e.preventDefault(); e.stopPropagation() }
    }
    const opts = { passive: true }
    window.addEventListener('pointerdown', down, opts)
    window.addEventListener('pointermove', move, opts)
    window.addEventListener('pointerup', end, opts)
    window.addEventListener('pointercancel', end, opts)
    window.addEventListener('pointerleave', end, opts)
    root?.addEventListener('touchmove', touchmove, false)
    return () => {
      window.removeEventListener('pointerdown', down)
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', end)
      window.removeEventListener('pointercancel', end)
      window.removeEventListener('pointerleave', end)
      root?.removeEventListener('touchmove', touchmove)
    }
  }, [next, prev])

  return { carouselRef, current, setCurrent }
}
