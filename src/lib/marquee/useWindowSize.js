// Port of Coda's useWindowSize (react-use style, rAF-throttled) — useWindowSize-CPyXvShL.js.
import { useEffect, useRef, useState } from 'react'

export function useWindowSize() {
  const raf = useRef(0)
  const [size, setSize] = useState(() => ({ width: window.innerWidth, height: window.innerHeight }))
  useEffect(() => {
    const onResize = () => {
      cancelAnimationFrame(raf.current)
      raf.current = requestAnimationFrame(() => setSize({ width: window.innerWidth, height: window.innerHeight }))
    }
    window.addEventListener('resize', onResize)
    return () => {
      window.removeEventListener('resize', onResize)
      cancelAnimationFrame(raf.current)
    }
  }, [])
  return size
}
