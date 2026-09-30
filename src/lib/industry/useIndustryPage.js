import { useEffect } from 'react'

// Page-level behaviour for the industries / use-case pages.
//
// Responsive image `sizes`, ported from Coda's image component (Nw in client-CrH_2JZ5.js):
//   useLayoutEffect -> img.setAttribute('sizes', '200px');
//   ResizeObserver  -> sizes = Math.ceil(contentRect.width / 40) * 40 + 'px'
// The SSR snapshot ships these images with sizes="20vw", so without this the browser keeps
// picking the ~300w srcset candidate (live picks 768w / 1536w at desktop).
// Blocks owned by the shared enhancers (card carousel, FAQ, marquees) are left alone.
const SHARED = '.card-carousel, .faq, .rfm-marquee-container, .publisher-logos, .press-carousel'

export function useIndustryPage(ref) {
  useEffect(() => {
    const root = ref.current
    if (!root) return undefined
    const imgs = [...root.querySelectorAll('img[srcset][sizes="20vw"], img[srcSet][sizes="20vw"]')].filter(
      (img) => !img.closest(SHARED),
    )
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const w = Math.ceil(e.contentRect.width / 40) * 40
        e.target.setAttribute('sizes', `${w}px`)
      }
    })
    imgs.forEach((img) => {
      img.setAttribute('sizes', '200px')
      ro.observe(img)
    })
    return () => ro.disconnect()
  }, [ref])
}
