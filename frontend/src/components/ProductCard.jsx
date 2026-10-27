import { useState } from 'react'
import emblemUrl from '../assets/logo-emblem.svg'
import { formatPrice } from '../utils/format'
import QuantityControl from './QuantityControl'

export default function ProductCard({ product, quantity, busy, onOpen, onIncrement, onDecrement }) {
  const [broken, setBroken] = useState(false)

  return (
    <article className="lk-card flex flex-col gap-2 rounded-[1.125rem] p-2.5 pb-3 text-center">
      <button type="button" onClick={() => onOpen(product)} className="flex flex-col gap-2 text-center">
        <span className="lk-photo m-1 block aspect-[3/4]">
          {broken ? (
            <span className="flex h-full items-center justify-center">
              <img src={emblemUrl} alt="" className="w-3/4 opacity-80" />
            </span>
          ) : (
            <img
              src={product.photo_url}
              alt=""
              loading="lazy"
              className="h-full w-full object-cover"
              onError={() => setBroken(true)}
            />
          )}
        </span>
        <span className="font-display text-[1.19rem] leading-tight text-cream">{product.name}</span>
      </button>
      <span className="text-base font-extrabold text-gold">{formatPrice(product.price)}</span>
      <div className="mt-auto">
        <QuantityControl
          quantity={quantity}
          busy={busy}
          name={product.name}
          onIncrement={() => onIncrement(product)}
          onDecrement={() => onDecrement(product)}
        />
      </div>
    </article>
  )
}
