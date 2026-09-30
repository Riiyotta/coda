// Scroll reveal, ported from Coda's reveal wrapper (M3 in client-CrH_2JZ5.js) — see CLONE_SPEC.md §0.
// One observer per element, threshold 0.1, fires once. Live React replaces the class list, and in
// coda-main.css .translate-y-7 wins over .translate-y-0, so the pre-reveal classes must be removed.
const BEFORE = ['opacity-0', 'translate-y-7', 'scale-110']
const AFTER = ['opacity-100', 'translate-y-0', 'scale-100']

export function initReveal() {
  const watched = new WeakSet()
  const observers = []

  const watch = (el) => {
    if (watched.has(el)) return
    watched.add(el)
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return
        el.classList.remove(...BEFORE)
        el.classList.add(...AFTER)
        io.disconnect()
      },
      { root: null, rootMargin: '0px', threshold: 0.1 },
    )
    io.observe(el)
    observers.push(io)
  }

  const scan = (root) => {
    if (root.matches?.('[data-reveal]')) watch(root)
    root.querySelectorAll?.('[data-reveal]').forEach(watch)
  }

  scan(document)
  // components remounted later (e.g. by hot reload) bring fresh, unrevealed nodes
  const mo = new MutationObserver((records) => {
    for (const r of records) r.addedNodes.forEach((n) => n.nodeType === 1 && scan(n))
  })
  mo.observe(document.body, { childList: true, subtree: true })

  return () => {
    mo.disconnect()
    observers.forEach((io) => io.disconnect())
  }
}
