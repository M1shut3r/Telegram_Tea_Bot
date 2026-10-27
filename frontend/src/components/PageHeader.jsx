import emblemUrl from '../assets/logo-emblem.svg'
import { BerryDivider } from './Ornaments'

// variant="emblem" — большая эмблема на витрине;
// variant="compact" — маленькая эмблема (или без неё) и заголовок вкладки.
export default function PageHeader({ variant = 'compact', kicker, title, emblem = true, children }) {
  if (variant === 'emblem') {
    return (
      <header className="flex flex-col items-center gap-3 pt-2">
        <img src={emblemUrl} alt="Жили Пили" width="358" height="336" className="block h-auto w-full max-w-[358px]" />
        <p className="lk-kicker">Чайная лавка · доставка по России</p>
        <BerryDivider width={240} />
      </header>
    )
  }

  return (
    <header className="flex flex-col items-center gap-1 pb-2 text-center">
      {emblem ? <img src={emblemUrl} alt="Жили Пили" width="96" height="90" className="mb-1.5 block h-[90px] w-[96px]" /> : null}
      {kicker ? <p className="lk-kicker">{kicker}</p> : null}
      <h1 className="lk-title">{title}</h1>
      {children ? <div className="text-sm text-cream-soft">{children}</div> : null}
      <BerryDivider className="mt-1" />
    </header>
  )
}
