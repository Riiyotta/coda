// "Explore more from Coda" card carousel on inner pages — DOM port of Coda's card-carousel
// (card-carousel-pYWQhttU.js) driven by useCarousel (useCarousel-DE99UO_7.js), the same algorithm as
// the homepage's src/lib/carousel/useCarousel.js:
// - items absolutely positioned, per-frame x-lerp 0.125 towards (x - x[current] + dragLerp),
//   drag lerp 0.2, values rounded to 1e-3 px; lerp state resets to 0 whenever window width changes
// - swipe past 15% of the first item's width -> next/prev (wrapping); >10px marks a drag and
//   suppresses the link click
// - arrow buttons (desktop header pair + mobile pair below) call setCurrent(current±1) and are
//   disabled (text-grey-2/50, no `group`, no click) at the ends; they do not wrap.
import { hasReactHandler, onWindowSize } from './util.js'

export const selector = '.card-carousel'

const BTN = 'w-8 h-8 md:w-7 md:h-7 cursor-pointer'
const btnClass = (disabled, reverse) =>
  (disabled
    ? `${BTN} transition-colors duration-300 text-grey-2/50`
    : `${BTN} text-charcoal transition-colors duration-300 group`) + (reverse ? ' rotate-180' : '')

export function attach(block) {
  const root = block.querySelector('.carousel')
  if (!root) return null
  const buttons = [...block.querySelectorAll('svg')]
    .filter((s) => !root.contains(s) && s.parentElement.querySelectorAll(':scope > svg').length === 2)
    .map((svg) => ({ svg, reverse: svg === svg.parentElement.firstElementChild }))
  if (buttons.some((b) => hasReactHandler(b.svg))) return null

  let items = root.querySelectorAll('.carousel-snap')
  let spacer = root.querySelector('.carousel-spacer')
  const count = items.length
  let current = 0
  let state = []
  const drag = { down: false, dragged: false, start: { x: 0, y: 0 }, delta: { x: 0, y: 0 }, current: { xLerp: 0, yLerp: 0 } }

  const setCurrent = (i) => {
    current = i
    buttons.forEach(({ svg, reverse }) => {
      const disabled = reverse ? current === 0 : current === count - 1
      svg.setAttribute('class', btnClass(disabled, reverse))
      svg.dataset.disabled = disabled ? '1' : ''
    })
  }
  const next = () => setCurrent(current + 1 < (items.length || 1) ? current + 1 : 0)
  const prev = () => setCurrent(current - 1 >= 0 ? current - 1 : (items.length || 1) - 1)

  // measurement effect (re-runs on window width change)
  const blockLink = (e) => e.preventDefault()
  const blockClick = (e) => {
    if (drag.dragged) { e.preventDefault(); e.stopPropagation() }
  }
  let links = []
  const unbindLinks = () =>
    links.forEach((a) => {
      a.removeEventListener('mousedown', blockLink, false)
      a.removeEventListener('mousemove', blockLink, false)
      a.removeEventListener('click', blockClick, false)
    })
  const measure = () => {
    unbindLinks()
    items = root.querySelectorAll('.carousel-snap')
    spacer = root.querySelector('.carousel-spacer')
    links = [...root.querySelectorAll('a')]
    state = []
    items.forEach((it, i) => {
      it.style.setProperty('position', 'absolute')
      it.style.setProperty('left', '0px')
      it.style.setProperty('top', '0px')
      it.style.setProperty('transition', 'none')
      it.style.setProperty('user-select', 'none')
      it.querySelector('img')?.style.setProperty('transition', 'none')
      state[i] = { x: 0, w: 0, h: 0, xLerp: 0 }
    })
    links.forEach((a) => {
      a.addEventListener('mousedown', blockLink, false)
      a.addEventListener('mousemove', blockLink, false)
      a.addEventListener('click', blockClick, false)
    })
  }
  measure()
  setCurrent(0)

  let raf = 0
  const tick = () => {
    drag.current.xLerp += (drag.delta.x - drag.current.xLerp) * 0.2
    drag.current.yLerp += (drag.delta.y - drag.current.yLerp) * 0.2
    let x = 0
    let target = 0
    const gap = spacer?.offsetWidth || 0
    items.forEach((it, i) => {
      const s = state[i]
      s.x = x
      s.w = it.offsetWidth
      s.h = it.offsetHeight
      if (i === current) target = x
      x += s.w + gap
    })
    items.forEach((it, i) => {
      const s = state[i]
      s.xLerp += (s.x - target + drag.current.xLerp - s.xLerp) * 0.125
      s.xLerp = Math.round(s.xLerp * 1e3) / 1e3
      it.style.transform = `translateX(${s.xLerp}px)`
    })
    raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)

  const onButton = (e) => {
    const b = buttons.find((x) => x.svg === e.currentTarget)
    if (!b || b.svg.dataset.disabled) return
    setCurrent(current + (b.reverse ? -1 : 1))
  }
  buttons.forEach((b) => b.svg.addEventListener('click', onButton))

  const end = () => {
    if (drag.down) { drag.down = false; drag.delta.x = 0; drag.delta.y = 0 }
  }
  const down = (e) => {
    if (e.target instanceof HTMLElement && root.contains(e.target)) {
      drag.start.x = e.clientX; drag.start.y = e.clientY; drag.down = true; drag.dragged = false
    }
  }
  const move = (e) => {
    if (!drag.down) return
    drag.delta.x = e.clientX - drag.start.x
    drag.delta.y = e.clientY - drag.start.y
    if (Math.abs(drag.delta.x) > 10) drag.dragged = true
    if (Math.abs(drag.delta.x) > (items[0]?.offsetWidth || window.innerWidth) * 0.15) {
      drag.delta.x < 0 ? next() : prev()
      end()
    }
  }
  const touchmove = (e) => {
    if (drag.dragged && drag.down) { e.preventDefault(); e.stopPropagation() }
  }
  const opts = { passive: true }
  window.addEventListener('pointerdown', down, opts)
  window.addEventListener('pointermove', move, opts)
  window.addEventListener('pointerup', end, opts)
  window.addEventListener('pointercancel', end, opts)
  window.addEventListener('pointerleave', end, opts)
  root.addEventListener('touchmove', touchmove, false)

  let lastWidth = window.innerWidth
  const stopSize = onWindowSize((w) => {
    if (w !== lastWidth) { lastWidth = w; measure() }
  })

  return () => {
    cancelAnimationFrame(raf)
    stopSize()
    unbindLinks()
    buttons.forEach((b) => b.svg.removeEventListener('click', onButton))
    window.removeEventListener('pointerdown', down)
    window.removeEventListener('pointermove', move)
    window.removeEventListener('pointerup', end)
    window.removeEventListener('pointercancel', end)
    window.removeEventListener('pointerleave', end)
    root.removeEventListener('touchmove', touchmove)
  }
}
