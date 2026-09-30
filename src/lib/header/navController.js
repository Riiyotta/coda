// Imperative port of Coda's header behaviour (client-CrH_2JZ5.js: pb, vg, ob, aS, db).
// The header markup is static JSX, so state is applied by toggling the same
// Tailwind classes live's React/tailwind-merge produces, and the dropdown tweens
// are the live GSAP calls verbatim, scoped to each .nav-header-category.
import gsap from 'gsap'

const MOBILE_BP = 800 // Q3(): window.innerWidth < 800
const HOVER_CLOSE_MS = 300 // br.hoverTimer
const CLOSE_TWEEN_DELAY_MS = 300 // ob(): setTimeout(w, 300) when active -> ""
const SCROLL_THROTTLE_MS = 50 // pb(): Date.now() - last < 50
const SCROLL_MIN_DELTA = 5
const SCROLL_THRESHOLD_VH = 0.2
// motion's default tween for non-transform props (Wk in bundle)
const MOTION_DEFAULT = { duration: 300, easing: 'cubic-bezier(0.25, 0.1, 0.35, 1)' }

function toggle(el, on, add, remove = []) {
  if (!el) return
  if (on) {
    remove.forEach((c) => el.classList.remove(c))
    add.forEach((c) => el.classList.add(c))
  } else {
    add.forEach((c) => el.classList.remove(c))
    remove.forEach((c) => el.classList.add(c))
  }
}

export function initHeaderNav(wrap) {
  const state = { active: '', lastActive: '', hoverTimer: 0, isMenuOpen: false, hidden: false }
  const isMobile = () => window.innerWidth < MOBILE_BP
  let mobile = isMobile()
  const cleanups = []
  let lastY = window.scrollY
  const on = (el, type, fn, opts) => {
    if (!el) return
    el.addEventListener(type, fn, opts)
    cleanups.push(() => el.removeEventListener(type, fn, opts))
  }

  const backdrop = wrap.children[0]
  const shell = wrap.querySelector('.min-h-navBarHeightBase')
  const menu = shell.children[2]
  const rowDesk = shell.children[3]
  const rowMob = shell.children[4]
  const burger = shell.querySelector('.group.cursor-pointer.p-4')

  // ---- category controllers (ob) ----
  const categories = [...wrap.querySelectorAll('.nav-header-category')].map((el) => {
    const label = [...el.classList].find((c) => c.startsWith('nav-header-category-')).slice(20)
    const q = gsap.utils.selector(el)
    const trigger = el.firstElementChild
    const cat = { el, label, q, trigger, isButton: trigger.tagName === 'BUTTON', pc: el.querySelector('.primary-category'), closeTimer: 0 }
    const all = () => q('.primary-category, .primary-inner, .primary-category-bg-inner, .primary-category .nav-header-item, .primary-category-featured')

    cat.open = () => {
      gsap.killTweensOf(q('.primary-category, .primary-inner, .primary-category-bg-inner, .primary-category .nav-header-item'))
      gsap.fromTo(q('.primary-category, .primary-inner'), { opacity: 0 }, { opacity: 1, duration: 0.5, ease: 'power2.out' })
      gsap.fromTo(q('.primary-category-bg-inner'), { y: '-100%' }, { y: 0, duration: 0.5, ease: 'power2.inOut' })
      gsap.fromTo(q('.primary-category .nav-header-item'), { opacity: 0, y: '-35%' }, { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out', stagger: 0.03, delay: 0.2 })
      const f = q('.primary-category-featured')
      if (f.length) gsap.fromTo(f, { opacity: 0, y: '-10%' }, { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out', delay: 0.4 })
    }
    cat.close = () => {
      gsap.killTweensOf(all())
      gsap.to(q('.primary-category'), { opacity: 0, duration: 0.35, ease: 'power2.out', delay: 0.35 })
      gsap.to(q('.primary-inner'), { opacity: 0, duration: 0.5, ease: 'power2.out' })
      gsap.to(q('.primary-category-bg-inner'), { y: '-100%', duration: 0.5, ease: 'power2.inOut' })
      const f = q('.primary-category-featured')
      if (f.length) gsap.to(f, { opacity: 0, duration: 0.35, ease: 'power2.out' })
    }
    cat.switchTo = () => {
      gsap.killTweensOf(all())
      gsap.set(q('.primary-category'), { opacity: 1 })
      gsap.to(q('.primary-inner, .primary-category .nav-header-item, .primary-category-featured'), { opacity: 1, duration: 0.5, ease: 'power2.out' })
      gsap.set(q('.primary-category-bg-inner'), { y: 0 })
    }
    cat.switchAway = () => {
      gsap.killTweensOf(all())
      gsap.to(q('.primary-category, .primary-inner, .primary-category .nav-header-item, .primary-category-featured'), { opacity: 0, duration: 0.5, ease: 'power2.out' })
      gsap.to(q('.primary-category .nav-header-item, .primary-category-featured'), { y: 0, duration: 0.5, ease: 'power2.out' })
      gsap.set(q('.primary-category-bg-inner'), { y: '-100%' })
    }
    // useEffect(..., [n.active])
    cat.onActiveChange = () => {
      window.clearTimeout(cat.closeTimer)
      if (state.active === label) state.lastActive === '' ? cat.open() : cat.switchTo()
      else if (state.active === '') cat.closeTimer = window.setTimeout(cat.close, CLOSE_TWEEN_DELAY_MS)
      else cat.switchAway()
    }
    return cat
  })

  // ---- render: class toggles exactly as live's tailwind-merge output ----
  const render = () => {
    const { active, isMenuOpen, hidden } = state
    toggle(wrap, hidden && !isMenuOpen && active === '', ['transform', '-translate-y-full'], ['transform-none'])
    toggle(backdrop, active !== '' || isMenuOpen, ['opacity-100'], ['opacity-0'])
    for (const el of [menu, rowDesk, rowMob]) {
      toggle(el, isMenuOpen, ['translate-y-0', 'opacity-100', 'pointer-events-auto'], ['opacity-0', '-translate-y-6'])
      toggle(el, !!active, ['-translate-x-full'])
    }
    // rows carry pointer-events-none in the base class list (removed by merge when open)
    for (const el of [rowDesk, rowMob]) toggle(el, !isMenuOpen, ['pointer-events-none'])
    toggle(burger, isMenuOpen, ['open'])
    for (const c of categories) {
      const isActive = active === c.label && c.label !== ''
      if (c.isButton) toggle(c.trigger, isActive, ['pointer-events-auto', 'md:bg-grey-0'])
      toggle(c.pc, isActive, ['pointer-events-auto'], ['pointer-events-none'])
    }
  }

  // store writes (valtio in live: effects only fire on actual change)
  const setActiveRaw = (v) => {
    if (state.active === v) return
    state.active = v
    render()
    categories.forEach((c) => c.onActiveChange())
  }
  const L = (v) => {
    if (state.active === v) return
    state.lastActive = state.active
    setActiveRaw(v)
  }
  const clearHover = () => clearTimeout(state.hoverTimer)
  const scheduleClose = () => {
    if (mobile) return
    clearHover()
    state.hoverTimer = window.setTimeout(() => L(''), HOVER_CLOSE_MS)
  }

  for (const c of categories) {
    if (c.isButton) {
      const enter = () => { if (!mobile) { clearHover(); L(c.label) } }
      on(c.trigger, 'mouseover', enter)
      on(c.trigger, 'mouseout', scheduleClose)
      on(c.trigger, 'click', (e) => { e.preventDefault(); if (mobile) L(c.label) })
      on(c.pc, 'mouseover', enter)
      on(c.pc, 'mouseout', scheduleClose)
    } else {
      // Pricing: plain link; hovering it closes any open dropdown immediately
      on(c.trigger, 'mouseover', () => { if (!mobile) { clearHover(); L('') } })
      on(c.trigger, 'mouseout', scheduleClose)
      on(c.pc, 'mouseover', () => { if (!mobile) { clearHover(); L(c.label) } })
      on(c.pc, 'mouseout', scheduleClose)
    }
    // mobile "Back" row
    on(c.pc && c.pc.querySelector('.cursor-pointer.md\\:hidden'), 'click', () => L(''))

    // featured card: motion.p animate {opacity, height: auto} with motion's default tween
    const feat = c.pc && c.pc.querySelector('.primary-category-featured')
    const desc = feat && feat.querySelector('p.hidden.md\\:flex')
    if (desc) {
      let hovered = false
      let anim = null
      const run = (next) => {
        if (next === hovered) return
        hovered = next
        const cs = getComputedStyle(desc)
        const fromH = desc.getBoundingClientRect().height
        const fromO = +cs.opacity
        if (anim) anim.cancel()
        desc.style.height = 'auto'
        const toH = next ? desc.getBoundingClientRect().height : 0
        const toO = next ? 1 : 0
        desc.style.height = `${toH}px`
        desc.style.opacity = String(toO)
        anim = desc.animate(
          [{ height: `${fromH}px`, opacity: fromO }, { height: `${toH}px`, opacity: toO }],
          MOTION_DEFAULT,
        )
        anim.onfinish = () => { anim = null; if (hovered) desc.style.height = 'auto' }
      }
      on(feat, 'mouseover', () => run(true))
      on(feat, 'mouseout', () => run(false))
    }
  }

  // hamburger (db)
  on(burger, 'click', () => {
    const next = !state.isMenuOpen
    state.isMenuOpen = next
    render()
    setTimeout(() => setActiveRaw(''), next ? 0 : 300)
  })

  // client-side route change (src/lib/router.js): reset to the state a fresh page load has
  const reset = () => {
    clearHover()
    state.isMenuOpen = false
    state.hidden = false
    lastY = window.scrollY
    setActiveRaw('')
    render()
  }
  on(window, 'coda:navigate', reset)
  on(window, 'popstate', reset)

  on(window, 'resize', () => {
    const m = isMobile()
    if (m !== mobile) { mobile = m; clearHover() }
  })

  // ---- hide/show on scroll (pb + Cg rAF loop) ----
  let lastDecision = 0
  let raf = 0
  const tick = () => {
    raf = requestAnimationFrame(tick)
    if (Date.now() - lastDecision < SCROLL_THROTTLE_MS) return
    const y = window.scrollY
    const threshold = window.innerHeight * SCROLL_THRESHOLD_VH
    if (y === lastY || Math.abs(y - lastY) < SCROLL_MIN_DELTA) return
    const hidden = y > threshold && y > lastY
    lastY = y
    lastDecision = Date.now()
    // live sets React state here; the class lands on the next task (after this
    // frame paints), i.e. ~1 frame later. Mirror that with a macrotask.
    if (hidden !== state.hidden) { state.hidden = hidden; setTimeout(render, 0) }
  }
  raf = requestAnimationFrame(tick)

  render()

  return () => {
    cancelAnimationFrame(raf)
    clearHover()
    categories.forEach((c) => { clearTimeout(c.closeTimer); gsap.killTweensOf(c.q('*')) })
    cleanups.forEach((f) => f())
  }
}
