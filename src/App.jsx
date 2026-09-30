import { lazy, Suspense, useEffect, useMemo } from 'react'
import Header from './components/Header.jsx'
import Main from './components/Main.jsx'
import Footer from './components/Footer.jsx'
import { routes } from './pages/routes.js'
import { initReveal } from './lib/reveal.js'
import { initLinkGuard } from './lib/linkGuard.js'
import { initRouterLinks, normalize, usePath } from './lib/router.js'
import { initEnhancers } from './lib/enhance/index.js'

const pages = Object.fromEntries(Object.entries(routes).map(([path, load]) => [path, lazy(load)]))

export default function App() {
  const path = normalize(usePath())
  const Page = useMemo(() => pages[path], [path])

  useEffect(() => {
    const stopReveal = initReveal()
    const stopGuard = initLinkGuard()
    const stopLinks = initRouterLinks()
    const stopEnhancers = initEnhancers()
    return () => {
      stopReveal()
      stopGuard()
      stopLinks()
      stopEnhancers()
    }
  }, [])

  return (
    <div data-locale="en">
      <Header />
      {Page ? (
        <Suspense fallback={<div className="min-h-screen" />}>
          <Page key={path} />
        </Suspense>
      ) : (
        <Main />
      )}
      <Footer />
    </div>
  )
}
