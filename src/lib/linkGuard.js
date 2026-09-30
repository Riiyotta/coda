// Links to pages outside this clone are rewritten to "#" by tools/html2jsx.py;
// this stops them from jumping the page to the top when clicked.
export function initLinkGuard() {
  const onClick = (e) => {
    const a = e.target.closest && e.target.closest('a[href="#"]')
    if (a) e.preventDefault()
  }
  document.addEventListener('click', onClick, true)
  return () => document.removeEventListener('click', onClick, true)
}
