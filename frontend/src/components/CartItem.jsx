import { useState } from 'react'
import { formatPrice } from '../utils/format'

export default function CartItem({ item, onChange }) {
  const [broken, setBroken] = useState(false)

  return (
    <article className="flex gap-4 rounded-[28px] bg-tg-secondary p-3">
      <div className="h-24 w-20 shrink-0 overflow-hidden rounded-2xl bg-black/5">
        {broken ? (
          <div className="flex h-full items-center justify-center bg-gradient-to-br from-[#d8c4a8] to-[#8f6b4a]">
            <span className="font-serif text-2xl text-white/80">茶</span>
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
          <h3 className="truncate font-serif text-lg leading-tight">{item.name}</h3>
          <p className="mt-1 text-sm text-tg-hint">{formatPrice(item.price)}</p>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 rounded-full bg-tg-bg px-1.5 py-1">
            <button
              type="button"
              onClick={() => onChange(item.product_id, item.quantity - 1)}
              className="flex h-8 w-8 items-center justify-center rounded-full text-lg leading-none"
            >
              −
            </button>
            <span className="min-w-[1.25rem] text-center text-sm font-semibold">{item.quantity}</span>
            <button
              type="button"
              onClick={() => onChange(item.product_id, item.quantity + 1)}
              className="flex h-8 w-8 items-center justify-center rounded-full text-lg leading-none"
            >
              +
            </button>
          </div>
          <p className="text-sm font-semibold">{formatPrice(item.line_total)}</p>
        </div>
      </div>
    </article>
  )
}
