// DOM enhancers for blocks shared by the inner pages (FAQ, card carousel, marquees, videos).
// Like reveal.js they attach to server-rendered markup, so page files stay as generated.
// They pick up pages that mount later (routes are lazy-loaded) via a MutationObserver, attach once
// per element, only inside lazily loaded route pages (the homepage has real React ports of the same
// blocks), and tear down when the element leaves the document or on unmount.
import * as faq from './faq.js'
import * as carousel from './carousel.js'
import * as video from './video.js'
import * as sizes from './sizes.js'
import { publisherLogos, contentMarquee } from './marquee.js'
import { inLazyPage } from './util.js'

const enhancers = [faq, carousel, publisherLogos, contentMarquee, video, sizes]

export function initEnhancers() {
  const attached = new Map() // element -> Map(enhancer -> cleanup)

  const tryAttach = (enh, node) => {
    if (attached.get(node)?.has(enh) || node.closest('[data-no-enhance]') || !inLazyPage(node)) return
    let cleanup = null
    try {
      cleanup = enh.attach(node)
    } catch (err) {
      console.warn('[enhance]', enh.selector, err)
    }
    if (!cleanup) return
    if (!attached.has(node)) attached.set(node, new Map())
    attached.get(node).set(enh, cleanup)
  }

  const scan = (root) => {
    for (const enh of enhancers) {
      if (root.matches?.(enh.selector)) tryAttach(enh, root)
      root.querySelectorAll?.(enh.selector).forEach((n) => tryAttach(enh, n))
    }
  }

  const sweep = () => {
    for (const [node, byEnh] of attached) {
      if (!node.isConnected) {
        byEnh.forEach((cleanup) => cleanup())
        attached.delete(node)
      }
    }
  }

  scan(document)
  const mo = new MutationObserver((records) => {
    let removed = false
    for (const r of records) {
      if (r.removedNodes.length) removed = true
      r.addedNodes.forEach((n) => n.nodeType === 1 && scan(n))
    }
    if (removed) sweep()
  })
  mo.observe(document.body, { childList: true, subtree: true })

  return () => {
    mo.disconnect()
    for (const byEnh of attached.values()) byEnh.forEach((cleanup) => cleanup())
    attached.clear()
  }
}
