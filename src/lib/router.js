// Minimal client-side router: pathname -> page. Internal links (href starting with "/") are
// intercepted and pushed onto history; links to pages outside the clone are "#" (see linkGuard.js).
import { useEffect, useState } from 'react'

const listeners = new Set()

export function navigate(to) {
  if (to === location.pathname + location.search) return
  history.pushState({}, '', to)
  listeners.forEach((fn) => fn())
  // live does a full page load here, which resets the header (menu, dropdowns)
  window.dispatchEvent(new Event('coda:navigate'))
  window.scrollTo(0, 0)
}

export function normalize(path) {
  return path.endsWith('/') ? path : path + '/'
}

export function usePath() {
  const [path, setPath] = useState(location.pathname)
  useEffect(() => {
    const update = () => setPath(location.pathname)
    listeners.add(update)
    window.addEventListener('popstate', update)
    return () => {
      listeners.delete(update)
      window.removeEventListener('popstate', update)
    }
  }, [])
  return path
}

export function initRouterLinks() {
  const onClick = (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
    const a = e.target.closest && e.target.closest('a[href^="/"]')
    if (!a || a.target === '_blank') return
    e.preventDefault()
    navigate(a.getAttribute('href'))
  }
  document.addEventListener('click', onClick)
  return () => document.removeEventListener('click', onClick)
}
