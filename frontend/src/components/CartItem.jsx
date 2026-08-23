import { useState } from 'react'
import { formatPrice } from '../utils/format'

export default function CartItem({ item, onChange }) {
  const [broken, setBroken] = useState(false)

  return (
    <article className="maison-card flex gap-4 p-3">
      <div className="relative h-24 w-[4.75rem] shrink-0 overflow-hidden bg-paper-deep">
        {broken ? (
          <div className="flex h-full items-center justify-center bg-paper-deep">
            <span className="font-neon text-xl text-neon">Ж</span>
          </div>
        ) : (
          <img
            src={item.photo_url}
            alt={item.name}
            className="h-full w-full object-cover"
            onError={() => setBroken(true)}
          />
        )}
      </div>
      <div className="flex min-w-0 flex-1 flex-col justify-between py-0.5">
        <div>
          <h3 className="truncate font-serif text-xl leading-tight">{item.name}</h3>
          <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-gold">{formatPrice(item.price)}</p>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 border border-white/10 px-1 py-1">
            <button
              type="button"
              onClick={() => onChange(item.product_id, item.quantity - 1)}
              className="flex h-8 w-8 items-center justify-center text-lg leading-none"
            >
              −
            </button>
            <span className="min-w-[1.25rem] text-center text-sm font-medium">{item.quantity}</span>
            <button
              type="button"
              onClick={() => onChange(item.product_id, item.quantity + 1)}
              className="flex h-8 w-8 items-center justify-center text-lg leading-none"
            >
              +
            </button>
          </div>
          <p className="font-serif text-lg">{formatPrice(item.line_total)}</p>
        </div>
      </div>
    </article>
  )
}
