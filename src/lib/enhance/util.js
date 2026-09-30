// Shared helpers for the DOM enhancers.

const LAZY = Symbol.for('react.lazy')

function reactKey(el, prefix) {
  for (const k in el) if (k.startsWith(prefix)) return k
  return null
}

// True when `el` was rendered by a lazily loaded route page (src/pages/*), i.e. static generated
// markup. The homepage (Main) renders the same block classes through real React ports, which must
// not be enhanced a second time.
export function inLazyPage(el) {
  const key = reactKey(el, '__reactFiber$')
  let f = key ? el[key] : null
  while (f) {
    if (f.elementType && f.elementType.$$typeof === LAZY) return true
    f = f.return
  }
  return false
}

// True when React already attached a handler (e.g. a page-specific React port of the block).
export function hasReactHandler(el, name = 'onClick') {
  if (!el) return false
  const key = reactKey(el, '__reactProps$')
  return !!(key && el[key] && typeof el[key][name] === 'function')
}

// react-use useWindowSize: the value updates on the animation frame after a resize event.
export function onWindowSize(cb) {
  let raf = 0
  const onResize = () => {
    cancelAnimationFrame(raf)
    raf = requestAnimationFrame(() => cb(window.innerWidth, window.innerHeight))
  }
  window.addEventListener('resize', onResize)
  return () => {
    cancelAnimationFrame(raf)
    window.removeEventListener('resize', onResize)
  }
}

export function el(tag, className, style) {
  const n = document.createElement(tag)
  if (className != null) n.className = className
  if (style) for (const [k, v] of Object.entries(style)) n.style.setProperty(k, v)
  return n
}

// Responsive image `sizes`, ported from Coda's image component (Nw in client-CrH_2JZ5.js):
// on mount sizes="200px", then a ResizeObserver sets sizes = ceil(contentWidth / 40) * 40 + "px".
// The SSR snapshot ships sizes="20vw" (so the browser would keep the ~300w candidate). Applied to
// every img that carries a sizes attribute (Nw images); plain WP core/image logos have none.
export function createSizesWatcher() {
  const ro = new ResizeObserver((entries) => {
    for (const e of entries) e.target.setAttribute('sizes', `${Math.ceil(e.contentRect.width / 40) * 40}px`)
  })
  return {
    watch(root) {
      root.querySelectorAll('img[sizes]').forEach((img) => {
        img.setAttribute('sizes', '200px')
        ro.observe(img)
      })
    },
    disconnect: () => ro.disconnect(),
  }
}
