// Image `sizes` for shared blocks whose markup stays in place (card carousel, FAQ). Marquee clones
// get the same treatment in marquee.js. See createSizesWatcher in util.js.
import { createSizesWatcher } from './util.js'

export const selector = '.card-carousel, .faq'

export function attach(block) {
  const w = createSizesWatcher()
  w.watch(block)
  return () => w.disconnect()
}
