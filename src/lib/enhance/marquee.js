// Marquees on inner pages — DOM port of react-fast-marquee as inlined by Coda (index-C-Tc9-Q2.js),
// horizontal "left" only (same as src/lib/marquee/Marquee.jsx), plus the two blocks that use it:
// - publisher-logos (publisher-logos-Bi5xzS59.js): narrow = width < 800, on = narrow || logos > 4;
//   Marquee autoFill=on play=on gradient=(!narrow && on) gradientColor #fcfcfc
// - content/marquee (marquee-aVY9p8pW.js): two wrappers ("hidden md:block" and "md:hidden"), each
//   Marquee autoFill=!narrow, playing, no gradient.
// Duration: autoFill ? width*copies/50 : max(width, container)/50 seconds; copies =
// ceil(container/width) when autoFill and the content is narrower than the container.
// The server markup (static list) is hidden and the marquee is built from clones next to it.
import { createSizesWatcher, el, onWindowSize } from './util.js'

const SPEED = 50

function createMarquee(template) {
  const container = el('div', 'rfm-marquee-container ')
  const overlay = el('div', 'rfm-overlay')
  const m1 = el('div', 'rfm-marquee')
  const initial = el('div', 'rfm-initial-child-container')
  const m2 = el('div', 'rfm-marquee')
  const sizes = createSizesWatcher()
  const child = () => {
    const c = el('div', 'rfm-child', { '--transform': 'none' })
    c.appendChild(template.cloneNode(true))
    sizes.watch(c)
    return c
  }
  initial.appendChild(child())
  m1.appendChild(initial)
  container.append(m1, m2)

  let props = { autoFill: false, play: true, gradient: false, gradientColor: 'white' }
  let multiplier = 0
  let cw = 0
  let mw = 0

  const setCopies = (parent, n, keep) => {
    while (parent.children.length - keep > n) parent.lastElementChild.remove()
    while (parent.children.length - keep < n) parent.appendChild(child())
  }
  const render = () => {
    const { autoFill, play, gradient, gradientColor } = props
    const run = play ? 'running' : 'paused'
    container.style.setProperty('--pause-on-hover', run)
    container.style.setProperty('--pause-on-click', run)
    container.style.setProperty('--width', '100%')
    container.style.setProperty('--transform', 'none')
    if (gradient) {
      overlay.style.setProperty('--gradient-color', gradientColor)
      overlay.style.setProperty('--gradient-width', '200px')
      if (!overlay.parentNode) container.prepend(overlay)
    } else overlay.remove()
    const duration = autoFill ? (mw * multiplier) / SPEED : mw < cw ? cw / SPEED : mw / SPEED
    for (const m of [m1, m2]) {
      m.style.setProperty('--play', run)
      m.style.setProperty('--direction', 'normal')
      m.style.setProperty('--duration', `${duration}s`)
      m.style.setProperty('--delay', '0s')
      m.style.setProperty('--iteration-count', 'infinite')
      m.style.setProperty('--min-width', autoFill ? 'auto' : '100%')
    }
    setCopies(m1, multiplier - 1, 1)
    setCopies(m2, multiplier, 0)
  }
  const calculate = () => {
    const c = container.getBoundingClientRect().width
    const m = initial.getBoundingClientRect().width
    multiplier = props.autoFill && c && m && m < c ? Math.ceil(c / m) : 1
    cw = c
    mw = m
    render()
  }
  const ro = new ResizeObserver(calculate)
  return {
    el: container,
    set(next) {
      props = { ...props, ...next }
      if (multiplier === 0) multiplier = 1
      render()
      if (container.isConnected) calculate()
    },
    start() {
      calculate()
      ro.observe(container)
      ro.observe(initial)
    },
    destroy() {
      ro.disconnect()
      sizes.disconnect()
    },
  }
}

function build(host, template, wrapClass, getProps) {
  const wrap = el('div', wrapClass)
  const mq = createMarquee(template)
  mq.set(getProps(window.innerWidth))
  wrap.appendChild(mq.el)
  host.appendChild(wrap)
  mq.start()
  return { wrap, mq }
}

function enhance(host, template, specs) {
  const pristine = template.cloneNode(true)
  template.style.display = 'none'
  const built = specs.map(([cls, getProps]) => ({ ...build(host, pristine, cls, getProps), getProps }))
  const stop = onWindowSize((w) => built.forEach(({ mq, getProps }) => mq.set(getProps(w))))
  return () => {
    stop()
    built.forEach(({ wrap, mq }) => { mq.destroy(); wrap.remove() })
    template.style.removeProperty('display')
  }
}

export const publisherLogos = {
  selector: '.publisher-logos',
  attach(block) {
    const host = block.lastElementChild
    const list = host?.firstElementChild
    if (!list || host === block.firstElementChild || host.querySelector('.rfm-marquee-container')) return null
    const logos = list.children.length
    return enhance(host, list, [
      ['w-full h-full [&_div]:h-full', (w) => {
        const narrow = w < 800
        const on = narrow || logos > 4
        return { autoFill: on, play: on, gradient: !narrow && on, gradientColor: '#fcfcfc' }
      }],
    ])
  },
}

export const contentMarquee = {
  selector: '.marquee',
  attach(block) {
    const items = block.querySelector(':scope > .marquee-items')
    if (!items || block.querySelector('.rfm-marquee-container')) return null
    const props = (w) => ({ autoFill: !(w < 800), play: true, gradient: false })
    return enhance(block, items, [
      ['hidden md:block w-full h-full [&_div]:h-full', props],
      ['w-full h-full md:hidden [&_div]:h-full', props],
    ])
  },
}
