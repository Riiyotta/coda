// FAQ accordion — port of Coda's faq-item (faq-item-RYMLneTQ.js). Every item starts collapsed
// (startOpen=false). The answer is a framer-motion div animating {height: open ? 'auto' : 0,
// opacity: open ? 1 : 0} with framer's default tween for non-transform values:
// 0.3s, ease [0.25, 0.1, 0.35, 1]. `overflow-hidden` is only present while closed (it is removed
// the moment the item opens), and the icon swaps instantly between plus and minus.
import { hasReactHandler } from './util.js'

const DURATION = 300
const EASING = 'cubic-bezier(0.25, 0.1, 0.35, 1)'
const PLUS =
  'M16.25 8C16.6642 8 17 8.33579 17 8.75V15.5H23.75C24.1642 15.5 24.5 15.8358 24.5 16.25C24.5 16.6642 24.1642 17 23.75 17H17V23.75C17 24.1642 16.6642 24.5 16.25 24.5C15.8358 24.5 15.5 24.1642 15.5 23.75V17H8.75C8.33579 17 8 16.6642 8 16.25C8 15.8358 8.33579 15.5 8.75 15.5H15.5V8.75C15.5 8.33579 15.8358 8 16.25 8Z'
const MINUS =
  'M8 15.75C8 15.3358 8.33579 15 8.75 15H22.75C23.1642 15 23.5 15.3358 23.5 15.75C23.5 16.1642 23.1642 16.5 22.75 16.5H8.75C8.33579 16.5 8 16.1642 8 15.75Z'

export const selector = '.faq-item'

export function attach(item) {
  const button = item.querySelector('button')
  const content = button?.closest('a')?.nextElementSibling
  if (!button || !content || hasReactHandler(button)) return null
  const icon = button.lastElementChild?.querySelector('svg path')

  // resume the state of a previous attach (effects re-run), otherwise collapsed like live
  let open = content.style.height !== '' && content.style.height !== '0px'
  let anims = []
  let raf = 0

  const apply = () => {
    content.classList.toggle('overflow-hidden', !open)
    icon?.setAttribute('d', open ? MINUS : PLUS)
    content.style.height = open ? 'auto' : '0px'
    content.style.opacity = open ? '1' : '0'
  }
  apply()

  const stop = () => {
    if (raf) content.style.height = open ? 'auto' : '0px'
    cancelAnimationFrame(raf)
    raf = 0
    anims.forEach((a) => a.cancel())
    anims = []
  }
  const onClick = () => {
    const fromH = content.getBoundingClientRect().height
    const fromO = parseFloat(getComputedStyle(content).opacity)
    stop()
    open = !open
    let toH = 0
    if (open) {
      content.style.height = 'auto'
      toH = content.getBoundingClientRect().height
    }
    apply()
    const opts = { duration: DURATION, easing: EASING }
    anims.push(content.animate([{ opacity: fromO }, { opacity: open ? 1 : 0 }], opts))
    // framer resolves 'auto' height keyframes in its next frame batch, so on live the height tween
    // starts one frame after the opacity tween; hold the start height for that frame.
    content.style.height = `${fromH}px`
    // (WAAPI start times are taken at the next frame commit, hence the double rAF)
    raf = requestAnimationFrame(() => {
      raf = requestAnimationFrame(() => {
        raf = 0
        content.style.height = open ? 'auto' : '0px'
        anims.push(content.animate([{ height: `${fromH}px` }, { height: `${toH}px` }], opts))
      })
    })
  }
  button.addEventListener('click', onClick)
  return () => {
    button.removeEventListener('click', onClick)
    stop()
  }
}
