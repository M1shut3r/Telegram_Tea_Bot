import { useState } from 'react'
import emblemUrl from '../assets/logo-emblem.svg'
import { formatPrice } from '../utils/format'
import { MinusIcon, PlusIcon, TrashIcon } from './Icons'

export default function CartItem({ item, onChange, busy = false }) {
  const [broken, setBroken] = useState(false)

  return (
    <article className="lk-card flex gap-3.5 p-2.5">
      <div className="h-[6.5rem] w-[4.875rem] flex-none overflow-hidden rounded-[0.625rem] border-2 border-gold bg-lacquer-deep">
        {broken ? (
          <div className="flex h-full items-center justify-center">
            <img src={emblemUrl} alt="" className="w-3/4 opacity-80" />
          </div>
        ) : (
          <img
            src={item.photo_url}
            alt={`Упаковка чая «${item.name}»`}
            className="h-full w-full object-cover"
            onError={() => setBroken(true)}
          />
        )}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <div className="flex items-baseline justify-between gap-2">
          <h2 className="truncate font-display text-xl leading-tight">{item.name}</h2>
          <span className="flex-none text-base font-extrabold text-gold">{formatPrice(item.line_total)}</span>
        </div>
        <span className="text-sm text-cream-soft">{formatPrice(item.price)} за пачку</span>
        <div className="mt-auto flex items-center justify-between pt-1.5">
          <div className="lk-stepper min-h-[2.75rem] w-[8.5rem]">
            <button
              type="button"
              disabled={busy}
              onClick={() => onChange(item.product_id, item.quantity - 1)}
              aria-label={`Убрать одну пачку «${item.name}»`}
            >
              <MinusIcon />
            </button>
            <span className="text-[0.95rem] font-extrabold" aria-live="polite">
              {item.quantity} шт.
            </span>
            <button
              type="button"
              disabled={busy}
              onClick={() => onChange(item.product_id, item.quantity + 1)}
              aria-label={`Добавить пачку «${item.name}»`}
            >
              <PlusIcon />
            </button>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => onChange(item.product_id, 0)}
            aria-label={`Удалить «${item.name}» из корзины`}
            className="flex h-11 w-11 items-center justify-center text-cream-soft disabled:opacity-55"
          >
            <TrashIcon />
          </button>
        </div>
      </div>
    </article>
  )
}
