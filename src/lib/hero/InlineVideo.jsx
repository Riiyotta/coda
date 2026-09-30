// Port of Coda's InlineVideo (InlineVideo-CpOHSTVY.js): playing=true by default, an effect calls
// play()/pause() whenever it changes, the button toggles it and swaps pause/play icons (no transition).
import { useEffect, useRef, useState } from 'react'

const PauseIcon = (
  <svg className="w-full" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M5.75 3C5.33579 3 5 3.33579 5 3.75V16.25C5 16.6642 5.33579 17 5.75 17H7.25C7.66421 17 8 16.6642 8 16.25V3.75C8 3.33579 7.66421 3 7.25 3H5.75Z" fill="currentColor"></path>
    <path d="M12.75 3C12.3358 3 12 3.33579 12 3.75V16.25C12 16.6642 12.3358 17 12.75 17H14.25C14.6642 17 15 16.6642 15 16.25V3.75C15 3.33579 14.6642 3 14.25 3H12.75Z" fill="currentColor"></path>
  </svg>
)
const PlayIcon = (
  <svg className="w-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path fillRule="evenodd" clipRule="evenodd" d="M6 7.40825C6 6.33866 7.14675 5.66062 8.08395 6.17607L16.7394 10.9366C17.7108 11.4708 17.7108 12.8667 16.7394 13.4009L8.08395 18.1614C7.14675 18.6769 6 17.9988 6 16.9292V7.40825Z" fill="currentColor"></path>
  </svg>
)

export default function InlineVideo({ src, className = '' }) {
  const ref = useRef(null)
  const [playing, setPlaying] = useState(true)

  useEffect(() => {
    const v = ref.current
    if (!v) return
    if (playing) {
      // React sets `muted` as a property after insertion; force it so autoplay policy allows play().
      v.muted = true
      const p = v.play()
      if (p && p.catch) p.catch(() => {})
    } else {
      v.pause()
    }
  }, [playing])

  return (
    <div className={'w-full aspect-video relative rounded-md overflow-hidden ' + className}>
      <video ref={ref} className="w-full h-full object-contain" autoPlay={playing} loop muted playsInline>
        <source src={src} type="video/mp4" />
        {'Your browser does not support the video tag.'}
      </video>
      <button
        className="p-3 rounded-md text-sm whitespace-nowrap bg-charcoal/20 text-offWhite absolute right-4 bottom-4"
        onClick={() => setPlaying((p) => !p)}
      >
        <div className="w-5 h-5">{playing ? PauseIcon : PlayIcon}</div>
      </button>
    </div>
  )
}
