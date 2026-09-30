// Port of Coda's ArrowButton (ArrowButton-BzPXnroR.js). Disabled: text-grey-2/50, no `group`
// (so no hover line/arrow shift), no onClick.
export default function ArrowButton({ onClick, disabled, reverse, className, fill = 'transparent' }) {
  const cls = ['w-8 h-8 md:w-7 md:h-7 cursor-pointer text-charcoal transition-colors duration-300', disabled && 'text-grey-2/50', !disabled && 'group', reverse && 'rotate-180', className]
    .filter(Boolean)
    .join(' ')
  return (
    <svg className={cls} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" onClick={disabled ? undefined : onClick}>
      <rect x="0.5" y="0.5" width="39" height="39" rx="11.5" fill={fill} stroke="currentColor"></rect>
      <path fillRule="evenodd" clipRule="evenodd" d="M21.2197 15.2197C21.5126 14.9268 21.9874 14.9268 22.2803 15.2197L26.5303 19.4697C26.8232 19.7626 26.8232 20.2374 26.5303 20.5303L22.2803 24.7803C21.9874 25.0732 21.5126 25.0732 21.2197 24.7803C20.9268 24.4874 20.9268 24.0126 21.2197 23.7197L24.9393 20L21.2197 16.2803C20.9268 15.9874 20.9268 15.5126 21.2197 15.2197Z" fill="currentColor" className="transition-transform duration-300 -translate-x-[0.15em] md:group-hover:translate-x-0"></path>
      <line x1="15.75" y1="20.0498" x2="24.25" y2="20.0498" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="transition-all opacity-0 duration-300 md:group-hover:opacity-100"></line>
    </svg>
  )
}
