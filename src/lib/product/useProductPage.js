import { useEffect } from 'react'

// Page-level behaviour for the six /product/* pages. The page files are server-rendered snapshots
// (tools/live2jsx.py); every block on them is CSS-only apart from the scroll reveal (src/lib/reveal.js)
// and the shared blocks handled by src/lib/enhance/. What the snapshot freezes is the image `sizes`:
//
// Coda's image component (Nw in client-CrH_2JZ5.js) renders sizes="20vw", then
//   useLayoutEffect -> img.setAttribute('sizes', '200px')
//   ResizeObserver  -> img.setAttribute('sizes', Math.ceil(contentRect.width / 40) * 40 + 'px')
// Without this the browser keeps the ~300w srcset candidate where live loads 768w / 1536w.
// Blocks owned by the shared enhancers are left alone.
const SHARED = '.card-carousel, .faq, .rfm-marquee-container, .publisher-logos, .press-carousel'

export function useProductPage(ref) {
  useEffect(() => {
    const root = ref.current
    if (!root) return undefined
    const imgs = [...root.querySelectorAll('img[srcset][sizes="20vw"]')].filter((img) => !img.closest(SHARED))
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        e.target.setAttribute('sizes', `${Math.ceil(e.contentRect.width / 40) * 40}px`)
      }
    })
    imgs.forEach((img) => {
      img.setAttribute('sizes', '200px')
      ro.observe(img)
    })
    return () => ro.disconnect()
  }, [ref])
}
