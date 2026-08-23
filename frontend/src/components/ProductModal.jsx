import { useEffect, useState } from 'react'
import { formatPrice } from '../utils/format'
import QuantityControl from './QuantityControl'

export default function ProductModal({ product, quantity, busy, onClose, onIncrement, onDecrement }) {
  const [broken, setBroken] = useState(false)

  useEffect(() => {
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previous
    }
  }, [])

  if (product == null) {
    return null
  }

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center sm:items-center">
      <button type="button" className="absolute inset-0 bg-black/40" onClick={onClose} aria-label="Закрыть" />
      <div className="relative max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-[32px] bg-tg-bg px-5 pb-8 pt-4 shadow-card sm:rounded-[32px]">
        <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-black/10" />
        <div className="overflow-hidden rounded-[28px] bg-tg-secondary">
          <div className="aspect-[4/5] bg-black/5">
            {broken ? (
              <div className="flex h-full items-center justify-center bg-gradient-to-br from-[#d8c4a8] to-[#8f6b4a]">
                <span className="font-serif text-6xl text-white/80">茶</span>
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
        </div>
        <div className="mt-5 space-y-3">
          <div className="flex items-start justify-between gap-4">
            <h2 className="font-serif text-[28px] leading-tight">{product.name}</h2>
            <p className="shrink-0 pt-1 text-base font-semibold">{formatPrice(product.price)}</p>
          </div>
          <p className="text-[15px] leading-relaxed text-tg-hint">{product.description}</p>
          {product.composition ? (
            <div className="rounded-3xl bg-tg-secondary px-4 py-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-tg-hint">Состав</p>
              <p className="text-sm leading-relaxed">{product.composition}</p>
            </div>
          ) : null}
        </div>
        <div className="mt-6 grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={onClose}
            className="h-12 rounded-2xl bg-tg-secondary text-sm font-semibold"
          >
            Закрыть
          </button>
          <QuantityControl
            quantity={quantity}
            busy={busy}
            onIncrement={() => onIncrement(product)}
            onDecrement={() => onDecrement(product)}
          />
        </div>
      </div>
    </div>
  )
}
