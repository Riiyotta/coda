// Port of react-fast-marquee as inlined by Coda (index-C-Tc9-Q2.js). Horizontal "left" only.
// The .rfm-* CSS and @keyframes scroll already ship in public/styles/wp-inline.css.
// Differences from the library: renders on first paint (library returns null until mounted) so the
// static layout is preserved before measurement.
import { Children, Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react'

const CHILD_STYLE = { '--transform': 'none' }

export default function Marquee({
  autoFill = false,
  play = true,
  speed = 50,
  delay = 0,
  loop = 0,
  gradient = false,
  gradientColor = 'white',
  gradientWidth = 200,
  className = '',
  children,
}) {
  const [containerWidth, setContainerWidth] = useState(0)
  const [marqueeWidth, setMarqueeWidth] = useState(0)
  const [multiplier, setMultiplier] = useState(1)
  const containerRef = useRef(null)
  const marqueeRef = useRef(null)

  const calculateWidth = useCallback(() => {
    if (!containerRef.current || !marqueeRef.current) return
    const c = containerRef.current.getBoundingClientRect().width
    const m = marqueeRef.current.getBoundingClientRect().width
    setMultiplier(autoFill && c && m && m < c ? Math.ceil(c / m) : 1)
    setContainerWidth(c)
    setMarqueeWidth(m)
  }, [autoFill])

  useEffect(() => {
    calculateWidth()
    if (!containerRef.current || !marqueeRef.current) return
    const ro = new ResizeObserver(() => calculateWidth())
    ro.observe(containerRef.current)
    ro.observe(marqueeRef.current)
    return () => ro.disconnect()
  }, [calculateWidth])

  const duration = useMemo(() => {
    if (autoFill) return (marqueeWidth * multiplier) / speed
    return marqueeWidth < containerWidth ? containerWidth / speed : marqueeWidth / speed
  }, [autoFill, containerWidth, marqueeWidth, multiplier, speed])

  const containerStyle = {
    '--pause-on-hover': play ? 'running' : 'paused',
    '--pause-on-click': play ? 'running' : 'paused',
    '--width': '100%',
    '--transform': 'none',
  }
  const gradientStyle = {
    '--gradient-color': gradientColor,
    '--gradient-width': typeof gradientWidth === 'number' ? `${gradientWidth}px` : gradientWidth,
  }
  const marqueeStyle = {
    '--play': play ? 'running' : 'paused',
    '--direction': 'normal',
    '--duration': `${duration}s`,
    '--delay': `${delay}s`,
    '--iteration-count': loop ? `${loop}` : 'infinite',
    '--min-width': autoFill ? 'auto' : '100%',
  }

  const wrap = () =>
    Children.map(children, (child) => (
      <div style={CHILD_STYLE} className="rfm-child">
        {child}
      </div>
    ))
  const multiplyChildren = (n) =>
    [...Array(Number.isFinite(n) && n >= 0 ? n : 0)].map((_, i) => <Fragment key={i}>{wrap()}</Fragment>)

  return (
    <div ref={containerRef} style={containerStyle} className={'rfm-marquee-container ' + className}>
      {gradient && <div style={gradientStyle} className="rfm-overlay" />}
      <div className="rfm-marquee" style={marqueeStyle}>
        <div className="rfm-initial-child-container" ref={marqueeRef}>
          {wrap()}
        </div>
        {multiplyChildren(multiplier - 1)}
      </div>
      <div className="rfm-marquee" style={marqueeStyle}>
        {multiplyChildren(multiplier)}
      </div>
    </div>
  )
}
