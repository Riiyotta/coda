// Port of Coda's section/payment-method-table-inner block (payment-method-table-inner-D0jBvXqv.js),
// its TabBar (TabBar-CVpb7Ctq.js), Input (Input-Ds1xwQCn.js) and the content/market-guide-table
// block (market-guide-table-BDqtbCrD.js). Live fetches the country rows from
// /_data/query/UseInfinitePaymentguidesCountries (5 pages of 10); the snapshot lives in
// paymentGuideCountries.json with logo/flag URLs pointing at public/images/2026-07/.
import { createRef, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import countries from './paymentGuideCountries.json'

const cx = (...a) => a.filter(Boolean).join(' ')

// TabBar: sliding pill (transition-all duration-200 = 200ms cubic-bezier(.4,0,.2,1)).
// Hover moves the pill to the hovered button; mouse-out snaps back to the active tab after 200ms.
function TabBar({ tabs, activeTab, setActiveTab, className }) {
  const refs = useMemo(() => tabs.map(() => createRef()), [tabs])
  const [width, setWidth] = useState(0)
  const [left, setLeft] = useState(0)
  const [hovered, setHovered] = useState(-1)
  const hoveredRef = useRef(-1)
  const lastSync = useRef(0)
  const outTimer = useRef()
  const prevActive = useRef(-1)
  hoveredRef.current = hovered

  const sync = (i = activeTab) => {
    const el = refs[i]?.current
    if (el) {
      setWidth(el.offsetWidth)
      setLeft(el.offsetLeft)
    }
  }

  const [vw, setVw] = useState(() => window.innerWidth)
  useEffect(() => {
    let raf = 0
    const onResize = () => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(() => setVw(window.innerWidth))
    }
    window.addEventListener('resize', onResize)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', onResize)
    }
  }, [])

  useEffect(() => sync(), [activeTab, vw]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (prevActive.current !== -1 && window.innerWidth < 700) {
      refs[activeTab]?.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    prevActive.current = activeTab
  }, [activeTab]) // eslint-disable-line react-hooks/exhaustive-deps

  // live runs a rAF loop (useRafLoop, always calling the latest render's callback) that re-measures
  // the active tab at most every 500ms; below 700px it does so even while another tab is hovered
  const activeRef = useRef(activeTab)
  activeRef.current = activeTab
  const syncRef = useRef(sync)
  syncRef.current = sync
  useEffect(() => {
    let raf
    const loop = () => {
      if (lastSync.current + 500 < Date.now() && (hoveredRef.current === -1 || window.innerWidth < 700)) {
        syncRef.current(activeRef.current)
        lastSync.current = Date.now()
      }
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => () => clearTimeout(outTimer.current), [])

  const over = (i) => {
    clearTimeout(outTimer.current)
    sync(i)
    setHovered(i)
  }
  const out = () => {
    clearTimeout(outTimer.current)
    outTimer.current = setTimeout(() => {
      setHovered(-1)
      syncRef.current(activeRef.current)
    }, 200)
  }

  return (
    <div className={cx('md:h-7 p-[3px] border border-current rounded-md md:w-fit', 'h-buttonLg overflow-auto snap-x snap-mandatory scroll-smooth hide-scrollbars', className)}>
      <div className="flex h-full items-center md:gap-1 relative flex-nowrap gap-5 justify-start">
        <div
          className={cx('absolute left-0 top-0 h-full bg-current rounded-md transition-all duration-200', hovered >= 0 || activeTab >= 0 ? 'opacity-100' : 'opacity-0')}
          style={{ width: `${width}px`, transform: `translateX(${left}px)` }}
        ></div>
        {tabs.map((t, i) => (
          <button
            key={t.label}
            ref={refs[i]}
            onClick={() => setActiveTab(i)}
            onMouseOver={() => over(i)}
            onMouseOut={out}
            // live merges classes with tailwind-merge, so text-offWhite replaces text-current
            className={
              (activeTab === i && hovered === -1) || hovered === i
                ? 'shrink-0 snap-center relative px-4 md:px-3 rounded-mdu md:rounded-md transition-colors duration-200 flex items-center justify-center type-ui-label leading-none text-offWhite h-full'
                : 'shrink-0 snap-center relative px-4 md:px-3 rounded-mdu md:rounded-md transition-colors duration-200 flex items-center justify-center text-current type-ui-label leading-none h-full'
            }
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  )
}

// className always carries hidden|flex; live's tailwind-merge drops the base `flex`, so it is omitted here
function Input({ name, value, onChange, className, placeholder }) {
  return (
    <div className={cx('flex-col gap-1 text-grey-2', className)}>
      <div className="relative">
        <input
          type="text"
          name={name}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="!text-[16px] md:!type-ui-label !w-full !border !border-current !bg-transparent !rounded-md !type-ui-label !h-buttonLg md:!h-7 !pl-4 !pr-2"
          placeholder={placeholder}
        />
      </div>
    </div>
  )
}

// Coda's image component (Nw in client bundle): sizes tracks rendered width rounded up to 40px.
function Flag({ src }) {
  const ref = useRef(null)
  useLayoutEffect(() => {
    const img = ref.current
    if (!img) return
    img.setAttribute('sizes', '200px')
    const ro = new ResizeObserver((e) => img.setAttribute('sizes', Math.ceil(e[0].contentRect.width / 40) * 40 + 'px'))
    ro.observe(img)
    return () => ro.disconnect()
  }, [src])
  if (!src) return null
  return (
    <div className="aspect-[--aspectRatio] w-6 h-6 inline-block">
      <img ref={ref} src={src} alt="" draggable={false} loading="lazy" className="!w-full !h-full object-cover" sizes="20vw" />
    </div>
  )
}

function MarketGuideTable() {
  return (
    <span style={{ display: 'contents' }}>
      <div className="wp-block-table">
        <figure className="wp-block-table">
          <table className="has-fixed-layout">
            <thead>
              <tr>
                <th>{'Country'}</th>
                <th className="has-text-align-right" data-align="right">{'Payment Methods'}</th>
              </tr>
            </thead>
            <tbody>
              {countries.map((n) => (
                <tr key={n.id}>
                  <td>
                    <Flag src={n.flag} />
                    {/* market guides are outside this clone */}
                    <a href="#" className="inline-block ml-2">{n.name}</a>
                  </td>
                  <td className="has-text-align-right" data-align="right">
                    <div dangerouslySetInnerHTML={{ __html: n.logos }} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </figure>
      </div>
    </span>
  )
}

export default function PaymentMethodTableInner({ typeTable }) {
  const ref = useRef(null)
  const [view, setView] = useState(1) // 1 = Type, 2 = Country
  const [tabs, setTabs] = useState([
    { label: 'Type', href: '#' },
    { label: 'Country', href: '#' },
  ])
  const [query, setQuery] = useState('')

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const a = el.children[0]?.querySelector('thead th')?.textContent || 'Type'
    const b = el.children[1]?.querySelector('thead th')?.textContent || 'Country'
    setTabs([
      { label: a, href: '#' },
      { label: b, href: '#' },
    ])
  }, [])

  useEffect(() => setQuery(''), [view])

  // same DOM filter as live: match the country cell's text, case-insensitive
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const rows = el.children[1]?.querySelectorAll('tbody tr') || []
    rows.forEach((tr) => {
      tr.style.display = view === 2 && !tr.children[0].textContent?.toLowerCase().includes(query.toLowerCase() || '') ? 'none' : ''
    })
  }, [query, view])

  return (
    <div className="payment-method-table-inner w-full">
      <TabBar tabs={tabs} activeTab={view - 1} setActiveTab={(i) => setView(i === 0 ? 1 : 2)} className="w-fit" />
      <Input placeholder="Country" name="country" value={query} onChange={setQuery} className={cx('mt-2 md:w-3/4', view === 1 ? 'hidden' : 'flex')} />
      <div
        ref={ref}
        className={cx(
          'w-full [&_.wp-block-table_img]:h-paymentTypeH [&_.wp-block-table_img]:!w-fit [&_.wp-block-table_tr_td:last-child_img]:mr-2 [&_.wp-block-table_tr_td:last-child_img]:md:ml-2 [&_.wp-block-table_tr_td:last-child_img]:md:mr-0 [&_.wp-block-table_img]:my-1 [&_.wp-block-table_tr_td:first-child]:type-header-s [&_.wp-block-table_thead_th]:type-special-pill-title-l-mobile [&_.wp-block-table_td_br]:hidden [&_.wp-block-table_td_br]:md:table-cell [&_table]:flex [&_table]:flex-col [&_tr]:flex [&_tr]:flex-col [&_tr_td:first-child]:border-none [&_tr_td:first-child]:!pb-0 [&_tr_td:last-child]:!text-left [&_table_thead]:border-none [&_table]:md:table [&_tr]:md:table-row [&_tr_td:first-child]:md:border-solid [&_tr_td:first-child]:md:!pb-2 [&_tr_td:last-child]:md:!text-right',
          'md:-mt-[4em] [&_.wp-block-table_thead_th:first-child]:invisible',
          view === 1 && '[&>span:first-child]:!contents [&>span:last-child]:!hidden',
          view === 2 && '[&>span:first-child]:!hidden [&>span:last-child]:!contents',
        )}
      >
        {typeTable}
        <MarketGuideTable />
      </div>
    </div>
  )
}
