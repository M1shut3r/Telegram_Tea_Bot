import { useState } from 'react'
import { formatPrice } from '../utils/format'
import QuantityControl from './QuantityControl'

export default function ProductCard({ product, quantity, busy, onOpen, onIncrement, onDecrement }) {
  const [broken, setBroken] = useState(false)

  return (
    <article className="overflow-hidden rounded-[28px] bg-tg-secondary shadow-card">
      <button type="button" onClick={() => onOpen(product)} className="block w-full text-left">
        <div className="relative aspect-[4/5] overflow-hidden bg-black/5">
          {broken ? (
            <div className="flex h-full items-center justify-center bg-gradient-to-br from-[#d8c4a8] to-[#8f6b4a]">
              <span className="font-serif text-4xl text-white/80">茶</span>
            </div>
          ) : (
            <img
              src={product.photo_url}
              alt={product.name}
              className="h-full w-full object-cover"
              onError={() => setBroken(true)}
            />
          )}
        </div>
        <div className="space-y-1.5 px-3.5 pb-4 pt-3">
          <h3 className="font-serif text-[17px] leading-snug tracking-tight">{product.name}</h3>
          <p className="text-sm font-semibold text-tg-hint">{formatPrice(product.price)}</p>
        </div>
      </button>
      <div className="px-3.5 pb-3.5">
        <QuantityControl
          quantity={quantity}
          busy={busy}
          onIncrement={() => onIncrement(product)}
          onDecrement={() => onDecrement(product)}
        />
      </div>
    </article>
  )
}
