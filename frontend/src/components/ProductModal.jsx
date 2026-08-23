import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { formatPrice } from '../utils/format'
import QuantityControl from './QuantityControl'

export default function ProductModal({ product, quantity, busy, onClose, onIncrement, onDecrement }) {
  const [broken, setBroken] = useState(false)

  useEffect(() => {
    setBroken(false)
  }, [product?.id])

  useEffect(() => {
    if (product == null) {
      return undefined
    }
    const scroller = document.querySelector('.tg-scroll')
    const previousOverflow = scroller ? scroller.style.overflow : ''
    document.body.classList.add('sheet-open')
    if (scroller) {
      scroller.style.overflow = 'hidden'
    }
    return () => {
      document.body.classList.remove('sheet-open')
      if (scroller) {
        scroller.style.overflow = previousOverflow
      }
    }
  }, [product])

  if (product == null) {
    return null
  }

  return createPortal(
    <div className="product-sheet" role="dialog" aria-modal="true" aria-labelledby="product-sheet-title">
      <button type="button" className="product-sheet-close" onClick={onClose} aria-label="Закрыть">
        ×
      </button>
      <div className="product-sheet-scroll">
        <div className="product-sheet-inner">
          <div className="product-sheet-photo">
            {broken ? (
              <div className="flex h-full min-h-[220px] items-center justify-center bg-paper-deep">
                <span className="font-neon text-6xl text-neon">Ж</span>
              </div>
            ) : (
              <img
                src={product.photo_url}
                alt={product.name}
                className="product-sheet-image"
                onError={() => setBroken(true)}
              />
            )}
          </div>
          <div className="space-y-3 px-5 pb-4 pt-5 text-center">
            <p className="maison-kicker">Коллекция</p>
            <h2 id="product-sheet-title" className="font-serif text-[2rem] leading-tight">
              {product.name}
            </h2>
            <p className="text-[12px] font-medium uppercase tracking-[0.2em] text-gold">{formatPrice(product.price)}</p>
            <p className="pt-1 text-[15px] font-light leading-relaxed text-tg-hint">{product.description}</p>
            {product.composition ? (
              <div className="maison-card px-4 py-4 text-left">
                <p className="maison-kicker mb-2">Состав</p>
                <p className="text-sm font-light leading-relaxed">{product.composition}</p>
              </div>
            ) : null}
          </div>
          <div className="product-sheet-actions">
            <button type="button" onClick={onClose} className="maison-btn-ghost">
              Закрыть
            </button>
            <QuantityControl
              quantity={quantity}
              busy={busy}
              tall
              onIncrement={() => onIncrement(product)}
              onDecrement={() => onDecrement(product)}
            />
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}
