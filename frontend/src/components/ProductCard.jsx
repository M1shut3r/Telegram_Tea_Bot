import { useState } from 'react'
import { formatPrice } from '../utils/format'
import QuantityControl from './QuantityControl'

export default function ProductCard({ product, quantity, busy, onOpen, onIncrement, onDecrement }) {
  const [broken, setBroken] = useState(false)

  return (
    <article className="maison-card overflow-hidden">
      <button type="button" onClick={() => onOpen(product)} className="block w-full text-left">
        <div className="relative aspect-[3/4] overflow-hidden bg-paper-deep">
          {broken ? (
            <div className="flex h-full items-center justify-center bg-paper-deep">
              <span className="font-neon text-4xl text-neon">Ж</span>
            </div>
          ) : (
            <img
              src={product.photo_url}
              alt={product.name}
              className="h-full w-full object-cover transition duration-500 hover:scale-[1.03]"
              onError={() => setBroken(true)}
            />
          )}
          <div className="pointer-events-none absolute inset-0 ring-1 ring-inset ring-white/5" />
        </div>
        <div className="space-y-1.5 px-3.5 pb-3.5 pt-3.5 text-center">
          <h3 className="font-serif text-[1.15rem] leading-snug tracking-tight">{product.name}</h3>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-gold">{formatPrice(product.price)}</p>
        </div>
      </button>
      <div className="px-3 pb-3">
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
