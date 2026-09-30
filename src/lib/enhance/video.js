// Inline videos on inner pages — DOM port of Coda's InlineVideo (InlineVideo-CpOHSTVY.js), same as
// src/lib/hero/InlineVideo.jsx: playing by default (muted autoplay loop), the button toggles
// play()/pause() and `autoplay`, and swaps pause/play icons instantly.
import { hasReactHandler } from './util.js'

const PAUSE =
  '<svg class="w-full" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5.75 3C5.33579 3 5 3.33579 5 3.75V16.25C5 16.6642 5.33579 17 5.75 17H7.25C7.66421 17 8 16.6642 8 16.25V3.75C8 3.33579 7.66421 3 7.25 3H5.75Z" fill="currentColor"></path><path d="M12.75 3C12.3358 3 12 3.33579 12 3.75V16.25C12 16.6642 12.3358 17 12.75 17H14.25C14.6642 17 15 16.6642 15 16.25V3.75C15 3.33579 14.6642 3 14.25 3H12.75Z" fill="currentColor"></path></svg>'
const PLAY =
  '<svg class="w-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M6 7.40825C6 6.33866 7.14675 5.66062 8.08395 6.17607L16.7394 10.9366C17.7108 11.4708 17.7108 12.8667 16.7394 13.4009L8.08395 18.1614C7.14675 18.6769 6 17.9988 6 16.9292V7.40825Z" fill="currentColor"></path></svg>'

export const selector = 'video'

export function attach(video) {
  const button = video.parentElement?.querySelector(':scope > button')
  const icon = button?.querySelector(':scope > div')
  if (!button || !icon || hasReactHandler(button)) return null
  let playing = !video.paused || video.autoplay
  const apply = () => {
    video.autoplay = playing
    icon.innerHTML = playing ? PAUSE : PLAY
    if (playing) {
      // React sets `muted` as a property only; force it so the autoplay policy allows play()
      video.muted = true
      video.play()?.catch?.(() => {})
    } else video.pause()
  }
  apply()
  const onClick = () => { playing = !playing; apply() }
  button.addEventListener('click', onClick)
  return () => button.removeEventListener('click', onClick)
}
